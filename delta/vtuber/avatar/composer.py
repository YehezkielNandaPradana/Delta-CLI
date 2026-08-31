"""
Unified Avatar Frame Compositor for Delta VTuber.
Aggregates subsystem layers (Expression, LipSync, Eyes/Blink, Head, Body, Hair Physics, Breathing)
into a single, authoritative FinalAvatarFrame with clear parameter ownership.
"""

import math
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from delta.vtuber.avatar.eye import EyeBehaviorController
from delta.vtuber.avatar.physics import PhysicsController
from delta.vtuber.avatar.schemas import AvatarState
from delta.vtuber.emotion.schemas import VTuberExpression


class FinalAvatarFrame(BaseModel):
    """
    Composed, fully-resolved avatar frame ready for Live2D/VTS rendering.
    """
    expression: VTuberExpression = VTuberExpression.NEUTRAL
    expression_intensity: float = 0.5
    mouth_open: float = 0.0
    mouth_form: float = 0.0
    head_x: float = 0.0
    head_y: float = 0.0
    body_angle: float = 0.0
    eye_x: float = 0.0
    eye_y: float = 0.0
    eye_l_open: float = 1.0
    eye_r_open: float = 1.0
    breath: float = 0.5
    hair_front: float = 0.0
    hair_side: float = 0.0
    hair_back: float = 0.0
    speaking: bool = False
    timestamp: float = Field(default_factory=time.time)

    def to_avatar_state(self) -> AvatarState:
        """Convert back to canonical AvatarState representation."""
        return AvatarState(
            expression=self.expression,
            expression_intensity=self.expression_intensity,
            mouth_open=self.mouth_open,
            mouth_form=self.mouth_form,
            head_x=self.head_x,
            head_y=self.head_y,
            body_angle=self.body_angle,
            speaking=self.speaking,
            timestamp=self.timestamp,
        )


class AvatarFrameComposer:
    """
    Composites multiple animation & physical layers into FinalAvatarFrame:
    1. Base Expression Layer (ExpressionController)
    2. Lip-Sync Layer (Audio/LipSyncController) -> Owns Mouth
    3. Eye Behavior Layer (Gaze + Blink) -> Owns Eyes
    4. Head & Body Posture Layer (Smoothing & Personality)
    5. Physics Layer (Hair, Accessories)
    6. Breathing Layer (Organic Continuous Sine Wave)
    """

    def __init__(self):
        self.eye_ctrl = EyeBehaviorController()
        self.physics_ctrl = PhysicsController()
        self._start_time = time.time()

    def compose_frame(
        self,
        base_state: AvatarState,
        mood_modifier: Optional[Dict[str, float]] = None,
        curiosity_mod: float = 0.5,
        energy_mod: float = 0.5,
        current_time: Optional[float] = None,
    ) -> FinalAvatarFrame:
        now = current_time or time.time()
        elapsed = now - self._start_time

        # 1. Base Expression & Mood Modulation
        expr = base_state.expression
        expr_intensity = base_state.expression_intensity
        if mood_modifier:
            if expr == VTuberExpression.SMILE and "happiness" in mood_modifier:
                expr_intensity = max(0.0, min(1.0, expr_intensity * (0.8 + 0.4 * mood_modifier["happiness"])))
            elif expr in (VTuberExpression.THINKING, VTuberExpression.CONFUSED) and "stress" in mood_modifier:
                expr_intensity = max(0.0, min(1.0, expr_intensity * (0.8 + 0.4 * mood_modifier["stress"])))

        # 2. Mouth Ownership (LipSync)
        # Controller resets mouth_open=0.0 on speech stop / barge-in (interruption ownership),
        # composer passes the LipSync-driven value through without fake gating.
        mouth_open = base_state.mouth_open
        mouth_form = base_state.mouth_form

        # 3. Head & Body Modulation with Mood
        head_x = base_state.head_x * (0.9 + 0.2 * energy_mod)
        head_y = base_state.head_y * (0.9 + 0.2 * energy_mod)
        body_angle = base_state.body_angle

        # Subtle idle posture motion
        if not base_state.speaking and expr == VTuberExpression.NEUTRAL:
            idle_sway = 0.03 * math.sin(elapsed * 0.8)
            head_x += idle_sway

        # 4. Eye System (Gaze + Blink)
        eye_data = self.eye_ctrl.update(now, expression=expr, curiosity_modifier=curiosity_mod)

        # 5. Physics Simulation (Hair Sway)
        phys = self.physics_ctrl.update_physics(
            head_x=head_x,
            head_y=head_y,
            body_angle=body_angle,
            speaking=base_state.speaking,
        )

        # 6. Continuous Breathing
        # Smooth organic sine oscillation (period ~3.5 seconds)
        breath_rate = 1.8 if base_state.speaking else (2.2 if expr == VTuberExpression.EXCITED else 1.5)
        breath_val = 0.5 + 0.5 * math.sin(elapsed * breath_rate)

        return FinalAvatarFrame(
            expression=expr,
            expression_intensity=round(expr_intensity, 2),
            mouth_open=round(mouth_open, 3),
            mouth_form=round(mouth_form, 3),
            head_x=round(head_x, 3),
            head_y=round(head_y, 3),
            body_angle=round(body_angle, 3),
            eye_x=eye_data["eye_ball_x"],
            eye_y=eye_data["eye_ball_y"],
            eye_l_open=eye_data["eye_l_open"],
            eye_r_open=eye_data["eye_r_open"],
            breath=round(breath_val, 2),
            hair_front=phys["hair_front"],
            hair_side=phys["hair_side"],
            hair_back=phys["hair_back"],
            speaking=base_state.speaking,
            timestamp=now,
        )


# Global Composer instance
avatar_frame_composer = AvatarFrameComposer()
