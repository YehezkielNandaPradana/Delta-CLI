"""
Personality Behavior and Natural Speech Formatting Layer for Delta VTuber.
Transforms full markdown/agent outputs into clean, natural conversational spoken text while
leaving code blocks, technical facts, and display formatting intact.
"""

import re
from typing import Tuple
from delta.vtuber.personality.schemas import PersonaProfile


class PersonalityBehavior:
    """
    Handles natural phrasing, speech text sanitization, and style formatting.
    """

    def __init__(self, profile: PersonaProfile):
        self.profile = profile

    def format_responses(self, raw_agent_response: str) -> Tuple[str, str]:
        """
        Split raw agent response into:
        1. display_text: Full formatted markdown with codeblocks, lists, and tables intact.
        2. speech_text: Clean, conversational verbal text without raw markdown symbols/code dumps.
        """
        if not raw_agent_response:
            return "", ""

        display_text = raw_agent_response.strip()

        # 1. Strip code blocks from spoken text and replace with brief natural summary
        speech_text = re.sub(
            r"```[a-zA-Z0-9_-]*\n(.*?)```",
            "Ini kodenya ya.",
            display_text,
            flags=re.DOTALL,
        )

        # 2. Strip inline backticks, bold, italics, links, and markdown headers
        speech_text = re.sub(r"`([^`]+)`", r"\1", speech_text)
        speech_text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", speech_text)
        speech_text = re.sub(r"[*_~#]+", "", speech_text)

        # 3. Clean multiple whitespace / newlines
        speech_text = re.sub(r"\n+", ". ", speech_text)
        speech_text = re.sub(r"\s+", " ", speech_text).strip()

        # 4. Apply light tone adjustments if formality is low
        if self.profile.formality < 0.5:
            speech_text = self._apply_casual_indonesian(speech_text)

        return display_text, speech_text

    def _apply_casual_indonesian(self, text: str) -> str:
        """Slight natural phrasing adjustments for casual VTuber tone."""
        replacements = [
            (r"\bBerikut adalah\b", "Ini"),
            (r"\bTelah berhasil\b", "Sudah berhasil"),
            (r"\bMengapa\b", "Kenapa"),
            (r"\bMemeriksa\b", "Mengecek"),
        ]
        res = text
        for pat, repl in replacements:
            res = re.sub(pat, repl, res, flags=re.IGNORECASE)
        return res
