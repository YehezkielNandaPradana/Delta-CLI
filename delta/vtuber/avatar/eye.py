"""
Eye Behavior and Natural Blink Controller for Delta VTuber.
Supports natural random blinking, double blinks, saccadic gaze shifts, and emotion-aware gaze.
"""

import math
import random
import time
from typing import Dict, Tuple
from delta.vtuber.emotion.schemas import VTuberExpression


class BlinkController:
    """
    Manages organic blinking dynamics (open, closing, closed, opening, double-blink).
    """

    def __init__(self, min_interval: float = 2.5, max_interval: float = 6.0, blink_duration: float = 0.15):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.blink_duration = blink_duration

        self._last_blink_time = time.time()
        self._next_blink_interval = random.uniform(self.min_interval, self.max_interval)
        self._is_blinking = False
        self._blink_start_time = 0.0
        self._is_double_blink = False
        self._double_blink_step = 0

    def update(self, current_time: float) -> float:
        """
        Step blink state machine and return eye opening factor (0.0 = closed, 1.0 = fully open).
        """
        dt_since_last = current_time - self._last_blink_time

        if not self._is_blinking:
            if dt_since_last >= self._next_blink_interval:
                self._is_blinking = True
                self._blink_start_time = current_time
                self._is_double_blink = random.random() < 0.2  # 20% chance of double blink
                self._double_blink_step = 1 if self._is_double_blink else 0
            return 1.0

        # In blink animation
        progress = (current_time - self._blink_start_time) / self.blink_duration
        if progress >= 1.0:
            if self._double_blink_step == 1:
                # Trigger second blink
                self._double_blink_step = 2
                self._blink_start_time = current_time
                progress = 0.0
            else:
                # Finished blinking
                self._is_blinking = False
                self._last_blink_time = current_time
                self._next_blink_interval = random.uniform(self.min_interval, self.max_interval)
                return 1.0

        # Bell curve closure: 0 -> 1 -> 0 closure
        # Eye open is inverted (1.0 at 0 and 1, 0.0 at 0.5)
        eye_open = abs(2.0 * (progress - 0.5))
        return max(0.0, min(1.0, eye_open))


class EyeBehaviorController:
    """
    Coordinates eye gaze, micro-saccades, and emotion-aware gaze positioning.
    """

    def __init__(self):
        self.blink_ctrl = BlinkController()
        self.eye_x: float = 0.0
        self.eye_y: float = 0.0
        self._target_x: float = 0.0
        self._target_y: float = 0.0
        self._last_saccade_time = time.time()
        self._next_saccade_interval = random.uniform(1.0, 3.5)

    def update(
        self,
        current_time: float,
        expression: VTuberExpression = VTuberExpression.NEUTRAL,
        curiosity_modifier: float = 0.5,
    ) -> Dict[str, float]:
        """
        Compute current eye parameter frame (eye_open_l, eye_open_r, eye_x, eye_y).
        """
        # 1. Update Blink
        blink_factor = self.blink_ctrl.update(current_time)

        # 2. Micro-saccades & gaze updates
        if current_time - self._last_saccade_time >= self._next_saccade_interval:
            self._last_saccade_time = current_time
            self._next_saccade_interval = random.uniform(1.2 - 0.5 * curiosity_modifier, 3.5 - 1.0 * curiosity_modifier)

            # Expression-directed gaze bias
            if expression == VTuberExpression.THINKING:
                self._target_x = random.uniform(0.1, 0.4)
                self._target_y = random.uniform(0.1, 0.3)
            elif expression == VTuberExpression.CONFUSED:
                self._target_x = random.uniform(-0.3, 0.3)
                self._target_y = random.uniform(-0.1, 0.1)
            elif expression == VTuberExpression.SAD:
                self._target_x = random.uniform(-0.1, 0.1)
                self._target_y = random.uniform(-0.4, -0.1)
            else:
                self._target_x = random.uniform(-0.25, 0.25)
                self._target_y = random.uniform(-0.15, 0.15)

        # Smooth gaze transition (LERP)
        self.eye_x += (self._target_x - self.eye_x) * 0.15
        self.eye_y += (self._target_y - self.eye_y) * 0.15

        return {
            "eye_l_open": round(blink_factor, 3),
            "eye_r_open": round(blink_factor, 3),
            "eye_ball_x": round(self.eye_x, 3),
            "eye_ball_y": round(self.eye_y, 3),
        }
