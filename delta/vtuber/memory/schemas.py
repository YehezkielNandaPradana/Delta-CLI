"""
Data models and schemas for Delta VTuber Short-term and Long-term Conversation Memory.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    CONVERSATION = "conversation"      # Short-term dialogue turn
    USER_PREFERENCE = "user_preference"  # Stable user settings / preferences
    IMPORTANT_FACT = "important_fact"    # Facts user explicitly told Delta to remember
    SESSION_CONTEXT = "session_context"  # Current active project / target context
    PROJECT_CONTEXT = "project_context"  # Persistent project facts
    TEMPORARY_CONTEXT = "temporary_context"  # Time-limited context with expiration


class MemoryEntry(BaseModel):
    """
    Individual memory unit stored in SQLite or memory store.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.CONVERSATION
    content: str
    category: str = "general"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = "user"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    last_accessed: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ShortTermMemoryBuffer(BaseModel):
    """
    Bounded sliding-window short-term conversation context.
    """
    max_messages: int = 20
    messages: List[Dict[str, str]] = Field(default_factory=list)

    def add_message(self, role: str, text: str) -> None:
        self.messages.append({"role": role, "text": text, "time": str(time.time())})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def clear(self) -> None:
        self.messages.clear()
