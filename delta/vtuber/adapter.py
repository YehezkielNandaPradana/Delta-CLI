"""
Bridge Adapter between Delta Core Agent and Async VTuber Event System.
Translates AgentEvent lifecycle into VTuberState transitions and VTuberEvent emissions.
"""

import asyncio
import logging
import threading
from typing import Any, Callable, Dict, Optional, Union

from delta.ai.events import AgentEvent, EventType, event_bus as core_event_bus
from delta.vtuber.events import (
    VTuberEmotion,
    VTuberEvent,
    VTuberEventType,
    VTuberPayload,
)
from delta.vtuber.emotion import EmotionEngine, emotion_engine
from delta.vtuber.personality import PersonalityManager, personality_manager
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.state_machine import (
    InvalidStateTransitionError,
    VTuberState,
    VTuberStateMachine,
)

logger = logging.getLogger(__name__)


class VTuberAgentAdapter:
    """
    Adapter that listens to Delta's internal AgentEvent stream and drives the
    asynchronous VTuberStateMachine, EmotionEngine, and VTuberEventBus.

    Thread-safe and async-safe: manages a dedicated background event loop
    to dispatch coroutines from synchronous or multi-threaded Delta contexts.
    """

    def __init__(
        self,
        state_machine: Optional[VTuberStateMachine] = None,
        event_bus: Optional[VTuberEventBus] = None,
        emotion_engine_instance: Optional[EmotionEngine] = None,
        auto_attach: bool = False,
    ):
        self.event_bus = event_bus or vtuber_event_bus
        self.state_machine = state_machine or VTuberStateMachine(
            initial_state=VTuberState.IDLE,
            event_bus=self.event_bus,
            auto_emit=True,
        )
        self.emotion_engine = emotion_engine_instance or emotion_engine
        self._unsubscribe_core: Optional[Callable[[], None]] = None
        self._lock = threading.RLock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None

        if auto_attach:
            self.attach()

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is None or not self._loop.is_running():
                self._loop = asyncio.new_event_loop()
                self._loop_thread = threading.Thread(
                    target=self._run_loop,
                    args=(self._loop,),
                    daemon=True,
                    name="VTuberAdapterEventLoop",
                )
                self._loop_thread.start()
            return self._loop

    def _run_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def dispatch_coroutine(self, coro: Any) -> Any:
        """
        Safely schedule an async coroutine from any synchronous thread.
        """
        loop = self._ensure_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop)

    def attach(self, target_bus: Optional[Any] = None) -> None:
        """
        Attach adapter to Delta Core EventBus to automatically receive AgentEvent stream.
        """
        bus = target_bus or core_event_bus
        with self._lock:
            if self._unsubscribe_core is None:
                self._unsubscribe_core = bus.subscribe(self.handle_agent_event)

    def detach(self) -> None:
        """
        Detach adapter from Delta Core EventBus.
        """
        with self._lock:
            if self._unsubscribe_core is not None:
                self._unsubscribe_core()
                self._unsubscribe_core = None

    def handle_agent_event(self, event: AgentEvent) -> None:
        """
        Synchronous entry point called by core EventBus.
        Schedules async processing in the background loop.
        """
        self.dispatch_coroutine(self.handle_agent_event_async(event))

    async def handle_agent_event_async(self, event: AgentEvent) -> None:
        """
        Map AgentEvent to VTuber State transitions, EmotionEngine resolution, and emit VTuberEvent.
        """
        ev_type = event.type if isinstance(event.type, EventType) else EventType(str(event.type))

        try:
            # 1. Update Emotion Engine first to resolve context-aware emotion & expression
            await self.emotion_engine.process_agent_event(event)

            # 2. Dispatch state transitions
            if ev_type == EventType.AGENT_START:
                await self._on_agent_start(event)
            elif ev_type == EventType.AGENT_THINKING:
                await self._on_agent_thinking(event)
            elif ev_type == EventType.TOOL_START:
                await self._on_tool_start(event)
            elif ev_type == EventType.TOOL_RESULT:
                await self._on_tool_result(event)
            elif ev_type == EventType.MESSAGE_COMPLETE:
                await self._on_message_complete(event)
            elif ev_type == EventType.AGENT_COMPLETE:
                await self._on_agent_complete(event)
            elif ev_type == EventType.ERROR:
                await self._on_error(event)
        except Exception as exc:
            logger.error("Error processing AgentEvent %s in VTuber adapter: %s", ev_type, exc, exc_info=True)

    async def _safe_transition(
        self,
        target_state: VTuberState,
        payload: Optional[VTuberPayload] = None,
        text: Optional[str] = None,
        emotion: Optional[VTuberEmotion] = None,
        intensity: float = 1.0,
        tool: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        curr = self.state_machine.current_state
        if curr == target_state:
            # Already in target state, just emit updated event if needed
            if self.event_bus and self.state_machine.auto_emit:
                event_type = self.state_machine._STATE_TO_EVENT.get(target_state, VTuberEventType.IDLE)
                event_payload = payload or VTuberPayload(
                    text=text,
                    emotion=emotion or VTuberEmotion.NEUTRAL,
                    intensity=intensity,
                    tool=tool,
                    metadata=metadata or {"state": target_state.value},
                )
                await self.event_bus.emit(VTuberEvent(type=event_type, payload=event_payload))
            return

        if not self.state_machine.can_transition_to(target_state):
            # If direct transition is not valid, step through an intermediate state if sensible
            if target_state == VTuberState.TOOL_USE and curr == VTuberState.IDLE:
                await self.state_machine.transition_to(VTuberState.THINKING)
            elif target_state == VTuberState.SPEAKING and curr == VTuberState.TOOL_USE:
                await self.state_machine.transition_to(VTuberState.THINKING)
            elif target_state == VTuberState.IDLE and curr == VTuberState.TOOL_USE:
                await self.state_machine.transition_to(VTuberState.THINKING)
            elif not self.state_machine.can_transition_to(target_state):
                logger.warning("Forcing state reset to IDLE before transitioning to %s from %s", target_state, curr)
                self.state_machine.reset()

        await self.state_machine.transition_to(
            target_state,
            payload=payload,
            text=text,
            emotion=emotion,
            intensity=intensity,
            tool=tool,
            metadata=metadata,
        )

    async def _on_agent_start(self, event: AgentEvent) -> None:
        await self._safe_transition(
            VTuberState.THINKING,
            text=event.status_text or "Thinking...",
            emotion=VTuberEmotion.THINKING,
            intensity=0.6,
            metadata={"execution_id": event.execution_id, "task_id": event.task_id},
        )

    async def _on_agent_thinking(self, event: AgentEvent) -> None:
        await self._safe_transition(
            VTuberState.THINKING,
            text=event.status_text or "Thinking...",
            emotion=VTuberEmotion.THINKING,
            intensity=0.6,
            metadata={"execution_id": event.execution_id, "task_id": event.task_id},
        )

    async def _on_tool_start(self, event: AgentEvent) -> None:
        tool_name = event.tool or "unknown_tool"
        status_text = event.status_text or f"Running {tool_name}..."
        await self._safe_transition(
            VTuberState.TOOL_USE,
            text=status_text,
            emotion=VTuberEmotion.THINKING,
            intensity=0.7,
            tool=tool_name,
            metadata={
                "execution_id": event.execution_id,
                "task_id": event.task_id,
                "tool": tool_name,
                "input_summary": str(event.input)[:120] if event.input else "",
            },
        )

    async def _on_tool_result(self, event: AgentEvent) -> None:
        tool_name = event.tool or "unknown_tool"
        is_success = event.success if event.success is not None else True

        if not is_success:
            await self._safe_transition(
                VTuberState.ERROR,
                text=f"Tool {tool_name} failed",
                emotion=VTuberEmotion.CONFUSED,
                intensity=0.8,
                tool=tool_name,
                metadata={
                    "execution_id": event.execution_id,
                    "task_id": event.task_id,
                    "tool": tool_name,
                    "success": False,
                },
            )
            # ReAct agent continues thinking after handling error
            await self._safe_transition(
                VTuberState.THINKING,
                text="Analyzing tool failure...",
                emotion=VTuberEmotion.THINKING,
                intensity=0.6,
            )
        else:
            await self._safe_transition(
                VTuberState.THINKING,
                text=event.status_text or f"Finished {tool_name}",
                emotion=VTuberEmotion.THINKING,
                intensity=0.6,
                tool=tool_name,
                metadata={
                    "execution_id": event.execution_id,
                    "task_id": event.task_id,
                    "tool": tool_name,
                    "duration_ms": event.duration_ms,
                    "success": True,
                },
            )

    async def _on_message_complete(self, event: AgentEvent) -> None:
        raw_text = event.content or ""
        # Separate display formatting vs natural spoken text through Personality layer
        from delta.vtuber.personality import personality_manager
        display_text, speech_text = personality_manager.format_agent_speech(raw_text)

        await self._safe_transition(
            VTuberState.SPEAKING,
            text=speech_text if speech_text else display_text,
            emotion=VTuberEmotion.NEUTRAL,
            intensity=0.8,
            metadata={
                "execution_id": event.execution_id,
                "task_id": event.task_id,
                "session_id": event.session_id,
                "display_text": display_text,
            },
        )

    async def _on_agent_complete(self, event: AgentEvent) -> None:
        await self._safe_transition(
            VTuberState.IDLE,
            text=event.status_text or "Task completed",
            emotion=VTuberEmotion.NEUTRAL,
            intensity=0.5,
            metadata={
                "execution_id": event.execution_id,
                "task_id": event.task_id,
            },
        )

    async def _on_error(self, event: AgentEvent) -> None:
        err_msg = ""
        if isinstance(event.error, dict):
            err_msg = str(event.error.get("message", event.error))
        elif event.error:
            err_msg = str(event.error)
        else:
            err_msg = event.status_text or "An error occurred"

        await self._safe_transition(
            VTuberState.ERROR,
            text=err_msg,
            emotion=VTuberEmotion.CONFUSED,
            intensity=0.9,
            metadata={
                "execution_id": event.execution_id,
                "task_id": event.task_id,
                "error": event.error,
            },
        )
