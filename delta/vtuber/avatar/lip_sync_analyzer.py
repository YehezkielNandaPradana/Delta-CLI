"""
Audio Amplitude Analyzer and Lip-Sync DSP Utilities for Delta VTuber.
Calculates RMS volume, applies noise gate, normalization, and attack/release envelope smoothing.
"""

import math
from typing import List, Sequence, Union


class AudioAmplitudeAnalyzer:
    """
    Analyzes raw audio sample sequences or byte arrays to compute smooth,
    noise-gated lip-sync mouth opening levels (0.0 to 1.0).
    """

    def __init__(
        self,
        noise_gate_threshold: float = 0.02,
        attack_factor: float = 0.6,
        release_factor: float = 0.2,
        gain_multiplier: float = 2.5,
    ):
        self.noise_gate_threshold = noise_gate_threshold
        self.attack_factor = attack_factor
        self.release_factor = release_factor
        self.gain_multiplier = gain_multiplier
        self._current_amplitude: float = 0.0

    @property
    def current_amplitude(self) -> float:
        return self._current_amplitude

    def calculate_rms(self, samples: Sequence[Union[float, int]]) -> float:
        """
        Compute Root Mean Square (RMS) of audio sample window.
        """
        if not samples:
            return 0.0

        sum_squares = sum(float(s) * float(s) for s in samples)
        rms = math.sqrt(sum_squares / len(samples))
        return rms

    def process_samples(self, samples: Sequence[Union[float, int]]) -> float:
        """
        Calculate RMS, apply noise gating, gain normalization, and attack/release smoothing.
        Returns final mouth opening value clamped between 0.0 and 1.0.
        """
        raw_rms = self.calculate_rms(samples)

        # 1. Noise Gate
        if raw_rms < self.noise_gate_threshold:
            target_amplitude = 0.0
        else:
            # 2. Gain & Normalization
            normalized = (raw_rms - self.noise_gate_threshold) / (1.0 - self.noise_gate_threshold)
            target_amplitude = min(1.0, max(0.0, normalized * self.gain_multiplier))

        # 3. Asymmetric Attack / Release Smoothing
        # Attack = mouth opens quickly; Release = mouth closes smoothly
        if target_amplitude > self._current_amplitude:
            self._current_amplitude += (target_amplitude - self._current_amplitude) * self.attack_factor
        else:
            self._current_amplitude += (target_amplitude - self._current_amplitude) * self.release_factor

        self._current_amplitude = round(max(0.0, min(1.0, self._current_amplitude)), 3)
        return self._current_amplitude

    def reset(self) -> None:
        """Reset internal amplitude tracker to zero."""
        self._current_amplitude = 0.0
