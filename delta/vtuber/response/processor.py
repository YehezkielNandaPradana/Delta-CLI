"""
Response Processor for Delta VTuber Unified Pipeline.
Formats raw agent text into dual display/speech channels and resolves emotion context.
"""

from typing import Any, Dict, Optional
from delta.vtuber.emotion import EmotionEngine, emotion_engine
from delta.vtuber.events import VTuberEmotion
from delta.vtuber.personality import PersonalityManager, personality_manager
from delta.vtuber.response.schemas import ResponsePayload


class ResponseProcessor:
    """
    Transforms raw agent outputs into structured ResponsePayloads.
    Separates Markdown display text from natural spoken TTS text using PersonalityManager rules.
    """

    def __init__(
        self,
        personality_mgr: Optional[PersonalityManager] = None,
        emotion_eng: Optional[EmotionEngine] = None,
    ):
        self.personality = personality_mgr or personality_manager
        self.emotion_engine = emotion_eng or emotion_engine

    def process(
        self,
        raw_text: str,
        response_id: Optional[str] = None,
        emotion: Optional[VTuberEmotion] = None,
        intensity: float = 0.7,
        is_error: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ResponsePayload:
        """
        Build a canonical ResponsePayload from raw text.
        """
        if not raw_text or not raw_text.strip():
            return ResponsePayload(
                response_id=response_id or "",
                display_text="",
                speech_text="",
                emotion=VTuberEmotion.NEUTRAL,
                emotion_intensity=0.3,
                metadata=metadata or {},
            )

        # 1. Format Markdown vs Spoken Text via Personality layer
        display_text, speech_text = self.personality.format_agent_speech(raw_text)

        # 2. Resolve Emotion
        resolved_emotion = emotion
        if not resolved_emotion:
            if is_error:
                resolved_emotion = VTuberEmotion.CONFUSED
            else:
                curr = self.emotion_engine.current_emotion
                val = curr.value if hasattr(curr, "value") else str(curr)
                try:
                    resolved_emotion = VTuberEmotion(val)
                except ValueError:
                    resolved_emotion = VTuberEmotion.NEUTRAL

        import uuid
        res_id = response_id or str(uuid.uuid4())

        return ResponsePayload(
            response_id=res_id,
            display_text=display_text,
            speech_text=speech_text,
            emotion=resolved_emotion,
            emotion_intensity=max(0.0, min(1.0, float(intensity))),
            metadata=metadata or {},
        )


# Global singleton instance
response_processor = ResponseProcessor()
