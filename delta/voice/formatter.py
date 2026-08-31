import re
from typing import List, Optional, Union
from delta.ai.personality import DeltaPersonalityState

class VoiceFormatter:
    # Conversational Feminine Casual/Playful phrasing map for natural speech
    FEMININE_CASUAL_PATTERNS = [
        # Task start & plan
        (r"^(?:saya akan mulai menganalisis|memulai analisis tugas|task started).*$", "Oke, aku mulai cek dulu ya."),
        (r"^(?:saya telah membuat rencana|plan created|membuat rencana).*$", "Aku udah ngerti masalahnya. Sekarang aku bikin rencananya."),
        (r"^(?:menganalisis|meneliti|researching).*$", "Aku cek bagian yang berhubungan dulu."),
        # Code & fixes
        (r"^(?:menerapkan perbaikan|mengubah kode|coding).*$", "Oke, aku benerin bagian ini ya."),
        (r"^(?:menjalankan pengujian|running tests|testing).*$", "Fix-nya udah masuk. Aku jalanin test sekarang."),
        # Completion & success
        (r"^(?:tugas telah selesai dengan sukses|semua pengujian berhasil|task completed successfully|all tests passed).*$", "Udah beres. Semua test-nya lolos."),
        (r"^(?:analisis telah selesai).*$", "Udah selesai aku cek ya."),
        # Failures & Debug
        (r"^(?:pengujian gagal|tests failed).*$", "Test-nya masih gagal. Aku cek penyebabnya dulu ya."),
        (r"^(?:memulai investigasi|debugging).*$", "Oke, ketemu penyebabnya. Aku benerin sekarang."),
        (r"^(?:tindakan diblokir oleh kebijakan|action blocked by policy).*$", "Yang ini nggak bisa aku jalanin ya, karena diblokir policy."),
    ]

    GENZ_PHRASE_PATTERNS = FEMININE_CASUAL_PATTERNS

    @classmethod
    def format_for_speech(
        cls,
        text: str,
        style: str = "feminine_casual",
        state: Optional[Union[str, DeltaPersonalityState]] = None,
    ) -> str:
        # Strip markdown code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Strip inline code ticks
        text = re.sub(r"`([^`]+)`", r"\1", text)
        # Remove headers #
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        # Remove bold/italic * _
        text = re.sub(r"[\*_]{1,3}", "", text)
        # Normalize code identifiers like AuthService.validate() -> AuthService validate
        text = re.sub(r"(\w+)\.(\w+)\(\)", r"\1 \2", text)

        # Technical acronym normalization
        tech_map = {
            r"C#": "C sharp",
            r"\bAPI\b": "A P I",
            r"\bHTTP\b": "H T T P",
            r"\bHTTPS\b": "H T T P S",
            r"\bNPM\b": "N P M",
            r"\bCLI\b": "C L I",
            r"\bURL\b": "U R L",
            r"\bSQL\b": "S Q L",
        }
        for pattern, replacement in tech_map.items():
            text = re.sub(pattern, replacement, text)

        # State-specific tuning
        resolved_state = None
        if state is not None:
            if isinstance(state, DeltaPersonalityState):
                resolved_state = state
            elif isinstance(state, str):
                try:
                    resolved_state = DeltaPersonalityState(state.upper())
                except ValueError:
                    resolved_state = None

        if resolved_state == DeltaPersonalityState.SERIOUS:
            # Direct, no playful filler
            text = re.sub(r"\b(?:hehe|yaa|dong|deh|yuk)\b", "", text, flags=re.IGNORECASE)

        # Feminine Casual / Gen Z Style Natural Phrasing Transformation
        if style in ("feminine_casual", "genz_cute", "feminine_playful") or resolved_state is not None:
            # Apply regex replacements for milestone sentences
            trimmed = text.strip().lower()
            for pattern, replacement in cls.FEMININE_CASUAL_PATTERNS:
                if re.search(pattern, trimmed, re.IGNORECASE):
                    text = replacement
                    break

            # Natural token smoothing (subtle, non-anime)
            subs = [
                (r"\bsaya telah\b", "aku udah"),
                (r"\bsaya akan\b", "aku mau"),
                (r"\bsaya\b", "aku"),
                (r"\banda\b", "kamu"),
                (r"\btuan\b", "kamu"),
                (r"\btelah berhasil\b", "udah beres"),
                (r"\bselesai\b", "beres"),
                (r"\bmenemukan\b", "nemu"),
                (r"\bmemperbaiki\b", "benerin"),
                (r"\bterdapat\b", "ada"),
                (r"\btidak bisa\b", "nggak bisa"),
                (r"\btidak\b", "nggak"),
            ]
            for pat, repl in subs:
                text = re.sub(pat, repl, text, flags=re.IGNORECASE)

        # Clean extra whitespace
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def segment_sentences(text: str) -> List[str]:
        if not text:
            return []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]
