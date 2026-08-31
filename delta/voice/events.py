from dataclasses import dataclass
from delta.voice.model import SpeakingState

@dataclass
class VoiceStateEvent:
    state: SpeakingState
    current_text: str = ""
    task_id: str = ""
