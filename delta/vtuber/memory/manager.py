"""
Memory Manager for Delta VTuber.
Coordinates short-term bounded conversation window, persistent long-term storage,
explicit memory commands (remember, forget, retrieve), and context injection into Delta ReAct loops.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from delta.vtuber.memory.schemas import MemoryEntry, MemoryType, ShortTermMemoryBuffer
from delta.vtuber.memory.store import SQLiteMemoryStore


class MemoryManager:
    """
    Central memory orchestrator managing dual-tier memory (short-term & long-term).
    """

    def __init__(
        self,
        store: Optional[SQLiteMemoryStore] = None,
        max_short_term_messages: int = 20,
    ):
        self.store = store or SQLiteMemoryStore()
        self.short_term = ShortTermMemoryBuffer(max_messages=max_short_term_messages)

    def add_short_term_turn(self, user_text: str, agent_response: str) -> None:
        """Record dialogue turn into bounded short-term memory buffer."""
        if user_text:
            self.short_term.add_message("user", user_text)
        if agent_response:
            self.short_term.add_message("assistant", agent_response)

    def store_long_term_fact(
        self,
        fact: str,
        category: str = "user_preference",
        importance: float = 0.8,
    ) -> bool:
        """Persist important fact or preference into long-term storage."""
        entry = MemoryEntry(
            memory_type=MemoryType.IMPORTANT_FACT,
            content=fact.strip(),
            category=category,
            importance=importance,
        )
        return self.store.store(entry)

    def handle_explicit_memory_command(self, user_input: str) -> Tuple[bool, str]:
        """
        Check if user input is an explicit memory command:
        - "ingat bahwa <fact>" / "remember that <fact>" -> store
        - "lupakan bahwa <query>" / "forget that <query>" -> delete
        - "apa yang kamu ingat tentang aku?" / "what do you remember" -> summarize
        """
        inp = user_input.strip()
        lower = inp.lower()

        # 1. Explicit Remember Command
        rem_match = re.search(r"^(?:ingat\s+bahwa|remember\s+that|ingat|remember)\s+(.+)", lower, re.IGNORECASE)
        if rem_match:
            fact_to_remember = inp[rem_match.start(1):].strip()
            success = self.store_long_term_fact(fact_to_remember, category="user_explicit", importance=0.9)
            if success:
                return True, f"Siap, aku sudah mengingat: \"{fact_to_remember}\""
            else:
                return True, "Maaf, informasi tersebut tidak dapat disimpan karena terdeteksi berisi data sensitif/kredensial."

        # 2. Explicit Forget Command
        forg_match = re.search(r"^(?:lupakan\s+bahwa|forget\s+that|lupakan|forget)\s+(.+)", lower, re.IGNORECASE)
        if forg_match:
            query = inp[forg_match.start(1):].strip()
            deleted_count = self.store.delete_by_query(query)
            if deleted_count > 0:
                return True, f"Aku sudah melupakan {deleted_count} ingatan terkait: \"{query}\""
            return True, f"Aku tidak menemukan ingatan terkait: \"{query}\""

        # 3. Explicit Query Memory Command
        if any(q in lower for q in [
            "apa yang kamu ingat tentang aku",
            "apa yang kamu ingat",
            "what do you remember about me",
            "what do you remember",
            "list memory",
            "daftar ingatan"
        ]):
            memories = self.store.retrieve(limit=10)
            if not memories:
                return True, "Aku belum memiliki catatan ingatan jangka panjang tentangmu."
            mem_lines = [f"- {m.content}" for m in memories]
            summary = "Ini beberapa hal yang aku ingat tentang kamu:\n" + "\n".join(mem_lines)
            return True, summary

        return False, ""

    def retrieve_relevant_context(self, current_prompt: str, limit: int = 5) -> str:
        """
        Retrieve relevant facts from long-term memory for agent prompt context injection.
        """
        if not current_prompt or not current_prompt.strip():
            return ""

        words = [w for w in re.findall(r"\w+", current_prompt.lower()) if len(w) > 3]
        matched_memories: Dict[str, MemoryEntry] = {}

        # Search by keywords
        for w in words[:4]:
            found = self.store.retrieve(query=w, limit=3)
            for f in found:
                matched_memories[f.id] = f

        if not matched_memories:
            # Fallback to highest-importance memories
            top = self.store.retrieve(limit=limit)
            for t in top:
                matched_memories[t.id] = t

        if not matched_memories:
            return ""

        lines = [f"- {m.content}" for m in list(matched_memories.values())[:limit]]
        return "VTUBER MEMORY CONTEXT:\n" + "\n".join(lines)


# Global singleton instance
memory_manager = MemoryManager()
