# delta/ai/__init__.py
"""
AI Engine for Delta - Natural language understanding and intent recognition.
Provides offline intent parsing, context memory, and recommendation engine.
"""

from delta.ai.intent import IntentEngine, IntentResult
from delta.ai.context import ContextManager
from delta.ai.knowledge import KnowledgeBase
from delta.ai.reasoning import ReasoningEngine
from delta.ai.recommendation import RecommendationEngine

__all__ = [
    "IntentEngine", "IntentResult",
    "ContextManager",
    "KnowledgeBase",
    "ReasoningEngine",
    "RecommendationEngine",
]