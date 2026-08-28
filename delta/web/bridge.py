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

    def get_directory_tree(self, sub_path: str = "") -> Dict[str, Any]:
        root_dir = os.path.abspath(getattr(self.engine, "cwd", None) or os.getcwd())
        target_dir = os.path.abspath(os.path.join(root_dir, sub_path))

        # Security: Prevent directory traversal outside root
        if not target_dir.startswith(root_dir):
            return {"status": "error", "message": "Access denied: Path outside workspace"}

        ignored_names = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", ".idea", ".vscode"}

        def build_tree(current_path: str, max_depth: int = 4, depth: int = 0):
            if depth > max_depth:
                return []
            items = []
            try:
                entries = sorted(os.scandir(current_path), key=lambda e: (not e.is_dir(), e.name.lower()))
                for entry in entries:
                    if entry.name in ignored_names:
                        continue
                    rel_path = os.path.relpath(entry.path, root_dir).replace("\\", "/")
                    is_directory = entry.is_dir(follow_symlinks=False)
                    size = entry.stat(follow_symlinks=False).st_size if not is_directory else 0
                    ext = os.path.splitext(entry.name)[1].lower() if not is_directory else ""

                    item = {
                        "name": entry.name,
                        "path": rel_path,
                        "is_dir": is_directory,
                        "size": size,
                        "extension": ext
                    }

                    if is_directory:
                        item["children"] = build_tree(entry.path, max_depth=max_depth, depth=depth + 1)
                        item["size"] = sum(c.get("size", 0) for c in item["children"])
                    items.append(item)
            except (PermissionError, FileNotFoundError):
                pass
            return items

        tree = build_tree(target_dir)
        total_files = 0
        total_folders = 0

        def count_nodes(nodes):
            nonlocal total_files, total_folders
            for n in nodes:
                if n["is_dir"]:
                    total_folders += 1
                    count_nodes(n.get("children", []))
                else:
                    total_files += 1

        count_nodes(tree)

        return {
            "status": "ok",
            "root_path": root_dir,
            "total_files": total_files,
            "total_folders": total_folders,
            "tree": tree
        }

    def read_file_content(self, file_path: str) -> Dict[str, Any]:
        root_dir = os.path.abspath(getattr(self.engine, "cwd", None) or os.getcwd())
        abs_path = os.path.abspath(os.path.join(root_dir, file_path))

        # Security check
        if not abs_path.startswith(root_dir):
            return {"status": "error", "message": "Access denied: Path outside workspace"}

        if not os.path.isfile(abs_path):
            return {"status": "error", "message": "File not found"}

        try:
            stat = os.stat(abs_path)
            if stat.st_size > 2 * 1024 * 1024:  # 2MB size limit
                return {"status": "error", "message": "File too large to view directly (>2MB)"}

            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            lines = content.splitlines()
            return {
                "status": "ok",
                "path": file_path.replace("\\", "/"),
                "filename": os.path.basename(abs_path),
                "size": stat.st_size,
                "content": content,
                "line_count": len(lines),
                "extension": os.path.splitext(abs_path)[1].lower()
            }
        except Exception as exc:
            return {"status": "error", "message": str(exc)}


