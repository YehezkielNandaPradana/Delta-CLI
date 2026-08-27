# Refactor: web bridge
"""Bridge between Delta CLI Engine and Web Interface."""
import io
import json
import os
import re
import sys
import threading
from typing import Any, Dict, Optional

ANSI_STRIP = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07")
CLI_PREFIX_STRIP = re.compile(r"^(?:Δ AI\s*(?:memikirkan jawaban\.\.\.|→\s*\w+|\n|▔+)|[▔\s]+)+", re.MULTILINE)

def clean_terminal_output(text: str) -> str:
    """Clean ANSI escape codes and TUI terminal banners for Web display."""
    if not text:
        return ""
    # Strip ANSI escape codes
    clean = ANSI_STRIP.sub("", text)
    # Filter out TUI spinner line & header banner
    lines = []
    for line in clean.splitlines():
        trimmed = line.strip()
        if "memikirkan jawaban..." in trimmed:
            continue
        if "Δ AI" in trimmed or "▔" in trimmed:
            continue
        lines.append(line)
    result = "\n".join(lines).strip()
    return result

class EngineBridge:
    def __init__(self, engine: Optional[Any] = None):
        self.engine = engine
        if self.engine:
            self.engine.web_mode = True

    def cancel_execution(self) -> Dict[str, Any]:
        if self.engine and hasattr(self.engine, "_stop_event") and self.engine._stop_event:
            self.engine._stop_event.set()
            return {"status": "ok", "message": "Stop signal sent"}
        return {"status": "error", "message": "No active execution to stop"}

    def get_status(self) -> Dict[str, Any]:
        cwd = getattr(self.engine, "cwd", None) or os.getcwd()
        return {
            "status": "online",
            "version": "1.0.0",
            "working_directory": cwd,
            "llm_enabled": getattr(self.engine.config, "llm_enabled", False) if self.engine and hasattr(self.engine, "config") else False,
        }

    def execute_command(self, cmd: str, execution_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.engine:
            return {"output": f"Executed command (mock): {cmd}", "is_task": False, "task_id": None}

        # Enable web_mode to prevent CLI-specific display rendering to stdout/stream
        original_web_mode = getattr(self.engine, "web_mode", False)
        self.engine.web_mode = True

        output_capture = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = output_capture
            self.engine._stop_event = threading.Event()
            res = self.engine._process_input(cmd, execution_id=execution_id)
            
            # Extract structured response from _process_input dictionary
            if isinstance(res, dict):
                output_str = res.get("response") or res.get("error") or ""
                if not output_str and res.get("command"):
                    output_str = f"Executed: {res['command']}"
                output = output_str if output_str else output_capture.getvalue()
                is_task = res.get("is_task", False)
                task_id = res.get("task_id")
            else:
                output = output_capture.getvalue()
                is_task = False
                task_id = None
        finally:
            sys.stdout = old_stdout
            self.engine._stop_event = None
            self.engine.web_mode = original_web_mode

        return {
            "output": clean_terminal_output(output),
            "response": clean_terminal_output(output),
            "is_task": is_task,
            "task_id": task_id
        }

