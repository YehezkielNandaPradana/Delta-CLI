"""Bridge between Delta CLI Engine and Web Interface."""
import io
import sys
from typing import Any, Dict, Optional

class EngineBridge:
    def __init__(self, engine: Optional[Any] = None):
        self.engine = engine

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "online",
            "version": "1.0.0",
            "llm_enabled": getattr(self.engine.config, "llm_enabled", False) if self.engine and hasattr(self.engine, "config") else False,
        }

    def execute_command(self, cmd: str) -> str:
        if not self.engine:
            return f"Executed command (mock): {cmd}"
        output_capture = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = output_capture
            self.engine._process_input(cmd)
        finally:
            sys.stdout = old_stdout
        return output_capture.getvalue()
