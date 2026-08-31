"""
Audio Player Abstraction and Implementations for Delta VTuber.
"""

import asyncio
from typing import Optional, Protocol, runtime_checkable
from delta.vtuber.voice.schemas import AudioData


@runtime_checkable
class AudioPlayer(Protocol):
    """
    Protocol defining the interface for Audio Playback engines.
    """

    async def play(self, audio: AudioData) -> None:
        """
        Play audio data asynchronously. Must return when playback finishes or is cancelled.
        """
        ...

    async def stop(self) -> None:
        """
        Stop currently playing audio immediately.
        """
        ...

    @property
    def is_playing(self) -> bool:
        """Return whether audio is currently playing."""
        ...


class MockAudioPlayer:
    """
    Mock Audio Player for tests and headless environments.
    Simulates playback duration without opening physical audio devices.
    """

    def __init__(self, playback_speed_multiplier: float = 1.0):
        self.playback_speed_multiplier = playback_speed_multiplier
        self._is_playing = False
        self._current_task: Optional[asyncio.Task] = None
        self.played_audio_list: list[AudioData] = []

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    async def play(self, audio: AudioData) -> None:
        self._is_playing = True
        self.played_audio_list.append(audio)

        play_duration = max(0.01, (audio.duration_sec / max(self.playback_speed_multiplier, 0.1)))

        try:
            self._current_task = asyncio.current_task()
            await asyncio.sleep(play_duration)
        except asyncio.CancelledError:
            self._is_playing = False
            raise
        finally:
            self._is_playing = False
            self._current_task = None

    async def stop(self) -> None:
        self._is_playing = False
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            self._current_task = None
