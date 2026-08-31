"""
Mock STT Provider for Testing, CI, and Simulation without Hardware/Cloud APIs.
"""

import asyncio
from typing import Any, AsyncIterator, Dict, List, Optional
from delta.vtuber.voice.stt.schemas import STTFinalResult, STTPartialResult, STTResult


class MockSTTProvider:
    """
    Mock STT provider simulating speech recognition responses.
    """

    def __init__(
        self,
        canned_response: str = "Delta tolong cek status server",
        confidence: float = 0.95,
        latency_sec: float = 0.01,
        fail_on_keyword: Optional[str] = None,
    ):
        self.canned_response = canned_response
        self.confidence = confidence
        self.latency_sec = latency_sec
        self.fail_on_keyword = fail_on_keyword
        self.is_initialized = False
        self.transcribed_payloads: List[bytes] = []

    async def initialize(self) -> None:
        self.is_initialized = True

    async def shutdown(self) -> None:
        self.is_initialized = False

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "id-ID",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> STTResult:
        if self.fail_on_keyword and self.fail_on_keyword in self.canned_response:
            raise RuntimeError(f"Mock STT transcription failed due to keyword: {self.fail_on_keyword}")

        if self.latency_sec > 0:
            await asyncio.sleep(self.latency_sec)

        self.transcribed_payloads.append(audio_data)

        return STTFinalResult(
            text=self.canned_response,
            confidence=self.confidence,
            language=language,
            duration_sec=max(0.5, len(audio_data) / 32000.0),
            metadata=metadata or {"provider": "MockSTTProvider"},
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "id-ID",
    ) -> AsyncIterator[STTResult]:
        words = self.canned_response.split()
        accum = []

        for w in words[:-1]:
            accum.append(w)
            if self.latency_sec > 0:
                await asyncio.sleep(self.latency_sec)
            yield STTPartialResult(
                text=" ".join(accum),
                confidence=self.confidence * 0.9,
                language=language,
            )

        yield STTFinalResult(
            text=self.canned_response,
            confidence=self.confidence,
            language=language,
        )
