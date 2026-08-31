"""
Idle Behavior Manager for Delta VTuber.
Coordinates non-intrusive background procedural motions (breathing, micro-sway, mood-aware idle expressions)
without blocking the agent or generating unprompted speech chatter.
"""

import asyncio
import math
import random
import time
from typing import Any, Callable, Dict, Optional, Set
from delta.vtuber.avatar.controller import AvatarController, avatar_controller
from delta.vtuber.avatar.priority import AnimationPriority
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.emotion.schemas import VTuberEmotion, VTuberExpression
from delta.vtuber.personality.manager import PersonalityManager, personality_manager


class IdleBehaviorManager:
    """
    Background asynchronous scheduler computing subtle micro-movements,
    breathing cycles, and mood-aligned rest postures.
    """

    def __init__(
        self,
        avatar_ctrl: Optional[AvatarController] = None,
        personality_mgr: Optional[PersonalityManager] = None,
        breathing_interval_sec: float = 0.5,
        enabled: bool = True,
    ):
        self.avatar = avatar_ctrl or avatar_controller
        self.personality = personality_mgr or personality_manager
        self.breathing_interval_sec = breathing_interval_sec
        self.enabled = enabled

        self._task: Optional[asyncio.Task] = None
        self._is_running = False
        self._step_counter = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start(self) -> None:
        """Start non-blocking background idle scheduler loop."""
        if not self.enabled:
            return

        if self._task is None or self._task.done():
            self._is_running = True
            self._task = asyncio.create_task(self._idle_loop())

    async def stop(self) -> None:
        """Stop background idle scheduler cleanly."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def compute_idle_frame(self, time_step: float) -> AvatarState:
        """
        Pure function computing subtle idle head tilt and mood-aligned posture.
        """
        # 1. Subtle breathing float (period ~ 3.5s)
        sway_y = round(math.sin(time_step * 1.8) * 0.04, 3)
        # 2. Micro head sway (period ~ 5.0s)
        sway_x = round(math.cos(time_step * 1.2) * 0.05, 3)
        # 3. Body angle micro-compensation
        body_ang = round(-sway_x * 0.4, 3)

        # 4. Determine mood-influenced idle baseline expression
        mood = self.personality.mood
        idle_expr = VTuberExpression.NEUTRAL
        intensity = 0.3

        if mood.happiness > 0.75:
            idle_expr = VTuberExpression.SMILE
            intensity = 0.4
        elif mood.curiosity > 0.8:
            idle_expr = VTuberExpression.THINKING
            intensity = 0.35
        elif mood.stress > 0.65:
            idle_expr = VTuberExpression.CONFUSED
            intensity = 0.3

        return AvatarState(
            expression=idle_expr,
            expression_intensity=intensity,
            mouth_open=0.0,
            mouth_form=0.0,
            head_x=sway_x,
            head_y=sway_y,
            body_angle=body_ang,
            speaking=False,
        )

    async def _idle_loop(self) -> None:
        """Asynchronous tick loop generating periodic subtle idle updates."""
        try:
            while self._is_running:
                self._step_counter += 1
                t = time.time()

                # Only update idle posture if avatar is currently not speaking or processing high priority task
                if not self.avatar.current_state.speaking:
                    idle_state = self.compute_idle_frame(t)
                    # Merge micro-sway without overriding active non-idle expressions
                    async with self.avatar._lock:
                        if self.avatar.current_state.expression == VTuberExpression.NEUTRAL:
                            self.avatar._current_state.expression = idle_state.expression
                            self.avatar._current_state.expression_intensity = idle_state.expression_intensity
                        self.avatar._current_state.head_x = idle_state.head_x
                        self.avatar._current_state.head_y = idle_state.head_y
                        self.avatar._current_state.body_angle = idle_state.body_angle

                    await self.avatar.render_current_state()

                await asyncio.sleep(self.breathing_interval_sec)

        except asyncio.CancelledError:
            self._is_running = False


# Global singleton instance
idle_behavior_manager = IdleBehaviorManager()
