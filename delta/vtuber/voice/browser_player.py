"""
Browser Audio Transport and WebSocket Relay for Delta VTuber.
Streams synthesized audio chunks and playback control frames to connected browser clients.
"""

import base64
import json
import logging
import threading
from typing import Any, Dict, List, Optional, Set
from delta.vtuber.voice.schemas import AudioData, SpeechLifecycleEvent, SpeechLifecycleEventType, SpeechState

logger = logging.getLogger(__name__)


class BrowserAudioPlayer:
    """
    AudioPlayer implementation that relays synthesized audio directly to
    connected Web browser clients over WebSockets / HTTP long-poll / SSE channels.
    """

    def __init__(self):
        self._is_playing: bool = False
        self._current_speech_id: Optional[str] = None
        self._subscribers: Set[Any] = set()
        self._lock = threading.RLock()

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def register_client(self, client_queue: Any) -> None:
        """Register a client queue to receive audio messages."""
        with self._lock:
            self._subscribers.add(client_queue)

    def unregister_client(self, client_queue: Any) -> None:
        """Unregister a client queue."""
        with self._lock:
            if client_queue in self._subscribers:
                self._subscribers.remove(client_queue)

    def broadcast_message(self, message: Dict[str, Any]) -> None:
        """Broadcast a control or audio frame to all connected clients."""
        with self._lock:
            for client in list(self._subscribers):
                try:
                    if hasattr(client, "put_nowait"):
                        client.put_nowait(message)
                    elif callable(client):
                        client(message)
                except Exception as exc:
                    logger.debug("Failed to deliver audio frame to client: %s", exc)

    async def play(self, audio: AudioData) -> None:
        """
        Stream audio chunk to browser clients.
        """
        self._is_playing = True
        self._current_speech_id = audio.speech_id

        # Encode raw audio bytes into base64 payload
        audio_b64 = base64.b64encode(audio.audio_bytes).decode("ascii") if audio.audio_bytes else ""

        # 1. Send speech_start / audio frame
        payload = {
            "type": "speech_audio_chunk",
            "speech_id": audio.speech_id,
            "chunk_id": audio.chunk_id,
            "sequence": audio.sequence,
            "format": audio.format,
            "sample_rate": audio.sample_rate,
            "duration_sec": audio.duration_sec,
            "audio_base64": audio_b64,
            "metadata": audio.metadata,
        }
        self.broadcast_message(payload)

    async def stop(self) -> None:
        """
        Broadcast immediate speech interrupt to all connected browser clients.
        """
        self._is_playing = False
        payload = {
            "type": "speech_stop",
            "speech_id": self._current_speech_id or "all",
            "reason": "interrupt",
        }
        self.broadcast_message(payload)
        self._current_speech_id = None


# Global singleton instance
browser_audio_player = BrowserAudioPlayer()
