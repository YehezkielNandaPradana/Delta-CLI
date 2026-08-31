"""
Speech Prosody Controller & Modulator for Delta VTuber.
Modulates speech rate, pitch, and SSML strings according to active emotion and intensity.
"""

from typing import Dict, Optional
from delta.vtuber.emotion.schemas import VTuberEmotion
from delta.vtuber.voice.prosody.schemas import EMOTION_PROSODY_DEFAULTS, ProsodyProfile


class ProsodyModulator:
    """
    Computes fine-grained prosody profiles and SSML tags from emotion and intensity.
    """

    @classmethod
    def modulate(
        cls,
        emotion: VTuberEmotion = VTuberEmotion.NEUTRAL,
        intensity: float = 0.5,
    ) -> ProsodyProfile:
        """
        Calculate adjusted prosody profile for TTS synthesis.
        """
        clamped_intensity = max(0.0, min(1.0, float(intensity)))
        base = EMOTION_PROSODY_DEFAULTS.get(emotion, EMOTION_PROSODY_DEFAULTS[VTuberEmotion.NEUTRAL])

        # Scale rate and pitch offset based on emotion intensity
        base_rate: float = float(base["rate"])
        base_pitch_hz: float = float(base["pitch_hz"])

        final_rate = 1.0 + (base_rate - 1.0) * (0.5 + 0.5 * clamped_intensity)
        final_pitch_hz = base_pitch_hz * clamped_intensity

        # Format SSML tags for Edge-TTS
        rate_pct = int(round((final_rate - 1.0) * 100))
        rate_ssml = f"{'+' if rate_pct >= 0 else ''}{rate_pct}%"

        pitch_hz_int = int(round(final_pitch_hz))
        pitch_ssml = f"{'+' if pitch_hz_int >= 0 else ''}{pitch_hz_int}Hz"

        return ProsodyProfile(
            emotion=emotion,
            rate_multiplier=round(final_rate, 2),
            pitch_offset_hz=round(final_pitch_hz, 1),
            rate_ssml=rate_ssml,
            pitch_ssml=pitch_ssml,
        )


class ProsodyController:
    """
    Maintains active speech prosody state.
    """

    def __init__(self):
        self._current_profile = ProsodyProfile()

    @property
    def current_profile(self) -> ProsodyProfile:
        return self._current_profile

    def update_for_emotion(self, emotion: VTuberEmotion, intensity: float = 0.5) -> ProsodyProfile:
        self._current_profile = ProsodyModulator.modulate(emotion, intensity)
        return self._current_profile


# Global singleton instance
prosody_controller = ProsodyController()
