"""
Avatar Controller and Runtime Coordinator for Delta VTuber.
Integrates EmotionChangedEvents, SpeechLifecycleEvents, ExpressionController,
LipSyncController, and AvatarFrameComposer to maintain an authoritative AvatarState
and dispatch frames to AvatarRenderers.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set

from delta.vtuber.avatar.composer import AvatarFrameComposer, FinalAvatarFrame, avatar_frame_composer
from delta.vtuber.avatar.expressions import ExpressionController
from delta.vtuber.avatar.lip_sync import DefaultLipSyncController, LipSyncController
from delta.vtuber.avatar.renderer import AvatarRenderer, MockAvatarRenderer
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.emotion.schemas import EmotionChangedEvent, VTuberExpression
from delta.vtuber.event_bus import VTuberEventBus, vtuber_event_bus
from delta.vtuber.voice.schemas import SpeechLifecycleEvent, SpeechLifecycleEventType

logger = logging.getLogger(__name__)


class AvatarController:
    """
    Central controller orchestrating avatar visual state, expression transitions,
    lip-sync mouth movements, and dispatching composed state frames to connected renderers.
    """

    def __init__(
        self,
        renderer: Optional[AvatarRenderer] = None,
        expression_controller: Optional[ExpressionController] = None,
        lip_sync_controller: Optional[LipSyncController] = None,
        composer: Optional[AvatarFrameComposer] = None,
        event_bus: Optional[VTuberEventBus] = None,
        auto_subscribe: bool = True,
    ):
        self.renderer = renderer or MockAvatarRenderer()
        self.expressions = expression_controller or ExpressionController()
        self.lip_sync = lip_sync_controller or DefaultLipSyncController()
        self.composer = composer or avatar_frame_composer
        self.event_bus = event_bus or vtuber_event_bus

        self._current_state = AvatarState()
        self._last_rendered_state: Optional[AvatarState] = None
        self._listeners: Set[Callable[[AvatarState], Any]] = set()
        self._lock = asyncio.Lock()
        self._is_initialized = False

        if auto_subscribe and self.event_bus:
            self.attach_event_bus(self.event_bus)

    @property
    def current_state(self) -> AvatarState:
        return self._current_state

    def add_listener(self, listener: Callable[[AvatarState], Any]) -> Callable[[], None]:
        """Subscribe to avatar state updates."""
        self._listeners.add(listener)

        def _unsub():
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _unsub

    def attach_event_bus(self, bus: VTuberEventBus) -> None:
        """Attach to VTuberEventBus for emotion & speech lifecycle events."""
        pass  # Handled directly or through handle_emotion_event / handle_speech_lifecycle

    async def initialize(self) -> None:
        """Initialize controller and underlying renderer."""
        if hasattr(self.renderer, "initialize"):
            await self.renderer.initialize()
        self._is_initialized = True
        await self.render_current_state(force=True)

    async def shutdown(self) -> None:
        """Shutdown controller and underlying renderer."""
        self._is_initialized = False
        if hasattr(self.renderer, "shutdown"):
            await self.renderer.shutdown()
        self._listeners.clear()

    async def handle_emotion_event(self, event: EmotionChangedEvent) -> None:
        """Process incoming emotion changes and update avatar expression."""
        expr, intensity = self.expressions.handle_emotion_event(event)
        async with self._lock:
            self._current_state.expression = expr
            self._current_state.expression_intensity = intensity
        await self.render_current_state()

    async def handle_speech_lifecycle(self, event: SpeechLifecycleEvent) -> None:
        """Process incoming speech lifecycle events and update speaking state."""
        ev_type = event.event_type
        async with self._lock:
            if ev_type in (SpeechLifecycleEventType.SPEECH_STARTED, SpeechLifecycleEventType.SPEECH_PLAYING):
                self._current_state.speaking = True
            elif ev_type in (
                SpeechLifecycleEventType.SPEECH_FINISHED,
                SpeechLifecycleEventType.SPEECH_INTERRUPTED,
                SpeechLifecycleEventType.SPEECH_ERROR,
            ):
                self._current_state.speaking = False
                await self.lip_sync.reset()
                self._current_state.mouth_open = 0.0

        await self.render_current_state(force=(ev_type == SpeechLifecycleEventType.SPEECH_INTERRUPTED))

    async def set_expression(
        self,
        expression: VTuberExpression,
        intensity: float = 0.5,
    ) -> None:
        """Directly set expression and intensity."""
        self.expressions.set_expression(expression, intensity)
        async with self._lock:
            self._current_state.expression = expression
            self._current_state.expression_intensity = max(0.0, min(1.0, float(intensity)))
        await self.render_current_state()

    async def set_mouth_open(self, value: float) -> None:
        """Directly update mouth opening level for lip-sync."""
        await self.lip_sync.update_amplitude(value)
        async with self._lock:
            self._current_state.mouth_open = self.lip_sync.current_mouth_open
        await self.render_current_state()

    async def set_speaking(self, speaking: bool) -> None:
        """Set speaking status flag."""
        async with self._lock:
            self._current_state.speaking = speaking
            if not speaking:
                await self.lip_sync.reset()
                self._current_state.mouth_open = 0.0
        await self.render_current_state(force=(not speaking))

    async def set_idle(self) -> None:
        """Reset avatar state to default idle rest posture."""
        self.expressions.reset()
        await self.lip_sync.reset()
        async with self._lock:
            self._current_state = AvatarState(
                expression=VTuberExpression.NEUTRAL,
                expression_intensity=0.3,
                mouth_open=0.0,
                mouth_form=0.0,
                head_x=0.0,
                head_y=0.0,
                body_angle=0.0,
                speaking=False,
            )
        await self.render_current_state(force=True)

    async def render_current_state(self, force: bool = False) -> None:
        """
        Compose layers via AvatarFrameComposer and render frame to AvatarRenderer.
        """
        # 1. Compose full frame with live mood modulation from PersonalityManager
        mood_modifier = {}
        curiosity_mod = 0.5
        energy_mod = 0.5
        try:
            from delta.vtuber.personality.manager import personality_manager
            mood = personality_manager.mood
            mood_modifier = {
                "happiness": mood.happiness,
                "stress": mood.stress,
            }
            curiosity_mod = mood.confidence
            energy_mod = mood.energy
        except Exception:
            pass

        composed_frame: FinalAvatarFrame = self.composer.compose_frame(
            self._current_state,
            mood_modifier=mood_modifier,
            curiosity_mod=curiosity_mod,
            energy_mod=energy_mod,
        )
        frame_state = composed_frame.to_avatar_state()

        if not force and self._last_rendered_state is not None:
            if not frame_state.is_significantly_different_from(self._last_rendered_state):
                # Suppress redundant render spam
                return

        self._last_rendered_state = frame_state

        # 2. Dispatch to AvatarRenderer (urgent=force bypasses rate-limit & delta, e.g. barge-in)
        try:
            await self.renderer.render(frame_state, urgent=force)
        except Exception as exc:
            logger.error("AvatarRenderer error during render: %s", exc, exc_info=True)

        # 3. Dispatch to listeners
        for listener in list(self._listeners):
            try:
                res = listener(frame_state)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as exc:
                logger.error("AvatarController state listener error: %s", exc)


# Global singleton instance
avatar_controller = AvatarController()
