# delta/core/tui.py
"""
Delta CLI — Modern AI Agent Terminal User Interface.

Design Philosophy:
  • Modern AI coding agent CLI (Claude Code / Codex aesthetic).
  • Minimalist, high density, terminal-native typography.
  • Indentation-aware text wrapping engine (Strict NO horizontal scrolling).
  • Live Agent workflow tree synced with the core AgentEvent bus.
  • Compact thinking indicator with expandable tree ('>' / '<' / 'd' details).
  • Adaptive responsive layout for 80x24 up to ultrawide displays.
"""

import ctypes
import io
import os
import re
import shlex
import shutil
import sys
import textwrap
import threading
import time
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from delta.core.auth import verify_credentials
from delta.ai.events import event_bus, AgentEvent, EventType, AgentStep, StepStatus, StepKind

# True when the terminal accepted ANSI/VT color sequences.
_VT_OK = False

def _enable_vt() -> None:
    """Enable ANSI/VT processing and UTF-8 output where possible."""
    global _VT_OK
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
    except Exception:
        pass

    if os.name != "nt":
        _VT_OK = True
        return

    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            after = ctypes.c_uint32()
            kernel32.GetConsoleMode(handle, ctypes.byref(after))
            _VT_OK = bool(after.value & 0x0004)
    except Exception:
        _VT_OK = False

    if not _VT_OK:
        setattr(T, "RESET", "")
        setattr(T, "BOLD", "")
        setattr(T, "DIM", "")
        setattr(T, "ITALIC", "")

def _fg(r: int, g: int, b: int) -> str:
    if not _VT_OK:
        return ""
    return f"\033[38;2;{r};{g};{b}m"

def _bg(r: int, g: int, b: int) -> str:
    if not _VT_OK:
        return ""
    return f"\033[48;2;{r};{g};{b}m"

# ---------------------------------------------------------------------------
# Native Win32 console API
# ---------------------------------------------------------------------------
class _COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

class _SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]

class _CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [("dwSize", _COORD), ("dwCursorPosition", _COORD),
                ("wAttributes", ctypes.c_ushort), ("srWindow", _SMALL_RECT),
                ("dwMaximumWindowSize", _COORD)]

class _CONSOLE_CURSOR_INFO(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_uint), ("bVisible", ctypes.c_int)]

class _KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [("bKeyDown", ctypes.c_int), ("wRepeatCount", ctypes.c_ushort),
                ("wVirtualKeyCode", ctypes.c_ushort), ("wVirtualScanCode", ctypes.c_ushort),
                ("uChar", ctypes.c_wchar), ("dwControlKeyState", ctypes.c_uint)]

class _MOUSE_EVENT_RECORD(ctypes.Structure):
    _fields_ = [("dwMousePosition", _COORD), ("dwButtonState", ctypes.c_uint),
                ("dwControlKeyState", ctypes.c_uint), ("dwEventFlags", ctypes.c_uint)]

class _INPUT_RECORD_UNION(ctypes.Union):
    _fields_ = [("key", _KEY_EVENT_RECORD), ("mouse", _MOUSE_EVENT_RECORD)]

class _INPUT_RECORD(ctypes.Structure):
    _fields_ = [("EventType", ctypes.c_ushort), ("Event", _INPUT_RECORD_UNION)]

_VK_SPECIAL = {
    0x25: "K", 0x27: "M", 0x26: "H", 0x28: "P",
    0x24: "G", 0x23: "O", 0x2E: "S", 0x21: "I", 0x22: "Q",
}

# ---------------------------------------------------------------------------
# Color System (Refined Developer Dark Palette)
# ---------------------------------------------------------------------------
class T:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"

    # Base neutrals
    BG = (13, 14, 18)             # #0D0E12 Near-black canvas
    BORDER = (55, 65, 81)         # #374151 Subtle border
    BORDER_SUBTLE = (38, 42, 53)  # #262A35 Faint separator
    TEXT = (243, 244, 246)        # #F3F4F6 Primary bright off-white
    TEXT_MUTED = (156, 163, 175)  # #9CA3AF Secondary muted gray
    TEXT_DIM = (107, 114, 128)    # #6B7280 Dim helper text
    MUTED = (156, 163, 175)       # Compatibility alias

    # Delta Accent & States
    ACCENT = (56, 189, 248)       # #38BDF8 Sky Cyan Accent
    CYAN = (56, 189, 248)
    SUCCESS = (74, 222, 128)      # #4ADE80 Emerald Green
    GREEN = (74, 222, 128)
    WARNING = (251, 191, 36)      # #FBBF24 Amber Warning
    YELLOW = (251, 191, 36)
    ERROR = (248, 113, 113)       # #F87171 Coral Red Error
    RED = (248, 113, 113)
    CODE = (186, 230, 253)        # #BAE6FD Light Code Token
    TOOL = (147, 197, 253)        # #93C5FD Tool Tree Accent
    USER = (129, 140, 248)        # #818CF8 User Prompt Accent

ANSI_STRIP = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07")

# ---------------------------------------------------------------------------
# Terminal Text Wrapping Engine (Strict NO Horizontal Scrolling)
# ---------------------------------------------------------------------------
def plain_text(text: str) -> str:
    """Strip ANSI color escapes."""
    return ANSI_STRIP.sub("", text)

def visual_width(s: str) -> int:
    """Calculate terminal visual column width accounting for East Asian characters."""
    plain = plain_text(s)
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in plain)

def wrap_terminal_text(
    text: str,
    available_width: int,
    indent: str = "",
    continuation_prefix: str = ""
) -> List[str]:
    """
    Wrap text to strictly fit within available_width.
    Handles unbroken tokens (paths, commands, hashes) by breaking them safely.
    Applies indent to line 0, and continuation_prefix to lines 1..N.
    """
    if available_width <= 4:
        return [text[:max(available_width, 1)]]

    lines_out: List[str] = []
    paragraphs = text.split("\n")

    for p_idx, raw_para in enumerate(paragraphs):
        para = raw_para.rstrip()
        if not para:
            lines_out.append(indent if p_idx == 0 else continuation_prefix)
            continue

        # Process words / tokens with soft break capability
        words = para.split(" ")
        curr_line = ""
        is_first = (p_idx == 0 and len(lines_out) == 0)

        for w_idx, word in enumerate(words):
            prefix = indent if is_first else continuation_prefix
            lead_space = " " if curr_line else ""
            candidate = curr_line + lead_space + word
            avail = available_width - visual_width(prefix)

            if visual_width(candidate) <= avail:
                curr_line = candidate
            else:
                if curr_line:
                    lines_out.append(prefix + curr_line)
                    curr_line = ""
                    is_first = False

                # If word itself is longer than available width, break word into slices
                avail_now = available_width - visual_width(continuation_prefix if not is_first else indent)
                word_rem = word
                while visual_width(word_rem) > avail_now and avail_now > 2:
                    # Find cut point
                    cut = 0
                    acc = 0
                    for ch in word_rem:
                        cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
                        if acc + cw > avail_now:
                            break
                        acc += cw
                        cut += 1
                    slice_str = word_rem[:cut]
                    prefix_slice = indent if is_first else continuation_prefix
                    lines_out.append(prefix_slice + slice_str)
                    word_rem = word_rem[cut:]
                    is_first = False

                curr_line = word_rem

        if curr_line:
            prefix = indent if is_first else continuation_prefix
            lines_out.append(prefix + curr_line)

    return lines_out or [""]

class DeltaTUI:
    """Full-screen modern AI Agent CLI interface with shared workflow tree."""

    def __init__(self, engine) -> None:
        self.engine = engine
        self.engine.tui_mode = True
        _enable_vt()
        self._native = False
        self._hout = None
        self._hin = None
        self._kernel32 = None

        if os.name == "nt":
            try:
                kernel32 = ctypes.windll.kernel32
                h = kernel32.GetStdHandle(-11)
                mode = ctypes.c_uint32()
                if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
                    self._hout = h
                    self._kernel32 = kernel32
                    self._native = True
                    hin = kernel32.GetStdHandle(-10)
                    imode = ctypes.c_uint32()
                    if kernel32.GetConsoleMode(hin, ctypes.byref(imode)):
                        self._hin = hin
                        kernel32.SetConsoleMode(
                            hin, (imode.value & ~0x0040) | 0x0080 | 0x0010
                        )
            except Exception:
                pass

        self.messages: list = []
        self.scroll = 0
        self.show_cursor = True
        self.input_text = ""
        self.input_pos = 0
        self._history: List[str] = []
        self._hist_idx = 0
        self._help_idx: Optional[int] = None
        self._processing = False
        self._draw_lock = threading.Lock()
        self._term_w, self._term_h = self._size()

        # Shared Agent Workflow State
        self.workflow_expanded: bool = False
        self.show_node_details: bool = False
        self.current_execution_id: Optional[str] = None
        self.active_steps: Dict[str, Dict[str, Any]] = {}
        self.active_task_label: str = ""
        self.active_status_text: str = "Ready"

        # Subscribe to shared EventBus
        self._unsubscribe = event_bus.subscribe(self._on_agent_event)

    def _on_agent_event(self, ev: AgentEvent) -> None:
        """Process real-time agent workflow events from event_bus."""
        if ev.execution_id:
            self.current_execution_id = ev.execution_id
        if ev.status_text:
            self.active_status_text = ev.status_text

        # Track steps
        step_dict = ev.payload.get("step") if (ev.payload and isinstance(ev.payload, dict)) else None
        if step_dict and isinstance(step_dict, dict) and "id" in step_dict:
            step_id = step_dict["id"]
            self.active_steps[step_id] = Object_merge(self.active_steps.get(step_id, {}), step_dict)

        if ev.type == EventType.AGENT_START:
            self.active_steps.clear()
            self.active_task_label = ev.status_text or "Working"
        elif ev.type == EventType.AGENT_COMPLETE:
            self.active_status_text = "Task completed"

        # Trigger live in-place repaint if processing
        if self._processing:
            self._repaint_live_only()

    @staticmethod
    def _size() -> Tuple[int, int]:
        try:
            s = shutil.get_terminal_size(fallback=(100, 30))
            return (s.columns, s.lines)
        except Exception:
            return (100, 30)

    def _size_changed(self) -> bool:
        w, h = self._size()
        if w == self._term_w and h == self._term_h:
            return False
        self._term_w, self._term_h = w, h
        return True

    def _write(self, text: str = "") -> None:
        out_stream = sys.__stdout__ or sys.stdout
        try:
            out_stream.write(text)
        except UnicodeEncodeError:
            safe = text
            for orig, repl in {
                "Δ": "D", "◐": "o", "●": "O", "█": "#", "─": "-",
                "╭": "+", "╮": "+", "╰": "+", "╯": "+", "│": "|",
                "├": "+", "┤": "+", "↑": "^", "↓": "v", "→": "->",
                "·": "*", "✓": "v", "✔": "v", "✗": "x", "✘": "x", "⚠": "!",
                "ℹ": "i", "•": "*", "…": "...", "└": "+", "│": "|"
            }.items():
                safe = safe.replace(orig, repl)
            out_stream.write(safe.encode("ascii", "replace").decode("ascii"))
        out_stream.flush()

    def _move(self, row: int, col: int = 1) -> None:
        if self._native and self._kernel32 is not None and self._hout is not None:
            self._kernel32.SetConsoleCursorPosition(
                self._hout, _COORD(max(0, int(col) - 1), max(0, int(row) - 1))
            )
        else:
            out_stream = sys.__stdout__ or sys.stdout
            out_stream.write(f"\033[{int(row)};{int(col)}H")

    def _clear_line(self) -> None:
        if self._native and self._kernel32 is not None and self._hout is not None:
            info = _CONSOLE_SCREEN_BUFFER_INFO()
            if not self._kernel32.GetConsoleScreenBufferInfo(
                self._hout, ctypes.byref(info)
            ):
                return
            width = info.srWindow.Right - info.srWindow.Left + 1
            n = max(width - info.dwCursorPosition.X, 0)
            written = ctypes.c_ulong()
            self._kernel32.FillConsoleOutputCharacterW(
                self._hout, ctypes.c_wchar(" "), n, info.dwCursorPosition,
                ctypes.byref(written)
            )
        else:
            out_stream = sys.__stdout__ or sys.stdout
            out_stream.write("\033[K")

    def _clear_screen(self) -> None:
        if self._native and self._kernel32 is not None and self._hout is not None:
            info = _CONSOLE_SCREEN_BUFFER_INFO()
            if self._kernel32.GetConsoleScreenBufferInfo(
                self._hout, ctypes.byref(info)
            ):
                left = info.srWindow.Left
                top = info.srWindow.Top
                w = info.srWindow.Right - left + 1
                h = info.srWindow.Bottom - top + 1
                if top != 0 or left != 0:
                    win = _SMALL_RECT(0, 0, w - 1, h - 1)
                    self._kernel32.SetConsoleWindowInfo(
                        self._hout, True, ctypes.byref(win)
                    )
                total = max(w * h, 1)
                written = ctypes.c_ulong()
                self._kernel32.FillConsoleOutputCharacterW(
                    self._hout, ctypes.c_wchar(" "), total, _COORD(left, top),
                    ctypes.byref(written)
                )
                self._kernel32.FillConsoleOutputAttribute(
                    self._hout, 7, total, _COORD(left, top),
                    ctypes.byref(written)
                )
                self._kernel32.SetConsoleCursorPosition(
                    self._hout, _COORD(left, top)
                )
        else:
            out_stream = sys.__stdout__ or sys.stdout
            out_stream.write("\033[2J\033[H")
        (sys.__stdout__ or sys.stdout).flush()

    def _hide_real_cursor(self) -> None:
        if self._native and self._kernel32 is not None and self._hout is not None:
            info = _CONSOLE_CURSOR_INFO(25, False)
            self._kernel32.SetConsoleCursorInfo(self._hout, ctypes.byref(info))
        else:
            out_stream = sys.__stdout__ or sys.stdout
            out_stream.write("\033[?25l")
        (sys.__stdout__ or sys.stdout).flush()

    def _show_real_cursor(self) -> None:
        if self._native and self._kernel32 is not None and self._hout is not None:
            info = _CONSOLE_CURSOR_INFO(25, True)
            self._kernel32.SetConsoleCursorInfo(self._hout, ctypes.byref(info))
        else:
            out_stream = sys.__stdout__ or sys.stdout
            out_stream.write("\033[?25h\033[0 q")
        (sys.__stdout__ or sys.stdout).flush()

    @property
    def compact(self) -> bool:
        w, h = self._size()
        return h < 24 or w < 65

    def _layout(self) -> dict:
        w, h = self._size()
        main_w = w
        header_rows = 2 if not self.compact else 1
        chrome_bottom = header_rows + 1

        # Dynamic Workflow Live Region Calculation
        workflow_rows = self._render_live_workflow_lines(main_w - 4) if (self._processing or self.active_steps) else []
        live_height = min(len(workflow_rows), 8) if self.workflow_expanded else (1 if workflow_rows else 0)

        input_row = h - 2
        footer_row = h
        live_row = input_row - live_height - 1
        transcript_last = live_row - 1
        transcript_top = chrome_bottom + 1

        if transcript_last < transcript_top:
            transcript_last = transcript_top

        return {
            "w": w,
            "h": h,
            "header_rows": header_rows,
            "chrome_bottom": chrome_bottom,
            "transcript_top": transcript_top,
            "transcript_last": transcript_last,
            "live_row": live_row,
            "live_height": live_height,
            "input_row": input_row,
            "footer_row": footer_row,
            "main_w": main_w,
        }

    def _draw_chrome(self, lay: dict) -> None:
        w = lay["main_w"]
        border_dim = _fg(*T.BORDER_SUBTLE)

        # Subtle top header line
        self._move(lay["chrome_bottom"], 1)
        self._write(f"{border_dim}{'─' * w}{T.RESET}")

        # Subtle prompt separator line
        prompt_sep = lay["input_row"] - 1
        if prompt_sep > lay["chrome_bottom"]:
            self._move(prompt_sep, 1)
            self._write(f"{border_dim}{'─' * w}{T.RESET}")

    def _draw_header(self, lay: dict, state: str = "ready") -> None:
        w = lay["main_w"]
        model = self.engine.llm_engine.model if (self.engine and self.engine.llm_engine) else "offline"

        try:
            cwd = os.path.abspath(os.getcwd())
            home = os.path.expanduser("~")
            if cwd == home:
                cwd = "~"
            elif cwd.startswith(home):
                cwd = "~" + cwd[len(home):]
        except Exception:
            cwd = "~"

        if state == "thinking":
            status_badge = f"{_fg(*T.ACCENT)}◐ Thinking{T.RESET}"
        elif state == "error":
            status_badge = f"{_fg(*T.ERROR)}● Error{T.RESET}"
        else:
            status_badge = f"{_fg(*T.SUCCESS)}● Ready{T.RESET}"

        if self.compact:
            left = f" {_fg(*T.ACCENT)}{T.BOLD}DELTA{T.RESET} {_fg(*T.TEXT_DIM)}·{T.RESET} {_fg(*T.TEXT_MUTED)}{cwd[:24]}{T.RESET}"
            right = f"{_fg(*T.TEXT_MUTED)}{model}{T.RESET} {_fg(*T.TEXT_DIM)}·{T.RESET} {status_badge} "
            pad = max(w - visual_width(left) - visual_width(right), 1)
            line = left + (" " * pad) + right
            self._move(1, 1)
            self._write(wrap_terminal_text(line, w)[0])
        else:
            brand = f" {_fg(*T.ACCENT)}{T.BOLD}DELTA{T.RESET}  {_fg(*T.TEXT_DIM)}AI Developer Agent{T.RESET}"
            meta_right = f"{_fg(*T.TEXT_MUTED)}{model}{T.RESET}  {_fg(*T.TEXT_DIM)}·{T.RESET}  {status_badge} "
            gap1 = max(w - visual_width(brand) - visual_width(meta_right), 1)
            row1 = brand + (" " * gap1) + meta_right

            path_line = f" {_fg(*T.TEXT_DIM)}↳{T.RESET} {_fg(*T.TEXT_MUTED)}{cwd[:max(w - 36, 10)]}{T.RESET}"
            help_hint = f"{_fg(*T.TEXT_DIM)}'>' workflow · '?' help{T.RESET} "
            gap2 = max(w - visual_width(path_line) - visual_width(help_hint), 1)
            row2 = path_line + (" " * gap2) + help_hint

            self._move(1, 1)
            self._write(wrap_terminal_text(row1, w)[0])
            self._move(2, 1)
            self._write(wrap_terminal_text(row2, w)[0])

    def _render_live_workflow_lines(self, width: int) -> List[str]:
        """Render shared live workflow steps with vertical tree and wrapping."""
        lines_out: List[str] = []
        is_running = self._processing
        status_label = self.active_status_text or "Working"
        toggle_glyph = "<" if self.workflow_expanded else ">"

        # Compact Header Line: ◐ Thinking... >
        status_color = _fg(*T.ACCENT) if is_running else _fg(*T.SUCCESS)
        spin_char = "◐" if is_running else "✓"
        header = f" {status_color}{spin_char}{T.RESET} {_fg(*T.TEXT)}{status_label}{T.RESET} {_fg(*T.TEXT_DIM)}{toggle_glyph}{T.RESET}"
        lines_out.append(header)

        if not self.workflow_expanded or not self.active_steps:
            return lines_out

        # Expanded Tree Hierarchy
        steps = list(self.active_steps.values())
        action_steps = [s for s in steps if s.get("kind") != "root"]
        if not action_steps:
            lines_out.append(f"   {_fg(*T.BORDER_SUBTLE)}└── {_fg(*T.TEXT_DIM)}No steps recorded yet{T.RESET}")
            return lines_out

        # If multiple branch steps exist, render styled flow
        for idx, step in enumerate(action_steps):
            is_last = (idx == len(action_steps) - 1)
            tree_char = "└── " if is_last else "├── "
            step_status = step.get("status", "running")
            step_running = (step_status == "running")
            s_icon = "→" if step_running else ("✗" if step_status == "failed" else "✓")
            s_color = _fg(*T.ACCENT) if step_running else (_fg(*T.ERROR) if step_status == "failed" else _fg(*T.SUCCESS))

            # Rich label
            label = step.get("label") or step.get("id", "")
            if step.get("command"):
                label = f"Run: {step['command']}"
            elif step.get("file_path"):
                fname = os.path.basename(step["file_path"])
                label = f"{step.get('tool_name', 'File')}: {fname}"

            dur = step.get("duration_ms")
            dur_str = f" · {dur/1000:.1f}s" if dur and dur >= 1000 else (f" · {int(dur)}ms" if dur else "")

            lead = f"   {_fg(*T.BORDER_SUBTLE)}{tree_char}{T.RESET}{s_color}{s_icon}{T.RESET} "
            avail = max(width - visual_width(lead) - visual_width(dur_str) - 2, 10)
            wrapped = wrap_terminal_text(label, avail, indent="", continuation_prefix="       ")
            if wrapped:
                first_line = f"{lead}{_fg(*T.TEXT)}{wrapped[0]}{T.RESET}{_fg(*T.TEXT_DIM)}{dur_str}{T.RESET}"
                lines_out.append(first_line)
                for cont in wrapped[1:]:
                    lines_out.append(f"       {_fg(*T.TEXT_MUTED)}{cont}{T.RESET}")

        return lines_out

    def _draw_input_row(self, lay: dict, cursor: bool = True) -> None:
        w = lay["main_w"]
        row = lay["input_row"]

        self._move(row, 1)
        self._clear_line()

        prefix = f" {_fg(*T.ACCENT)}{T.BOLD}>{T.RESET} "
        prefix_len = visual_width(prefix)
        avail = max(w - prefix_len - 2, 5)

        text = self.input_text
        start = 0
        total = visual_width(text)
        if total > avail:
            start = len(text)
            acc = 0
            while start > 0:
                ch = text[start - 1]
                cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
                if acc + cw > avail:
                    break
                acc += cw
                start -= 1

        vis = text[start:]
        pos_rel = visual_width(vis[: self.input_pos - start])
        tail = visual_width(vis) - pos_rel
        cut = max(avail - pos_rel - 1, 0)
        if tail > cut:
            vis = vis[: cut + len(vis) - tail]

        if not text and not self._processing:
            content = f"{_fg(*T.TEXT_DIM)}Ask Delta anything...{T.RESET}"
        else:
            content = f"{_fg(*T.TEXT)}{vis}{T.RESET}"

        cursor_glyph = f"{_fg(*T.ACCENT)}▋{T.RESET}" if cursor else " "
        line_out = f"{prefix}{content}{cursor_glyph if text or self._processing else ''}"
        self._write(line_out)

    def _draw_live_workflow(self, lay: dict) -> None:
        """Draw active workflow region without horizontal overflow."""
        if not lay["live_height"]:
            return
        lines = self._render_live_workflow_lines(lay["main_w"] - 4)
        for i in range(lay["live_height"]):
            self._move(lay["live_row"] + i, 1)
            self._clear_line()
            if i < len(lines):
                self._write(lines[i])

    def _repaint_live_only(self) -> None:
        """In-place update of live workflow without full screen flicker."""
        lay = self._layout()
        with self._draw_lock:
            self._draw_live_workflow(lay)

    def _render_markdown(self, text: str, width: int) -> List[str]:
        out: List[str] = []
        in_fence = False
        fence_lines: List[str] = []
        fence_lang = ""

        for raw in text.split("\n"):
            stripped = raw.strip()
            if not stripped and not in_fence:
                out.append("")
                continue

            if stripped.startswith("```"):
                if in_fence:
                    in_fence = False
                    lang_tag = f" {_fg(*T.TEXT_DIM)}{fence_lang}{T.RESET}" if fence_lang else ""
                    out.append(f"  {_fg(*T.BORDER_SUBTLE)}┌──{lang_tag}{'─' * max(width - 6 - len(fence_lang), 2)}┐{T.RESET}")
                    for fl in fence_lines:
                        w_code = wrap_terminal_text(fl, width - 8, indent="", continuation_prefix="")
                        for cln in w_code:
                            out.append(f"  {_fg(*T.BORDER_SUBTLE)}│{T.RESET} {_fg(*T.CODE)}{cln}{T.RESET}")
                    out.append(f"  {_fg(*T.BORDER_SUBTLE)}└──{'─' * max(width - 6, 2)}┘{T.RESET}")
                    fence_lines = []
                    fence_lang = ""
                else:
                    in_fence = True
                    fence_lang = stripped[3:].strip()
                continue

            if in_fence:
                fence_lines.append(raw)
                continue

            # Headings & Lists wrapped with indentation
            if stripped.startswith("### "):
                out.extend(wrap_terminal_text(f"{_fg(*T.ACCENT)}{T.BOLD}{stripped[4:]}{T.RESET}", width - 4, indent="  ", continuation_prefix="  "))
            elif stripped.startswith("## "):
                out.append("")
                out.extend(wrap_terminal_text(f"{_fg(*T.TEXT)}{T.BOLD}{stripped[3:]}{T.RESET}", width - 4, indent="  ", continuation_prefix="  "))
            elif stripped.startswith("# "):
                out.append("")
                out.extend(wrap_terminal_text(f"{_fg(*T.ACCENT)}{T.BOLD}{stripped[2:]}{T.RESET}", width - 4, indent="  ", continuation_prefix="  "))
            elif stripped.startswith("> "):
                out.extend(wrap_terminal_text(f"{_fg(*T.BORDER_SUBTLE)}│{T.RESET} {_fg(*T.TEXT_MUTED)}{T.ITALIC}{stripped[2:]}{T.RESET}", width - 4, indent="  ", continuation_prefix="  │ "))
            elif re.match(r"^\s*[-*•]\s+", stripped):
                body = re.sub(r"^\s*[-*•]\s+", "", stripped)
                out.extend(wrap_terminal_text(body, width - 6, indent=f"  {_fg(*T.ACCENT)}•{T.RESET} ", continuation_prefix="    "))
            elif re.match(r"^\s*\d+[.)]\s+", stripped):
                m = re.match(r"^\s*(\d+[.)])\s+", stripped)
                num = m.group(1) if m else "1."
                body = stripped[m.end():] if m else stripped
                out.extend(wrap_terminal_text(body, width - 8, indent=f"  {_fg(*T.TEXT_MUTED)}{num}{T.RESET} ", continuation_prefix="     "))
            else:
                out.extend(wrap_terminal_text(stripped, width - 4, indent="  ", continuation_prefix="  "))

        return out

    def _render_message(self, msg: dict, width: int) -> List[str]:
        kind = msg.get("kind", "text")
        out: List[str] = []

        if kind == "user":
            out.append("")
            out.extend(wrap_terminal_text(msg['text'], width - 4, indent=f" {_fg(*T.ACCENT)}{T.BOLD}>{T.RESET} {_fg(*T.TEXT)}{T.BOLD}", continuation_prefix="   "))
            out.append("")

        elif kind == "ai":
            out.append(f" {_fg(*T.ACCENT)}{T.BOLD}Delta{T.RESET}")
            out.extend(self._render_markdown(msg["text"], width))
            out.append("")

        elif kind == "thought":
            out.extend(wrap_terminal_text(msg['text'], width - 6, indent=f"  {_fg(*T.TEXT_DIM)}◐ {T.ITALIC}", continuation_prefix="    "))

        elif kind == "agent":
            out.extend(wrap_terminal_text(msg['text'], width - 6, indent=f"  {_fg(*T.ACCENT)}→{T.RESET} {_fg(*T.TEXT_MUTED)}", continuation_prefix="    "))

        elif kind == "tool":
            name = msg.get("bullet", "Tool")
            call = msg.get("call", "")
            result = msg.get("result", "")
            head = f"{name} {call} → {result}" if result else f"{name} {call}"
            out.extend(wrap_terminal_text(head, width - 6, indent=f"  {_fg(*T.TOOL)}├─{T.RESET} {_fg(*T.TEXT)}", continuation_prefix="  │  "))

        elif kind == "success":
            out.extend(wrap_terminal_text(msg['text'], width - 6, indent=f"  {_fg(*T.SUCCESS)}✓{T.RESET} {_fg(*T.TEXT)}", continuation_prefix="    "))

        elif kind == "notice":
            out.extend(wrap_terminal_text(msg['text'], width - 6, indent=f"  {_fg(*T.TEXT_DIM)}· ", continuation_prefix="    "))

        elif kind == "text":
            out.extend(wrap_terminal_text(msg["text"], width - 4, indent="  ", continuation_prefix="  "))

        return out

    def _repaint(self, state: str = "ready", cursor: bool = True) -> None:
        lay = self._layout()
        w = lay["main_w"]

        with self._draw_lock:
            self._clear_screen()
            self._draw_chrome(lay)
            self._draw_header(lay, state=state)

            cw = w - 2
            rows: List[str] = []
            for msg in self.messages:
                rows.extend(self._render_message(msg, cw))

            avail = lay["transcript_last"] - lay["transcript_top"] + 1
            total = len(rows)
            start = max(0, total - avail - self.scroll)
            row = lay["transcript_top"]

            for i in range(avail):
                self._move(row, 1)
                if start + i < total:
                    text_out = rows[start + i]
                    self._write(text_out)
                    pad = cw - visual_width(text_out)
                    if pad > 0:
                        self._write(" " * pad)
                else:
                    self._write(" " * cw)
                row += 1

            self._draw_live_workflow(lay)
            self._draw_input_row(lay, cursor=cursor)

    def _repaint_input_only(self, cursor: bool = True) -> None:
        lay = self._layout()
        with self._draw_lock:
            self._draw_input_row(lay, cursor=cursor)

    def _add_welcome(self, welcome: str) -> None:
        model = self.engine.llm_engine.model if (self.engine and self.engine.llm_engine) else "offline"
        self.messages.append({
            "kind": "notice",
            "text": f"Delta AI Agent initialized · Model: {model} · Ready for instructions.",
        })

    def _toggle_workflow_expand(self) -> None:
        self.workflow_expanded = not self.workflow_expanded
        self._repaint()

    def _toggle_node_detail(self) -> None:
        if not self.active_steps:
            self._notice("No active workflow node details available.")
            return
        last_step = list(self.active_steps.values())[-1]
        lines = [
            f"Node: {last_step.get('label', last_step.get('id', ''))}",
            f"Tool: {last_step.get('tool_name', 'None')}",
            f"Status: {last_step.get('status', 'running')}",
            f"Target: {last_step.get('file_path') or last_step.get('command') or 'None'}",
            f"Duration: {last_step.get('duration_ms', 0)}ms",
            f"Preview: {last_step.get('output_preview', 'None')}"
        ]
        for ln in lines:
            self.messages.append({"kind": "notice", "text": ln})
        self._repaint()

    def _toggle_help(self) -> None:
        if self._help_idx is not None:
            del self.messages[self._help_idx:]
            self._help_idx = None
        else:
            lines = [
                {"kind": "notice", "text": "Keyboard Navigation & Shortcuts"},
                {"kind": "text", "text": "> / <         Toggle workflow tree expand/collapse"},
                {"kind": "text", "text": "↑ / ↓         Browse input history"},
                {"kind": "text", "text": "PgUp / PgDn   Scroll conversation stream"},
                {"kind": "text", "text": "Ctrl+C        Cancel current query or copy transcript"},
                {"kind": "text", "text": "/clear        Clear conversation history"},
                {"kind": "text", "text": "exit          Exit Delta session"},
            ]
            self._help_idx = len(self.messages)
            self.messages.extend(lines)
        self.scroll = 0
        self._repaint()

    def _notice(self, text: str, color: str = "muted") -> None:
        self.messages.append({"kind": "notice", "text": text})
        self.scroll = 0
        self._repaint()

    def _transcript_text(self) -> str:
        w, _ = self._size()
        cw = max(w - 4, 20)
        lines: List[str] = []
        for msg in self.messages:
            lines.extend(self._render_message(msg, cw))
        plain = [plain_text(ln).rstrip() for ln in lines]
        header = f"Delta Session Transcript — {datetime.now():%Y-%m-%d %H:%M:%S}"
        return header + "\n" + "\n".join(plain)

    @staticmethod
    def _copy_win32(text: str) -> bool:
        if os.name != "nt":
            return False
        try:
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
            user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
            user32.SetClipboardData.restype = ctypes.c_void_p

            if not user32.OpenClipboard(None):
                return False
            try:
                user32.EmptyClipboard()
                data = (text + "\x00").encode("utf-16-le")
                h = kernel32.GlobalAlloc(0x0042, len(data))
                if not h:
                    return False
                try:
                    ptr = kernel32.GlobalLock(h)
                    if not ptr:
                        return False
                    ctypes.memmove(ptr, data, len(data))
                    kernel32.GlobalUnlock(h)
                    ok = bool(user32.SetClipboardData(13, h))
                    if ok:
                        h = None
                    return ok
                finally:
                    if h:
                        kernel32.GlobalFree(h)
            finally:
                user32.CloseClipboard()
        except Exception:
            return False

    def _copy_transcript(self) -> Tuple[bool, str, str]:
        text = self._transcript_text()
        if self._copy_win32(text):
            return True, "clipboard", ""
        try:
            path = os.path.join(self.engine.config.data_dir, "delta_copy.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            return True, "file", path
        except Exception:
            return False, "", ""

    def _read_key(self) -> str:
        import msvcrt
        if self._hin is not None and self._kernel32 is not None:
            try:
                self._kernel32.WaitForSingleObject(self._hin, 250)
                rec = _INPUT_RECORD()
                n = ctypes.c_uint32()
                if self._kernel32.ReadConsoleInputW(
                    self._hin, ctypes.byref(rec), 1, ctypes.byref(n)
                ) and n.value == 1:
                    if rec.EventType == 1:
                        if rec.Event.key.bKeyDown:
                            u = rec.Event.key.uChar
                            if u != "\x00":
                                return u
                            vk = rec.Event.key.wVirtualKeyCode
                            if vk == 0x0D:
                                return "\r"
                            if vk == 0x1B:
                                return "\x1b"
                            if vk == 0x03:
                                return "\x03"
                            if vk == 0x08:
                                return "\b"
                            if vk in _VK_SPECIAL:
                                return "\xe0" + _VK_SPECIAL[vk]
                            return ""
                    elif rec.EventType == 2:
                        if rec.Event.mouse.dwEventFlags == 4:
                            delta = ctypes.c_int16(
                                rec.Event.mouse.dwButtonState >> 16
                            ).value
                            return "\x00U" if delta > 0 else "\x00D"
                    elif rec.EventType == 5:
                        return "\x00R"

                if self._size_changed():
                    return "\x00R"
                return ""
            except Exception:
                self._hin = None

        return msvcrt.getwch()

    def _read_line_raw(self) -> Tuple[str, Optional[str]]:
        self.input_text = ""
        self.input_pos = 0

        while True:
            if self._size_changed():
                self._repaint(cursor=True)
            self._repaint_input_only(cursor=True)

            ch = self._read_key()
            if not ch:
                continue

            if ch[:1] in ("\x00", "\xe0"):
                k2 = ch[1] if len(ch) > 1 else self._read_key()
                if k2 == "K":
                    self.input_pos = max(0, self.input_pos - 1)
                elif k2 == "M":
                    self.input_pos = min(len(self.input_text), self.input_pos + 1)
                elif k2 == "H":
                    if self._hist_idx > 0:
                        self._hist_idx -= 1
                        self.input_text = self._history[self._hist_idx]
                        self.input_pos = len(self.input_text)
                elif k2 == "P":
                    if self._hist_idx < len(self._history) - 1:
                        self._hist_idx += 1
                        self.input_text = self._history[self._hist_idx]
                        self.input_pos = len(self.input_text)
                    else:
                        self._hist_idx = len(self._history)
                        self.input_text, self.input_pos = "", 0
                elif k2 == "G":
                    self.input_pos = 0
                elif k2 == "O":
                    self.input_pos = len(self.input_text)
                elif k2 == "S":
                    if self.input_pos < len(self.input_text):
                        self.input_text = (
                            self.input_text[: self.input_pos]
                            + self.input_text[self.input_pos + 1:]
                        )
                elif k2 == "I":
                    self.scroll += 6
                    self._repaint(cursor=False)
                elif k2 == "Q":
                    self.scroll = max(0, self.scroll - 6)
                    self._repaint(cursor=False)
                elif k2 == "R":
                    self._repaint(cursor=True)
                elif k2 == "U":
                    self.scroll += 3
                    self._repaint(cursor=False)
                elif k2 == "D":
                    self.scroll = max(0, self.scroll - 3)
                    self._repaint(cursor=False)
                continue

            if ch == "\r":
                text, self.input_text, self.input_pos = self.input_text, "", 0
                return ("submit", text)

            if ch == "\x03":
                if self._processing and hasattr(self.engine, "_stop_event") and self.engine._stop_event:
                    self.engine._stop_event.set()
                    self._notice("Stop requested (Ctrl+C)...")
                    return ("", None)
                if self.input_text:
                    self.input_text, self.input_pos = "", 0
                    return ("cancel", None)
                return ("copy", None)

            if ch == "\x1b":
                self.input_text, self.input_pos = "", 0
                continue

            if ch == "\b":
                if self.input_pos > 0:
                    self.input_text = (
                        self.input_text[: self.input_pos - 1]
                        + self.input_text[self.input_pos:]
                    )
                    self.input_pos -= 1
                continue

            if ch == ">" and not self.input_text:
                self._toggle_workflow_expand()
                continue

            if ch == "<" and not self.input_text:
                self._toggle_workflow_expand()
                continue

            if ch == "?" and not self.input_text:
                return ("help", None)

            if ch.isprintable():
                self.input_text = (
                    self.input_text[: self.input_pos]
                    + ch
                    + self.input_text[self.input_pos:]
                )
                self.input_pos += 1

    def _read_line(self) -> Tuple[str, Optional[str]]:
        if os.name == "nt":
            return self._read_line_raw()

        self.input_text = ""
        if self._size_changed():
            self._repaint(cursor=True)

        sys.stdout.write("\033[?25h\033[1 q")
        sys.stdout.flush()
        try:
            try:
                text = input()
            except EOFError:
                return ("exit", None)
            except KeyboardInterrupt:
                if self.input_text:
                    self.input_text, self.input_pos = "", 0
                    return ("cancel", None)
                return ("copy", None)
        finally:
            sys.stdout.write("\033[0 q")
            sys.stdout.flush()

        return ("submit", text)

    def _cursor_blinker(self, stop: threading.Event) -> None:
        visible = True
        while not stop.is_set():
            if not self._processing:
                self._repaint_input_only(cursor=visible)
            visible = not visible
            time.sleep(0.5)

    def _process_captured(self, fn) -> Tuple[str, Any]:
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            ret = fn()
        finally:
            sys.stdout = old

        text = plain_text(buf.getvalue())
        lines: List[str] = []
        for ln in text.split("\n"):
            ln = ln.split("\r")[-1].rstrip()
            lines.append(ln)

        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()

        if len(lines) > 150:
            lines = lines[:150] + [f"... {len(lines) - 150} more line(s) omitted"]

        return "\n".join(lines) + "\n", ret

    def _submit(self, text: str) -> None:
        self._history.append(text)
        self._hist_idx = len(self._history)
        self.scroll = 0
        self.input_text, self.input_pos = "", 0

        clean = text.strip().lower()
        if clean in ("/clear", "/cls", "/clean", "clear", "cls"):
            self.messages = []
            self.scroll = 0
            self.active_steps.clear()
            if self.engine.llm_engine:
                self.engine.llm_engine.reset_conversation()
            self.messages.append({"kind": "notice", "text": "Conversation cleared."})
            self._repaint()
            return

        self.messages.append({"kind": "user", "text": text})

        llm = self.engine.llm_engine
        start = time.monotonic()
        self._processing = True
        self.engine._stop_event = threading.Event()

        captured = ""
        result = None

        try:
            captured, result = self._process_captured(
                lambda: self.engine._process_input(text)
            )
        except KeyboardInterrupt:
            self.messages.append({"kind": "notice", "text": "[Cancelled]"})
        except Exception as e:
            self.messages.append({"kind": "notice", "text": f"Error: {e}"})
            if self.engine.config.debug:
                import traceback
                traceback.print_exc()
        finally:
            self.engine._stop_event = None

        self._processing = False

        if isinstance(result, dict):
            err = result.get("error") or ""
            response = result.get("response") or ""
            if err:
                self.messages.append({"kind": "notice", "text": err})
            if response:
                self.messages.append({"kind": "ai", "text": response})
            elif captured.strip():
                for ln in captured.split("\n"):
                    if ln.strip():
                        self.messages.append({"kind": "text", "text": ln})
        else:
            if captured.strip():
                for ln in captured.split("\n"):
                    if ln.strip():
                        self.messages.append({"kind": "text", "text": ln})
            else:
                self.messages.append({"kind": "notice", "text": "Done."})

        if len(self.messages) > 500:
            self.messages = self.messages[-500:]

        self._repaint()

    def run(self, welcome: str = "") -> None:
        self.engine.running = True
        self.messages = []
        self.scroll = 0
        self._history = []
        self._help_idx = None

        self._add_welcome(welcome)

        if os.name == "nt":
            self._hide_real_cursor()

        self._repaint()

        blinker_stop = threading.Event()
        blinker: Optional[threading.Thread] = None

        if os.name == "nt":
            blinker = threading.Thread(
                target=self._cursor_blinker, args=(blinker_stop,), daemon=True
            )
            blinker.start()

        try:
            while self.engine.running:
                action, payload = self._read_line()

                if action == "submit":
                    if not (payload or "").strip():
                        self._repaint()
                        continue
                    self._submit(payload or "")

                elif action == "cancel":
                    self._notice("[Type 'exit' to quit]")

                elif action == "copy":
                    ok, how, path = self._copy_transcript()
                    if ok:
                        if how == "file":
                            self._notice(f"Transcript saved to {path}")
                        else:
                            self._notice("✓ Transcript copied to clipboard", color="success")
                    else:
                        self._notice("Failed to copy transcript.")

                elif action == "help":
                    self._toggle_help()

                elif action == "exit":
                    self.engine.running = False
                    break
        finally:
            blinker_stop.set()
            if blinker:
                blinker.join(timeout=1.0)
            if hasattr(self, "_unsubscribe") and callable(self._unsubscribe):
                self._unsubscribe()

        self._show_real_cursor()
        self._clear_screen()
        print(f"\n {_fg(*T.ACCENT)}DELTA{T.RESET} {_fg(*T.TEXT_DIM)}session ended.{T.RESET}\n")

    def show_login(self, config, max_attempts: int = 3) -> bool:
        import getpass
        self._clear_screen()
        w, h = self._size()
        box_w = min(50, w - 4)
        left = max(1, (w - box_w) // 2)
        top = max(2, h // 2 - 4)

        border = _fg(*T.BORDER_SUBTLE)
        accent = _fg(*T.ACCENT)
        txt = _fg(*T.TEXT)
        muted = _fg(*T.TEXT_MUTED)

        def edge(row, start_char, end_char) -> None:
            self._move(top + row, left)
            self._write(f"{border}{start_char}{'─' * (box_w - 2)}{end_char}{T.RESET}")

        def line(row, content: str) -> None:
            self._move(top + row, left)
            wrapped = wrap_terminal_text(content, box_w - 4)[0]
            self._write(f"{border}│{T.RESET} {wrapped}")
            self._move(top + row, left + box_w - 1)
            self._write(f"{border}│{T.RESET}")

        edge(0, "┌", "┐")
        line(1, f"{accent}{T.BOLD}DELTA{T.RESET} {_fg(*T.TEXT_DIM)}Authentication{T.RESET}")
        line(2, f"{muted}Please enter your credentials{T.RESET}")
        line(3, "")
        line(4, f"{txt}Username:{T.RESET}")
        line(5, f"{txt}Password:{T.RESET}")
        line(6, "")
        edge(7, "└", "┘")

        input_row = top + 4
        for attempt in range(max_attempts):
            self._move(input_row, left + 12)
            self._clear_line()
            self._write(f"{txt}> {T.RESET}")
            username = input()

            self._move(input_row + 1, left + 12)
            self._clear_line()
            self._write(f"{txt}> {T.RESET}")
            password = getpass.getpass("")

            if verify_credentials(config, username.strip(), password):
                self._move(input_row + 2, left + 2)
                self._write(f"{_fg(*T.SUCCESS)}✓ Authenticated.{T.RESET}")
                time.sleep(0.5)
                return True

            remaining = max_attempts - attempt - 1
            msg = f"Invalid credentials. ({remaining} left)" if remaining else "Access denied."
            self._move(input_row + 2, left + 2)
            self._clear_line()
            self._write(f"{_fg(*T.ERROR)}✗ {msg}{T.RESET}")

        return False

def Object_merge(d1: dict, d2: dict) -> dict:
    res = dict(d1)
    res.update(d2)
    return res

def run_tui(engine) -> bool:
    try:
        tui = DeltaTUI(engine)
        tui.run()
        return True
    except Exception as e:
        print(f"Error starting TUI: {e}")
        return False
