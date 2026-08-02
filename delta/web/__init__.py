"""
Delta Web Interface Package

This package provides web-based interfaces for Delta CLI,
including the landing page, chat interface, and report viewer.
"""

__version__ = "1.0.0"

from delta.web.chat import DeltaChatInterface

__all__ = [
    "DeltaChatInterface",
]