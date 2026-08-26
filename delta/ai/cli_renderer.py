# Refactor: cli output
# delta/ai/cli_renderer.py
"""
Terminal CLI Event Renderer for Delta AI Coding Agent.
Renders AgentEvent instances in real-time with clean, terminal-native formatting (Claude Code / Codex style).
"""

import sys
import time
from typing import Any, Dict, List, Optional
from delta.ai.events import AgentEvent, EventType, EventBus, event_bus

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class CLIRenderer:
    """Renders structured AgentEvents into a modern, clean terminal UI."""

    def __init__(self, bus: Optional[EventBus] = None):
        self.bus = bus or event_bus
        self._unsubscribe = self.bus.subscribe(self.render_event)
        self.start_time = time.time()
        self.active_tasks: List[Dict[str, Any]] = []
        self._spinner_idx = 0
        self._last_line_len = 0

    def close(self):
        if self._unsubscribe:
            self._unsubscribe()

    def _clear_status_line(self):
        if self._last_line_len > 0:
            sys.stdout.write("\r" + " " * self._last_line_len + "\r")
            sys.stdout.flush()
            self._last_line_len = 0

    def render_event(self, event: AgentEvent) -> None:
        event_type = event.type if isinstance(event.type, str) else event.type.value

        if event_type == EventType.AGENT_START.value:
            self.start_time = event.timestamp or time.time()

        elif event_type in (EventType.AGENT_STATUS.value, EventType.AGENT_THINKING.value):
            status = event.status_text or "Thinking..."
            frame = SPINNER_FRAMES[self._spinner_idx % len(SPINNER_FRAMES)]
            self._spinner_idx += 1
            line = f"  \033[36m{frame}\033[0m \033[2m{status}\033[0m"
            self._clear_status_line()
            sys.stdout.write(line)
            sys.stdout.flush()
            self._last_line_len = len(status) + 10

        elif event_type == EventType.TOOL_START.value:
            tool = event.tool or "tool"
            inp = event.input or {}
            target = inp.get("path") or inp.get("command") or inp.get("pattern") or ""
            target_str = f" \033[34m{target}\033[0m" if target else ""
            status_text = event.status_text or f"Executing {tool}"
            frame = SPINNER_FRAMES[self._spinner_idx % len(SPINNER_FRAMES)]
            self._spinner_idx += 1

            self._clear_status_line()
            line = f"  \033[36m{frame}\033[0m {status_text}{target_str}"
            sys.stdout.write(line)
            sys.stdout.flush()
            self._last_line_len = len(status_text) + len(target) + 10

        elif event_type == EventType.TOOL_RESULT.value:
            self._clear_status_line()
            tool = event.tool or "Tool"
            if event.success:
                status_text = event.status_text or f"Completed {tool}"
                sys.stdout.write(f"  \033[32m✓\033[0m \033[2m{status_text}\033[0m\n")
            else:
                err = event.error.get("message") if event.error else "Failed"
                sys.stdout.write(f"  \033[31m✗\033[0m {tool} failed: {err}\n")
            sys.stdout.flush()

        elif event_type == EventType.FILE_UPDATE.value:
            self._clear_status_line()
            path = event.path or "file"
            added = event.added_lines or 0
            removed = event.removed_lines or 0
            sys.stdout.write(f"  \033[32m✓\033[0m Updated \033[34m{path}\033[0m (\033[32m+{added}\033[0m \033[31m-{removed}\033[0m)\n")
            sys.stdout.flush()

        elif event_type == EventType.COMMAND_START.value:
            self._clear_status_line()
            sys.stdout.write(f"  \033[36m⠋\033[0m Running \033[1m$ {event.command}\033[0m\n")
            sys.stdout.flush()

        elif event_type == EventType.COMMAND_COMPLETED.value:
            self._clear_status_line()
            if event.exit_code == 0:
                sys.stdout.write("  \033[32m✓\033[0m Command completed\n")
            else:
                sys.stdout.write(f"  \033[31m✗\033[0m Command failed with exit code {event.exit_code}\n")
            sys.stdout.flush()

        elif event_type == EventType.DIAGNOSTIC.value:
            self._clear_status_line()
            count = event.count or 0
            sev = event.severity or "warning"
            sys.stdout.write(f"  \033[33m⚠ Found {count} diagnostic issues ({sev})\033[0m\n")
            sys.stdout.flush()

        elif event_type == EventType.AGENT_COMPLETE.value:
            self._clear_status_line()

