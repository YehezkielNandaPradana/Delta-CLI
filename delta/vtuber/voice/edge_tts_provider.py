"""
Edge-TTS Provider Implementation for Delta VTuber.
Generates speech audio using Microsoft Edge Online TTS without requiring paid API keys.
"""

import asyncio
import io
import logging
from typing import Optional
from delta.vtuber.voice.schemas import AudioData, SpeechChunk

logger = logging.getLogger(__name__)

# Default high-quality Indonesian / English voices
DEFAULT_ID_VOICE = "id-ID-GadisNeural"
DEFAULT_EN_VOICE = "en-US-AriaNeural"


class EdgeTTSProvider:
    """
    Concrete TTSProvider using edge-tts library.
    Falls back gracefully or yields synthesis error if edge-tts is not installed or network fails.
    """

    def __init__(
        self,
        voice: str = DEFAULT_ID_VOICE,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        volume: str = "+0%",
    ):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume
        self._is_available: Optional[bool] = None

    async def initialize(self) -> None:
        try:
            import edge_tts  # noqa: F401
            self._is_available = True
        except ImportError:
            logger.warning("edge-tts package is not installed. Synthesis will raise RuntimeError.")
            self._is_available = False

    async def shutdown(self) -> None:
        pass

    async def synthesize(self, chunk: SpeechChunk) -> AudioData:
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("edge-tts library is not installed. Please install with: pip install edge-tts")

        if not chunk.text or not chunk.text.strip():
            return AudioData(
                chunk_id=chunk.id,
                audio_bytes=b"",
                sample_rate=24000,
                format="mp3",
                duration_sec=0.0,
                metadata={"provider": "EdgeTTSProvider", "empty": True},
            )

        # Dynamic speed & pitch adjustment based on emotion & prosody profile if provided
        from delta.vtuber.voice.prosody import ProsodyModulator
        prosody = ProsodyModulator.modulate(chunk.emotion, chunk.intensity)

        effective_rate = prosody.rate_ssml if self.rate == "+0%" else self.rate
        effective_pitch = prosody.pitch_ssml if self.pitch == "+0Hz" else self.pitch

        communicate = edge_tts.Communicate(
            text=chunk.text,
            voice=self.voice,
            rate=effective_rate,
            pitch=effective_pitch,
            volume=self.volume,
        )

        audio_buffer = io.BytesIO()
        async for part in communicate.stream():
            if isinstance(part, dict) and part.get("type") == "audio":
                data = part.get("data")
                if data:
                    audio_buffer.write(data)

        audio_bytes = audio_buffer.getvalue()
        # Rough duration estimate for mp3 (~16KB per sec at 128kbps)
        estimated_duration = max(0.2, round(len(audio_bytes) / 16000.0, 2))

        return AudioData(
            chunk_id=chunk.id,
            speech_id=chunk.speech_id,
            sequence=chunk.sequence,
            audio_bytes=audio_bytes,
            sample_rate=24000,
            format="mp3",
            duration_sec=estimated_duration,
            metadata={
                "provider": "EdgeTTSProvider",
                "voice": self.voice,
                "text_len": len(chunk.text),
                "emotion": chunk.emotion.value,
                "byte_size": len(audio_bytes),
            },
        )
