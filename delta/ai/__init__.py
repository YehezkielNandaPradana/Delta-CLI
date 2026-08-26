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

from delta.ai.llm import LLMEngine, parse_command_from_response, strip_command_tags, PROVIDERS, MODEL_PRESETS

from delta.ai.memory import MemoryManager

from delta.ai.intent import IntentEngine, IntentResult

from delta.ai.context import ContextManager

from delta.ai.knowledge import KnowledgeBase

from delta.ai.reasoning import ReasoningEngine

from delta.ai.recommendation import RecommendationEngine

from delta.ai.llm import LLMEngine, parse_command_from_response, strip_command_tags, PROVIDERS, MODEL_PRESETS

from delta.ai.memory import MemoryManager

from delta.ai.events import AgentEvent, EventType, EventBus, event_bus

from delta.ai.task_manager import AgentTaskManager

from delta.ai.cli_renderer import CLIRenderer

from delta.ai.react_loop import ReActAgentEngine

__all__ = [

    "IntentEngine", "IntentResult",

    "ContextManager",

    "KnowledgeBase",

    "ReasoningEngine",

    "RecommendationEngine",

    "LLMEngine",

    "MemoryManager",

    "PROVIDERS",

    "MODEL_PRESETS",

    "parse_command_from_response",

    "strip_command_tags",

    "AgentEvent", "EventType", "EventBus", "event_bus",

    "AgentTaskManager", "CLIRenderer", "ReActAgentEngine",

]