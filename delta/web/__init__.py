"""
Delta Web Interface Package

This package provides web-based interfaces for Delta CLI,
including the landing page, chat interface, and report viewer.
"""

__version__ = "1.0.0"

try:
    from delta.web.chat import DeltaChatInterface
    _WEB_AVAILABLE = True
except ImportError:
    DeltaChatInterface = None
    _WEB_AVAILABLE = False

def is_available() -> bool:
    """Check if Flask web UI is available."""
    return _WEB_AVAILABLE

__all__ = [
    "DeltaChatInterface",
    "is_available",
]