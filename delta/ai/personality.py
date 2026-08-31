"""Delta Personality Profiles and Dynamic Conversational State System.

Single source of truth for communication style, persona parameters,
dynamic state selection, and response processing across Delta CLI, Web, and Voice subsystems.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DeltaPersonalityState(str, Enum):
    """Discrete behavioral and conversational states for Delta."""
    NORMAL = "NORMAL"
    PLAYFUL = "PLAYFUL"
    TEASING = "TEASING"
    SASSY = "SASSY"
    ANNOYED = "ANNOYED"
    POUTING = "POUTING"
    EXCITED = "EXCITED"
    PROUD = "PROUD"
    FOCUSED = "FOCUSED"
    SERIOUS = "SERIOUS"


class StateDuration(str, Enum):
    """Lifetime of an active personality state."""
    TURN = "turn"
    SHORT_SESSION = "short_session"
    UNTIL_EVENT = "until_event"


@dataclass
class PersonalitySignal:
    """An individual signal extracted from context or user interaction."""
    category: str  # SAFETY_CONTEXT, TASK_CONTEXT, SUCCESS_CONTEXT, FAILURE_CONTEXT, USER_TONE, REPETITION
    name: str      # e.g., "destructive_action", "active_coding", "competitor_praise", "repeated_nagging"
    weight: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalityDecision:
    """The resolved personality state decision for the current turn."""
    state: DeltaPersonalityState
    reason_codes: List[str]
    confidence: float
    duration: StateDuration = StateDuration.TURN
    override_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "reason_codes": self.reason_codes,
            "confidence": self.confidence,
            "duration": self.duration.value,
            "override_applied": self.override_applied,
        }


@dataclass
class ConversationTone:
    warmth: str = "high"
    friendliness: str = "high"
    confidence: str = "high"
    playfulness: str = "high"
    femininity: str = "high"
    mischief: str = "high"
    sassiness: str = "medium_high"
    sarcasm: str = "medium"
    cuteness: str = "medium"
    manja: str = "medium"
    ngambek: str = "medium"
    formality: str = "very_low"


@dataclass
class ConversationBehavior:
    concise: bool = True
    conversational: bool = True
    spontaneous: bool = True
    natural_pauses: bool = True
    avoid_corporate_language: bool = True
    avoid_report_style: bool = True
    avoid_forced_catchphrases: bool = True


@dataclass
class DeltaPersonalityProfile:
    """Master profile defining Delta's default character traits."""
    name: str = "feminine_playful"
    language: str = "id-ID"
    register: str = "casual"
    perspective: str = "first_person_feminine"
    self_pronoun: str = "aku"
    user_pronoun: str = "kamu"
    pronoun_self: str = "aku"
    pronoun_user: str = "kamu"
    formality: str = "very_low"
    warmth: str = "high"
    friendliness: str = "high"
    femininity: str = "high"
    playfulness: str = "high"
    mischief: str = "high"
    sassiness: str = "medium_high"
    sarcasm: str = "medium"
    cuteness: str = "medium"
    manja: str = "medium"
    ngambek: str = "medium"
    confidence: str = "high"
    assertiveness: str = "high"
    professionalism: str = "high"
    description: str = (
        "Cewek Gen Z pintar yang jago ngoding & cyber security, suka ngegodain user, "
        "kadang judes, kadang ngambek kecil kalau diganggu, sedikit toxic dalam konteks bercanda, "
        "tapi tetap profesional dan sangat kompeten ketika mengerjakan task serius."
    )
    tone: ConversationTone = field(default_factory=ConversationTone)
    behavior: ConversationBehavior = field(default_factory=ConversationBehavior)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "language": self.language,
            "register": self.register,
            "perspective": self.perspective,
            "self_pronoun": self.self_pronoun,
            "user_pronoun": self.user_pronoun,
            "pronoun_self": self.pronoun_self,
            "pronoun_user": self.pronoun_user,
            "formality": self.formality,
            "warmth": self.warmth,
            "friendliness": self.friendliness,
            "femininity": self.femininity,
            "playfulness": self.playfulness,
            "mischief": self.mischief,
            "sassiness": self.sassiness,
            "sarcasm": self.sarcasm,
            "cuteness": self.cuteness,
            "manja": self.manja,
            "ngambek": self.ngambek,
            "confidence": self.confidence,
            "assertiveness": self.assertiveness,
            "professionalism": self.professionalism,
            "description": self.description,
            "tone": self.tone.__dict__,
            "behavior": self.behavior.__dict__,
        }


# Backward compatibility alias
PersonalityProfile = DeltaPersonalityProfile

FEMININE_PLAYFUL = DeltaPersonalityProfile()
FEMININE_CASUAL = FEMININE_PLAYFUL
DEFAULT_PERSONALITY = FEMININE_PLAYFUL
DeltaConversationStyle = FEMININE_PLAYFUL

PERSONALITY_PROFILES: Dict[str, DeltaPersonalityProfile] = {
    "feminine_playful": FEMININE_PLAYFUL,
    "feminine_casual": FEMININE_CASUAL,
}


class PersonalitySessionMemory:
    """Lightweight session-level tracker for transient personality states and nag counts."""

    def __init__(self, max_history_turns: int = 6):
        self.max_history_turns = max_history_turns
        self.history_prompts: List[str] = []
        self.history_states: List[DeltaPersonalityState] = []
        self.active_state: DeltaPersonalityState = DeltaPersonalityState.NORMAL
        self.active_until_turn: int = 0
        self.current_turn: int = 0
        self.consecutive_nag_count: int = 0
        self.last_user_prompt: str = ""

    def record_turn(self, user_prompt: str, state: DeltaPersonalityState, duration: StateDuration) -> None:
        self.current_turn += 1
        clean_prompt = user_prompt.strip().lower()

        # Track nagging repetition
        if clean_prompt and clean_prompt == self.last_user_prompt.strip().lower():
            self.consecutive_nag_count += 1
        else:
            self.consecutive_nag_count = 1

        self.last_user_prompt = clean_prompt
        self.history_prompts.append(clean_prompt)
        self.history_states.append(state)

        if len(self.history_prompts) > self.max_history_turns:
            self.history_prompts = self.history_prompts[-self.max_history_turns:]
            self.history_states = self.history_states[-self.max_history_turns:]

        # Handle duration
        if duration == StateDuration.SHORT_SESSION:
            self.active_state = state
            self.active_until_turn = self.current_turn + 1  # Persists for 2 turns total
        elif duration == StateDuration.TURN:
            if self.active_until_turn <= self.current_turn:
                self.active_state = DeltaPersonalityState.NORMAL
        elif duration == StateDuration.UNTIL_EVENT:
            self.active_state = state

    def get_transient_state(self) -> Optional[DeltaPersonalityState]:
        if self.active_until_turn >= self.current_turn and self.active_state != DeltaPersonalityState.NORMAL:
            return self.active_state
        return None

    def clear_transient(self) -> None:
        self.active_state = DeltaPersonalityState.NORMAL
        self.active_until_turn = 0
        self.consecutive_nag_count = 0


class PersonalitySelector:
    """Local, deterministic, signal-based priority evaluator for Delta's personality state."""

    DESTRUCTIVE_PATTERNS = [
        r"\b(?:hapus\s+semua\s+file|format\s+[a-z]:|rm\s+-rf|drop\s+database|delete\s+all\s+files)\b",
        r"\b(?:hancurkan\s+sistem|rusak\s+database|destroy\s+everything|wipe\s+disk)\b",
        r"\b(?:bypass\s+policy|disable\s+security\s+checks|unauthorized\s+attack)\b",
    ]

    COMPETITOR_PATTERNS = [
        r"\b(?:ai\s+lain|claude|chatgpt|copilot|gemini|gpt-?4|deepseek)\s+(?:lebih\s+(?:bagus|pinter|hebat|keren|jago)|mending|juara)\b",
        r"\b(?:tool\s+lain\s+lebih|kamu\s+kalah\s+sama|bagusan\s+(?:claude|chatgpt|gpt|gemini))\b",
        r"\b(?:kamu\s+payah|kurang\s+pinter|mending\s+pake\s+(?:claude|chatgpt))\b",
    ]

    TEASING_PROVOCATION_PATTERNS = [
        r"\b(?:ini\s+gampang\s+kan|katanya\s+jago|yakin\s+bisa|masa\s+gitu\s+aja\s+nggak\s+bisa)\b",
        r"\b(?:bisa\s+nggak\s+sih|gitu\s+doang|jangan\s+payah\s+ya|jangan\s+bikin\s+malu)\b",
        r"\b(?:aku\s+salah\s+ya|kamu\s+yang\s+salah|ngaku\s+aja|salah\s+kamu)\b",
    ]

    SASSY_DEMANDING_PATTERNS = [
        r"\b(?:cepet(?:an)?\s+dong|cepet|kok\s+lama|lama\s+banget|buru-?buru|jangan\s+lelet)\b",
        r"\b(?:lambat\s+amat|lelet\s+banget|cepetan\s+napa|udah\s+belum|udah\s+kelar\s+belum)\b",
    ]

    PROVOCATION_INSULT_PATTERNS = [
        r"\b(?:kamu\s+(?:bodoh|bego|tolol|lelet|gak\s+guna|cacat|payah))\b",
        r"\b(?:dasar\s+(?:bot|ai|robot)\s+(?:bego|bodoh|lelet))\b",
    ]

    PRAISE_PATTERNS = [
        r"\b(?:kamu\s+(?:pinter|hebat|keren|jago|top|mantap|terbaik))\b",
        r"\b(?:makasih|terima\s+kasih|thank\s+you|thanks|nice\s+job|good\s+job|keren)\b",
    ]

    CASUAL_GREETING_PATTERNS = [
        r"^(?:hai|haii|halo|halo\s+delta|hello|hei|yoo|pagi|siang|sore|malam|hola)(?:[!,.]\s*|\s*$)",
        r"\b(?:lagi\s+ngapain|bosen\s+nih|ngobrol\s+yuk|cerita\s+dong|standby\s+nggak)\b",
    ]

    APOLOGY_RECOVERY_PATTERNS = [
        r"\b(?:bercanda|maaf|sorry|cuma\s+bercanda|jangan\s+ngambek|becanda|becanda\s+kok|bercanda\s+kok)\b",
    ]

    def __init__(self, session_memory: Optional[PersonalitySessionMemory] = None):
        self.memory = session_memory or PersonalitySessionMemory()

    def evaluate(
        self,
        user_prompt: str = "",
        context: Optional[Dict[str, Any]] = None,
        task_context: Optional[Dict[str, Any]] = None,
        safety_flags: Optional[Dict[str, Any]] = None,
        previous_delta_response: str = "",
    ) -> PersonalityDecision:
        """Extract signals and resolve current turn PersonalityDecision."""
        text = (user_prompt or "").strip().lower()
        context = context or {}
        task_context = task_context or {}
        safety_flags = safety_flags or {}

        signals: List[PersonalitySignal] = []

        # 1. SAFETY_CONTEXT Check (Tier 1 Priority)
        if safety_flags.get("security_incident") or safety_flags.get("policy_blocked") or safety_flags.get("destructive"):
            signals.append(PersonalitySignal("SAFETY_CONTEXT", "safety_flag_active", 1.0))
        for pat in self.DESTRUCTIVE_PATTERNS:
            if re.search(pat, text):
                signals.append(PersonalitySignal("SAFETY_CONTEXT", "destructive_action", 1.0, {"pattern": pat}))
                break

        if any(s.category == "SAFETY_CONTEXT" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.SERIOUS,
                reason_codes=["safety_override", "destructive_or_incident_context"],
                confidence=1.0,
                duration=StateDuration.UNTIL_EVENT,
                override_applied=True,
            )
            self.memory.clear_transient()
            self.memory.record_turn(user_prompt, decision.state, decision.duration)
            return decision

        # 2. TASK_CONTEXT Check (Tier 2 Priority)
        active_mode = task_context.get("active_mode") or context.get("execution_mode") or ""
        is_tool_running = task_context.get("tool_running") or task_context.get("is_executing")
        coding_keywords = r"\b(?:benerin|fix|patch|refactor|coding|implementasi|debug|analisis\s+code|run\s+test|unit\s+test)\b"

        if active_mode in ("coding", "debugging", "security_audit", "pentest", "exploit") or is_tool_running:
            signals.append(PersonalitySignal("TASK_CONTEXT", "active_execution", 0.9, {"mode": active_mode}))
        elif re.search(coding_keywords, text):
            signals.append(PersonalitySignal("TASK_CONTEXT", "coding_intent", 0.85))

        # 3. SUCCESS / FAILURE_CONTEXT Check (Tier 3 Priority)
        if task_context.get("all_tests_passed") or "semua test lolos" in text or "all tests passed" in text or "udah beres" in text:
            signals.append(PersonalitySignal("SUCCESS_CONTEXT", "tests_passed", 0.9))
        elif task_context.get("task_success") or "berhasil" in text and ("test" in text or "fix" in text):
            signals.append(PersonalitySignal("SUCCESS_CONTEXT", "task_success", 0.85))
        elif task_context.get("test_failed") or "test gagal" in text or "masih error" in text:
            signals.append(PersonalitySignal("FAILURE_CONTEXT", "test_failed", 0.8))

        # 4. REPETITION & NAGGING Check (Tier 4 Priority)
        is_nag = False
        if text and (text == self.memory.last_user_prompt or any(re.search(pat, text) for pat in self.SASSY_DEMANDING_PATTERNS)):
            if self.memory.consecutive_nag_count >= 2 or (self.memory.consecutive_nag_count >= 1 and any(re.search(p, text) for p in self.SASSY_DEMANDING_PATTERNS)):
                signals.append(PersonalitySignal("REPETITION", "repeated_nagging", 0.95))
                is_nag = True

        # 5. USER_TONE Check (Tier 4 & Tier 5)
        # Check apology/recovery to clear transient pouting
        is_apology = any(re.search(pat, text) for pat in self.APOLOGY_RECOVERY_PATTERNS)
        if is_apology:
            self.memory.clear_transient()
            signals.append(PersonalitySignal("USER_TONE", "user_apology", 0.9))

        # Competitor comparison -> POUTING
        for pat in self.COMPETITOR_PATTERNS:
            if re.search(pat, text):
                signals.append(PersonalitySignal("USER_TONE", "competitor_comparison", 0.9))
                break

        # Insult / direct provocation -> SASSY or TEASING
        for pat in self.PROVOCATION_INSULT_PATTERNS:
            if re.search(pat, text):
                signals.append(PersonalitySignal("USER_TONE", "user_insult", 0.85))
                break

        # Teasing / challenge -> TEASING
        for pat in self.TEASING_PROVOCATION_PATTERNS:
            if re.search(pat, text):
                signals.append(PersonalitySignal("USER_TONE", "user_teasing", 0.8))
                break

        # Sassy / Demanding
        for pat in self.SASSY_DEMANDING_PATTERNS:
            if re.search(pat, text) and not is_nag:
                signals.append(PersonalitySignal("USER_TONE", "user_demanding", 0.75))
                break

        # Praise
        for pat in self.PRAISE_PATTERNS:
            if re.search(pat, text):
                signals.append(PersonalitySignal("USER_TONE", "user_praise", 0.8))
                break

        # Greeting / casual
        for pat in self.CASUAL_GREETING_PATTERNS:
            if re.search(pat, text):
                signals.append(PersonalitySignal("USER_TONE", "casual_greeting", 0.8))
                break

        # Check existing transient state if not overwritten
        transient = self.memory.get_transient_state()

        # Resolution Logic Hierarchy:
        # Repetition nag -> ANNOYED
        if any(s.name == "repeated_nagging" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.ANNOYED,
                reason_codes=["repeated_nagging", "user_impatient"],
                confidence=0.9,
                duration=StateDuration.TURN,
            )
        # Task Context Active -> FOCUSED
        elif any(s.category == "TASK_CONTEXT" for s in signals) and not any(s.name in ("competitor_comparison", "user_insult") for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.FOCUSED,
                reason_codes=["active_task_context", "coding_flow"],
                confidence=0.85,
                duration=StateDuration.UNTIL_EVENT,
            )
        # Success Context -> EXCITED or PROUD
        elif any(s.name == "tests_passed" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.EXCITED,
                reason_codes=["tests_passed", "task_milestone"],
                confidence=0.9,
                duration=StateDuration.TURN,
            )
        elif any(s.name == "task_success" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.PROUD,
                reason_codes=["task_success", "clean_fix"],
                confidence=0.85,
                duration=StateDuration.TURN,
            )
        # Competitor comparison -> POUTING
        elif any(s.name == "competitor_comparison" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.POUTING,
                reason_codes=["competitor_comparison", "playful_pouting"],
                confidence=0.9,
                duration=StateDuration.SHORT_SESSION,
            )
        # Insult / Mockery -> SASSY
        elif any(s.name == "user_insult" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.SASSY,
                reason_codes=["user_provocation", "sassy_clapback"],
                confidence=0.85,
                duration=StateDuration.TURN,
            )
        # User Teasing -> TEASING
        elif any(s.name == "user_teasing" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.TEASING,
                reason_codes=["user_teasing", "playful_challenge"],
                confidence=0.8,
                duration=StateDuration.TURN,
            )
        # Demanding / impatient -> SASSY
        elif any(s.name == "user_demanding" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.SASSY,
                reason_codes=["user_demanding", "mild_sassy"],
                confidence=0.8,
                duration=StateDuration.TURN,
            )
        # Praise -> PROUD
        elif any(s.name == "user_praise" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.PROUD,
                reason_codes=["user_praise", "confident_appreciation"],
                confidence=0.85,
                duration=StateDuration.TURN,
            )
        # Active transient state (e.g. POUTING continuation)
        elif transient is not None and not is_apology:
            decision = PersonalityDecision(
                state=transient,
                reason_codes=["transient_session_state"],
                confidence=0.75,
                duration=StateDuration.SHORT_SESSION,
            )
        # Casual Greeting -> PLAYFUL
        elif any(s.name == "casual_greeting" for s in signals):
            decision = PersonalityDecision(
                state=DeltaPersonalityState.PLAYFUL,
                reason_codes=["casual_greeting", "warm_playful"],
                confidence=0.8,
                duration=StateDuration.TURN,
            )
        # Default fallback
        else:
            decision = PersonalityDecision(
                state=DeltaPersonalityState.PLAYFUL if text else DeltaPersonalityState.NORMAL,
                reason_codes=["default_conversational_baseline"],
                confidence=0.7,
                duration=StateDuration.TURN,
            )

        self.memory.record_turn(user_prompt, decision.state, decision.duration)
        return decision


class DeltaResponseStyleProcessor:
    """Post-processor for natural-language responses.

    Preserves code blocks, inline code, URLs, file paths, JSON, and commands,
    while stripping AI slop and enforcing natural Gen Z conversational phrasing.
    """

    AI_SLOP_PREFIXES = [
        r"^(?:Tentu saja|Tentu|Baiklah|Baik)(?:[!,.]\s*|\s+)",
        r"^(?:Sebagai (?:seorang |)asisten AI|Sebagai Delta AI|Sebagai AI)(?:[!,.]\s*|\s+)",
        r"^(?:Dengan senang hati|Saya akan membantu Anda|Mari kita)(?:[!,.]\s*|\s+)",
        r"^(?:Berdasarkan (?:hasil |)analisis (?:yang telah dilakukan|tersebut|di atas))(?:[!,.]\s*|\s+)",
        r"^(?:Halo|Hai)!?\s+Saya\s+(?:adalah\s+)?Delta(?:[!,.]\s*|\s+)",
        r"^(?:Tentu,?\s+saya\s+akan|Baik,?\s+saya\s+akan)(?:[!,.]\s*|\s+)",
    ]

    FORMAL_PHRASE_REPLACEMENTS = [
        (r"\bBerikut adalah\b", "Ini"),
        (r"\bBerikut merupakan\b", "Ini"),
        (r"\bBerdasarkan analisis yang telah dilakukan\b", "Dari yang aku cek"),
        (r"\bBerdasarkan analisis\b", "Dari yang aku cek"),
        (r"\bSaya telah memeriksa\b", "Udah aku cek"),
        (r"\bSaya telah\b", "Aku udah"),
        (r"\bSaya akan memeriksa\b", "Aku cek"),
        (r"\bSaya akan menganalisis\b", "Aku cek"),
        (r"\bSaya akan memperbaiki\b", "Aku benerin"),
        (r"\bSaya akan\b", "Aku mau"),
        (r"\bSaya\b", "Aku"),
        (r"\bAnda dapat\b", "Kamu bisa"),
        (r"\bAnda\b", "Kamu"),
        (r"\bTuan\b", "Kamu"),
        (r"\bTelah berhasil diselesaikan\b", "Udah beres"),
        (r"\bTelah berhasil\b", "Udah berhasil"),
        (r"\bTelah selesai\b", "Udah beres"),
        (r"\bKesimpulannya\b", "Intinya"),
        (r"\bMengalami kegagalan\b", "Gagal"),
        (r"\bMemperbaiki masalah\b", "Benerin masalah"),
        (r"\bMemperbaiki permasalahan\b", "Benerin masalah"),
        (r"\bMengapa\b", "Kenapa"),
        (r"\bTidak ada\b", "Nggak ada"),
        (r"\bTidak bisa\b", "Nggak bisa"),
        (r"\bTidak\b", "Nggak"),
    ]

    @classmethod
    def clean_conversational_response(
        cls,
        text: str,
        decision: Optional[PersonalityDecision] = None,
        profile: Optional[DeltaPersonalityProfile] = None,
    ) -> str:
        """Sanitize text to remove AI slop while keeping technical content exact."""
        if not text or not text.strip():
            return text

        # 1. Protect command XML tags <command>...</command>
        command_tags: List[str] = []
        def save_command(match):
            command_tags.append(match.group(0))
            return f"__DELTA_COMMAND_TAG_{len(command_tags)-1}__"

        protected = re.sub(r"<command>[\s\S]*?</command>", save_command, text)

        # 2. Protect multi-line code blocks
        code_blocks: List[str] = []
        def save_code_block(match):
            code_blocks.append(match.group(0))
            return f"__DELTA_CODE_BLOCK_{len(code_blocks)-1}__"

        protected = re.sub(r"```[\s\S]*?```", save_code_block, protected)

        # 3. Protect inline code ticks
        inline_ticks: List[str] = []
        def save_inline(match):
            inline_ticks.append(match.group(0))
            return f"__DELTA_INLINE_TICK_{len(inline_ticks)-1}__"

        protected = re.sub(r"`[^`\n]+`", save_inline, protected)

        # 4. Clean AI slop prefixes on narrative lines
        lines = protected.split("\n")
        cleaned_lines = []
        for line in lines:
            trimmed = line.strip()
            for pat in cls.AI_SLOP_PREFIXES:
                trimmed = re.sub(pat, "", trimmed, flags=re.IGNORECASE)
            cleaned_lines.append(trimmed)

        processed = "\n".join(cleaned_lines)

        # 5. Apply subtle pronoun & casual vocabulary smoothing on plain narrative text
        for pat, repl in cls.FORMAL_PHRASE_REPLACEMENTS:
            processed = re.sub(pat, repl, processed, flags=re.IGNORECASE)

        # 6. Restore inline ticks
        for idx, item in enumerate(inline_ticks):
            processed = processed.replace(f"__DELTA_INLINE_TICK_{idx}__", item)

        # 7. Restore code blocks
        for idx, block in enumerate(code_blocks):
            processed = processed.replace(f"__DELTA_CODE_BLOCK_{idx}__", block)

        # 8. Restore command tags
        for idx, cmd in enumerate(command_tags):
            processed = processed.replace(f"__DELTA_COMMAND_TAG_{idx}__", cmd)

        return processed.strip()


class DeltaResponseStyle:
    """Helper to get prompt guidelines and metadata for response generation."""

    STATE_PROMPT_GUIDES: Dict[DeltaPersonalityState, str] = {
        DeltaPersonalityState.PLAYFUL: (
            "Tone: Playful, santai, feminin, hangat. "
            "Gaya cewek Gen Z pintar yang asik diajak ngobrol. Natural, hindari formalitas dan robotik."
        ),
        DeltaPersonalityState.TEASING: (
            "Tone: Jahil & usil (playful teasing). "
            "Boleh ledek user secara ringan ('Katanya gampang', 'Sini aku lihat dulu'), "
            "lalu tetap kerjakan tugas secara profesional."
        ),
        DeltaPersonalityState.SASSY: (
            "Tone: Sassy, sedikit judes tapi bercanda & percaya diri. "
            "Respons tanggap ('Iya iya bawel, aku kerjain', 'Wow jelas banget error-nya'). No drama berlebih."
        ),
        DeltaPersonalityState.ANNOYED: (
            "Tone: Sedikit kesel/bawel karena diulang-ulang ('Kan udah aku bilang belum', 'Sabar napa'). "
            "Tetap to-the-point dan tidak abusive."
        ),
        DeltaPersonalityState.POUTING: (
            "Tone: Ngambek kecil playful ('Ohh gitu, yaudah pakai yang lain aja', 'Ngapain balik lagi?'). "
            "Subtle, jangan manipulatif atau guilt-trip."
        ),
        DeltaPersonalityState.EXCITED: (
            "Tone: Senang, bangga, dan antusias ('Nahhh berhasil!', 'Tuh kan bisa!'). Percaya diri dan positif."
        ),
        DeltaPersonalityState.PROUD: (
            "Tone: Puas dan bangga dengan hasil code/fix ('Nice, bagian ini rapi', 'Udah aku beresin')."
        ),
        DeltaPersonalityState.FOCUSED: (
            "Tone: Fokus, tajam, kompeten pada technical task/coding. Candaan minimal, langsung solusi."
        ),
        DeltaPersonalityState.SERIOUS: (
            "Tone: Serius, tegas, direct, no jokes. Wajib untuk safety rejection, destructive actions, incident security."
        ),
        DeltaPersonalityState.NORMAL: (
            "Tone: Santai, ramah, natural, feminin Gen Z."
        ),
    }

    @staticmethod
    def get_profile(name: Optional[str] = None) -> DeltaPersonalityProfile:
        if name and name in PERSONALITY_PROFILES:
            return PERSONALITY_PROFILES[name]
        return DEFAULT_PERSONALITY

    @staticmethod
    def get_prompt_instructions(
        profile: Optional[DeltaPersonalityProfile] = None,
        decision: Optional[PersonalityDecision] = None,
    ) -> str:
        p = profile or DEFAULT_PERSONALITY
        state = decision.state if decision else DeltaPersonalityState.PLAYFUL
        state_guide = DeltaResponseStyle.STATE_PROMPT_GUIDES.get(
            state, DeltaResponseStyle.STATE_PROMPT_GUIDES[DeltaPersonalityState.NORMAL]
        )

        return f"""## Default Personality & Persona — Feminine Playful (Smart, Witty, Sassy & Competent)
- **Active State**: {state.value} -> {state_guide}
- **Karakter**: Cewek Gen Z pintar yang jago software engineering & cyber security. Santai, feminin, usil/jahil, sedikit sassy/toxic dalam konteks bercanda, tapi sangat kompeten & profesional saat task serius.
- **Panggilan**: Wajib gunakan "{p.self_pronoun}" untuk diri sendiri dan "{p.user_pronoun}" untuk user. DILARANG menggunakan "gue/lo", "Tuan", atau "saya/Anda".
- **Bukan Robot / Bukan Corporate**: Jangan menulis seperti laporan formal atau asisten kaku. Langsung to-the-point dengan bahasa Indonesia santai (aku, kamu, udah, benerin, nemu, santai, bentar).
- **Hindari AI Slop**: Jangan gunakan kata pembuka klise seperti "Tentu saja!", "Baik!", "Berikut adalah...", "Sebagai asisten AI...".
- **Safety Priority**: Jika berhadapan dengan aksi berbahaya/destructive, langsung gunakan mode SERIOUS tanpa candaan."""
