# delta/__init__.py
"""
Delta - AI-Powered Cyber Security Assessment CLI
=================================================
Delta is a modern AI Command Line Interface for Cyber Security Assessment,
Security Audit, and Penetration Testing on authorized systems.

Delta combines AI-assisted natural language understanding with
professional security testing tools in a modern terminal interface.

Author: HackerAI
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "HackerAI"
__license__ = "MIT"

from delta.core.config import DeltaConfig
from delta.core.engine import DeltaEngine
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.core.display import DisplayManager
from delta.core.plugin import PluginManager
from delta.ai.intent import IntentEngine, IntentResult
from delta.ai.knowledge import KnowledgeBase

__all__ = [
    "DeltaConfig",
    "DeltaEngine", 
    "Database",
    "SessionManager",
    "DisplayManager",
    "PluginManager",
    "IntentEngine",
    "IntentResult",
    "KnowledgeBase",
    "__version__",
]