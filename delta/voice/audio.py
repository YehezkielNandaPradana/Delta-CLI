import threading
import time
import base64
from typing import Optional

class AudioOutput:
    def __init__(self):
        self.is_playing = False
        self._stop_flag = False

    def play_bytes(self, audio_data: bytes) -> None:
        self.is_playing = True
        self._stop_flag = False

        # 1. Forward audio chunk to Browser Audio Player (Web SSE / stream)
        try:
            from delta.vtuber.voice.browser_player import browser_audio_player
            b64_audio = base64.b64encode(audio_data).decode("utf-8")
            browser_audio_player.broadcast_message({
                "type": "audio_chunk",
                "format": "wav",
                "sample_rate": 22050,
                "channels": 1,
                "audio_base64": b64_audio,
                "duration_sec": max(0.2, round(len(audio_data) / 32000.0, 2)),
                "timestamp": time.time(),
            })
        except Exception:
            pass

        # 2. Local OS speaker playback (winsound on Windows / stdlib / native)
        try:
            import winsound
            if audio_data.startswith(b"RIFF"):
                winsound.PlaySound(audio_data, winsound.SND_MEMORY | winsound.SND_ASYNC)
        except Exception:
            pass

        play_time = min(len(audio_data) / 32000.0, 3.0)
        start = time.time()
        while time.time() - start < play_time and not self._stop_flag:
            time.sleep(0.05)
        self.is_playing = False

    def stop(self) -> None:
        self._stop_flag = True
        self.is_playing = False
        try:
            import winsound
            winsound.PlaySound(None, 0)
        except Exception:
            pass
