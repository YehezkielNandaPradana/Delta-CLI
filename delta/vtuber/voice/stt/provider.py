"""
STT Provider Protocol Definition for Delta VTuber.
"""

from typing import Any, AsyncIterator, Dict, Optional, Protocol, runtime_checkable
from delta.vtuber.voice.stt.schemas import STTResult


@runtime_checkable
class STTProvider(Protocol):
    """
    Protocol defining interface for Speech-to-Text transcribers (Whisper, Web Speech, Cloud STT, Mock).
    """

    async def initialize(self) -> None:
        """Initialize provider resources."""
        ...

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "id-ID",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> STTResult:
        """
        Transcribe raw audio bytes into a final STTResult.
        """
        ...

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "id-ID",
    ) -> AsyncIterator[STTResult]:
        """
        Stream transcription chunks yielding partial and final results.
        """
        ...

    async def shutdown(self) -> None:
        """Release provider resources cleanly."""
        ...
