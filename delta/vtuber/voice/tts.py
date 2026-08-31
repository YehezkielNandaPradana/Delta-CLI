"""
TTS Provider Abstraction and Implementations for Delta VTuber.
"""

import asyncio
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from delta.vtuber.voice.schemas import AudioData, SpeechChunk


@runtime_checkable
class TTSProvider(Protocol):
    """
    Protocol defining the interface for TTS synthesis backends.
    """

    async def synthesize(self, chunk: SpeechChunk) -> AudioData:
        """
        Synthesize text from a SpeechChunk into AudioData asynchronously.
        """
        ...

    async def initialize(self) -> None:
        """Initialize provider resources if necessary."""
        ...

    async def shutdown(self) -> None:
        """Release provider resources."""
        ...


class MockTTSProvider:
    """
    Mock TTS Provider for offline testing, CI, and simulation.
    Generates synthetic dummy audio frames without requiring external services.
    """

    def __init__(self, latency_sec: float = 0.01, fail_on_keyword: Optional[str] = None):
        self.latency_sec = latency_sec
        self.fail_on_keyword = fail_on_keyword
        self.synthesized_chunks: list[SpeechChunk] = []

    async def initialize(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def synthesize(self, chunk: SpeechChunk) -> AudioData:
        if self.fail_on_keyword and self.fail_on_keyword in chunk.text:
            raise RuntimeError(f"Mock TTS synthesis failed for: {chunk.text}")

        if self.latency_sec > 0:
            await asyncio.sleep(self.latency_sec)

        self.synthesized_chunks.append(chunk)

        # Estimate duration roughly based on text length (~15 chars/sec)
        est_duration = max(0.2, round(len(chunk.text) / 15.0, 2))
        dummy_bytes = b"\x00\x00" * int(est_duration * 100)

        return AudioData(
            chunk_id=chunk.id,
            speech_id=chunk.speech_id,
            audio_bytes=dummy_bytes,
            sample_rate=24000,
            format="raw",
            duration_sec=est_duration,
            metadata={
                "provider": "MockTTSProvider",
                "text_len": len(chunk.text),
                "emotion": chunk.emotion.value,
            },
        )
