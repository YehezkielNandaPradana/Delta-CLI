"""
Voice Activity Detection (VAD) Algorithm for Microphone Audio Frames.
Calculates energy thresholds, hangover buffers, and speech boundary states.
"""

import math
from typing import Sequence, Union
from delta.vtuber.voice.stt.schemas import VADState


class VoiceActivityDetector:
    """
    Lightweight energy-based VAD with debounce hangover frames for natural pauses.
    """

    def __init__(
        self,
        energy_threshold: float = 0.025,
        hangover_frames: int = 6,  # ~300ms pause tolerance before declaring SPEECH_END
        min_speech_frames: int = 2,  # ~100ms energy before declaring SPEECH_START
    ):
        self.energy_threshold = energy_threshold
        self.hangover_frames = hangover_frames
        self.min_speech_frames = min_speech_frames

        self._state: VADState = VADState.SILENCE
        self._consecutive_speech: int = 0
        self._consecutive_silence: int = 0

    @property
    def current_state(self) -> VADState:
        return self._state

    def calculate_frame_energy(self, samples: Sequence[Union[float, int]]) -> float:
        """Calculate RMS energy of a frame."""
        if not samples:
            return 0.0
        sum_sq = sum(float(s) * float(s) for s in samples)
        return math.sqrt(sum_sq / len(samples))

    def process_frame(self, samples: Sequence[Union[float, int]]) -> VADState:
        """
        Process audio frame samples and update VAD state machine.
        """
        energy = self.calculate_frame_energy(samples)
        is_active = (energy >= self.energy_threshold)

        if is_active:
            self._consecutive_speech += 1
            self._consecutive_silence = 0

            if self._state == VADState.SILENCE and self._consecutive_speech >= self.min_speech_frames:
                self._state = VADState.SPEECH_START
            elif self._state in (VADState.SPEECH_START, VADState.SPEAKING):
                self._state = VADState.SPEAKING
        else:
            self._consecutive_silence += 1
            self._consecutive_speech = 0

            if self._state in (VADState.SPEECH_START, VADState.SPEAKING):
                if self._consecutive_silence >= self.hangover_frames:
                    self._state = VADState.SPEECH_END
                else:
                    # Still in hangover buffer
                    self._state = VADState.SPEAKING
            elif self._state == VADState.SPEECH_END:
                self._state = VADState.SILENCE

        return self._state

    def reset(self) -> None:
        """Reset VAD counters and state."""
        self._state = VADState.SILENCE
        self._consecutive_speech = 0
        self._consecutive_silence = 0
