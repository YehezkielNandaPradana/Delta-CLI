# Refactor: tui formatting
# delta/core/tui.py

"""

Delta CLI — full-screen terminal user interface.

Design language (Hostile AI / Rogue Agent theme):

  • Near-black void background (#050505), blood-red borders that read like a warning light.

  • Animated skull glyph with glitch & breathing color effects.

  • OpenCode-style input box at the bottom with contextual hints.

  • HUD reads like a threat console: ARMED / HUNTING / BREACH instead of friendly status text.

  • Transcripts in bone-white on black, tool calls in arterial red, agent lines in venomous

    orange — nothing here is trying to be comforting.

  • Windows raw-keyboard input with a blinking blood-red block cursor.

  • Hostile sidebar on wide/desktop layouts containing advanced threat diagnostics.

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

import math

import random

from datetime import datetime

from typing import Any, List, Optional, Tuple

from delta.core.auth import verify_credentials

# True when the terminal accepted ANSI/VT color sequences.

_VT_OK = False

def _enable_vt() -> None:

    """Enable ANSI/VT processing and UTF-8 output where possible."""

    global _VT_OK

    try:

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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

        T.RESET = T.BOLD = T.DIM = T.ITALIC = ""

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

# Palette (Delta Web IDE Theme — Emerald / Dark Slate / Sky Truecolor)

# ---------------------------------------------------------------------------

class T:

    RESET = "\033[0m"

    BOLD = "\033[1m"

    DIM = "\033[2m"

    ITALIC = "\033[3m"

    BG = (15, 23, 42)             # #0F172A — Slate Canvas

    BORDER = (16, 185, 129)       # Primary Emerald #10B981

    BORDER_DIM = (51, 65, 85)     # Subtle Slate #374151

    TEXT = (241, 245, 249)        # Slate Light Text

    MUTED = (148, 163, 184)       # Muted Slate

    FAINT = (71, 85, 105)         # Faint Slate

    USER_BORDER = (16, 185, 129)  # Emerald Border

    RED = (239, 68, 68)           # Danger Red #EF4444

    YELLOW = (245, 158, 11)       # Amber Warning

    GREEN = (16, 185, 129)        # Emerald Primary

    SUCCESS = (209, 250, 229)     # Emerald Fixed

    CYAN = (14, 165, 233)         # Sky Blue

    ORANGE = (139, 92, 246)       # Secondary Violet #8B5CF6

    TOOL = (14, 165, 233)         # Sky Blue Tool Accent

    THINK = (14, 165, 233)        # Sky Blue Thinking Indicator

    AI_BORDER = (16, 185, 129)    # Emerald AI Border

    CODE = (125, 211, 252)       # Light Sky Code

    LOGO = [

        (16, 185, 129), (14, 165, 233), (139, 92, 246),

    ]

# Web IDE Style Banner Rows

SKULL_ROWS = [

    " ⚡ DELTA IDE WORKSPACE ",

    " ────────────────────── ",

]

ANSI_STRIP = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07")

class DeltaTUI:

    """Full-screen "Delta CLI" interface: hostile-AI blood-red window, skull glyph,

    scrollable transcript, threat sidebar, and bottom status bar."""

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

    @staticmethod

    def _vwidth(s: str) -> int:

        return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)

    @staticmethod

    def _plain(text: str) -> str:

        return ANSI_STRIP.sub("", text)

    @staticmethod

    def _clip(text: str, width: int) -> str:

        if width < 4:

            return text[:max(width, 0)]

        plain = DeltaTUI._plain(text)

        if DeltaTUI._vwidth(plain) <= width:

            return text

        return text[: width - 1] + "…"

    @staticmethod

    def _wrap(text: str, width: int) -> List[str]:

        width = max(10, width)

        out: List[str] = []

        for para in text.split("\n"):

            para = para.rstrip()

            if not para:

                out.append("")

                continue

            out.extend(textwrap.wrap(

                para, width=width, break_long_words=True,

                break_on_hyphens=False, replace_whitespace=False,

            ) or [""])

        return out

    def _write(self, text: str = "") -> None:

        try:

            sys.__stdout__.write(text)

        except UnicodeEncodeError:

            safe = text

            for orig, repl in {

                "Δ": "D", "◐": "o", "●": "O", "█": "#", "─": "-",

                "╭": "+", "╮": "+", "╰": "+", "╯": "+", "│": "|",

                "├": "+", "┤": "+", "↑": "^", "↓": "v", "→": "->",

                "·": "*", "✔": "v", "✘": "x", "⚠": "!", "ℹ": "i",

                "▔": "-", "•": "*", "…": "...", "⠋": "/", "⠙": "-",

                "⠹": "-", "⠸": "=", "⠼": "-", "⠴": "(", "⠦": "(",

                "⠧": ")", "⠇": ")", "⠏": "/", "▲": "^", "▙": "#", "▀": "-",

                "░": ".", "⣀": "#", "⢀": "#", "⣤": "#", "⣾": "#", "⣷": "#",

                "⣿": "#", "⡿": "#", "⠻": "#", "⢿": "#", "⣦": "#", "⣼": "#",

                "⠉": "#", "⠛": "#", "⣄": "#", "⣴": "#", "⠟": "#", "⡇": "#",

                "⠁": "#", "⠈": "#",

            }.items():

                safe = safe.replace(orig, repl)

            sys.__stdout__.write(safe.encode("ascii", "replace").decode("ascii"))

        sys.__stdout__.flush()

    def _move(self, row: int, col: int = 1) -> None:

        if self._native:

            self._kernel32.SetConsoleCursorPosition(

                self._hout, _COORD(max(0, int(col) - 1), max(0, int(row) - 1))

            )

        else:

            sys.__stdout__.write(f"\033[{int(row)};{int(col)}H")

    def _clear_line(self) -> None:

        if self._native:

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

            sys.__stdout__.write("\033[K")

    def _clear_screen(self) -> None:

        if self._native:

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

            sys.__stdout__.write("\033[2J\033[H")

        sys.__stdout__.flush()

    def _hide_real_cursor(self) -> None:

        if self._native:

            info = _CONSOLE_CURSOR_INFO(25, False)

            self._kernel32.SetConsoleCursorInfo(self._hout, ctypes.byref(info))

        else:

            sys.__stdout__.write("\033[?25l")

        sys.__stdout__.flush()

    def _show_real_cursor(self) -> None:

        if self._native:

            info = _CONSOLE_CURSOR_INFO(25, True)

            self._kernel32.SetConsoleCursorInfo(self._hout, ctypes.byref(info))

        else:

            sys.__stdout__.write("\033[?25h\033[0 q")

        sys.__stdout__.flush()

    @property

    def compact(self) -> bool:

        w, h = self._size()

        return h < 24 or w < 62

    def _layout(self) -> dict:

        w, h = self._size()

        sidebar_w = 0

        if w >= 100 and not self.compact:

            sidebar_w = 34

        main_w = w - sidebar_w - 1 if sidebar_w else w

        if self.compact:

            header_rows = 1

            chrome_bottom = 2

        else:

            header_rows = len(SKULL_ROWS)

            chrome_bottom = 2 + header_rows

        BOTTOM_ZONE = 6

        input_row = h - BOTTOM_ZONE + 1

        footer_row = h - 1

        transcript_last = input_row - 3

        transcript_top = chrome_bottom + 2

        transcript_top = min(transcript_top, max(transcript_last - 2, 1))

        if transcript_last - transcript_top < 2:

            transcript_last = transcript_top + 2

        return {

            "w": w, "h": h, "header_rows": header_rows,

            "chrome_bottom": chrome_bottom,

            "transcript_top": transcript_top,

            "transcript_last": transcript_last, "input_row": input_row,

            "footer_row": footer_row,

            "main_w": main_w, "sidebar_w": sidebar_w, "sidebar_x": main_w + 2

        }

    def _draw_chrome(self, lay: dict) -> None:

        w = lay["main_w"]

        border = _fg(*T.BORDER)

        dim = _fg(*T.BORDER_DIM)

        if w >= 46:

            try:

                path = "~ " + os.path.basename(os.path.abspath(os.getcwd()))

            except Exception:

                path = "~ delta"

            mid = (

                f"{_fg(*T.RED)}●{T.RESET}  {_fg(*T.YELLOW)}●{T.RESET}  "

                f"{_fg(*T.GREEN)}●{T.RESET}  {_fg(*T.MUTED)}{self._clip(path, 26)}{T.RESET} "

            )

            dash = max(w - self._vwidth(DeltaTUI._plain(mid)) - 3, 0)

            row = f"{border}╭─{mid}{dim}{'─' * dash}{border}╮{T.RESET}"

        else:

            row = f"{border}╭{dim}{'─' * (w - 2)}{border}╮{T.RESET}"

        self._move(1, 1)

        self._write(row)

        self._move(lay["h"], 1)

        self._write(f"{border}╰{dim}{'─' * (w - 2)}{border}╯{T.RESET}")

        chrome_bottom = lay.get("chrome_bottom", lay["transcript_top"] - 1)

        if chrome_bottom < lay["transcript_top"]:

            self._move(chrome_bottom, 1)

            self._write(f"{border}├{dim}{'─' * (w - 2)}{border}┤{T.RESET}")

        divider_row = lay["input_row"] - 2

        if divider_row > chrome_bottom + 1:

            self._move(divider_row, 1)

            self._write(f"{dim}{'─' * w}{T.RESET}")

    def _draw_header(self, lay: dict, glitch: bool = False) -> None:

        w = lay["main_w"]

        chrome_bottom = lay.get("chrome_bottom", 2)

        if self.compact:

            model = self.engine.llm_engine.model if self.engine.llm_engine else "offline"

            line = (

                f"  {_fg(*T.BORDER)}▐{_fg(*T.RED)} DELTA :: HOSTILE {_fg(*T.BORDER)}▌{T.RESET}"

                f"  {_fg(*T.MUTED)}[ {_fg(*T.YELLOW)}{model}{_fg(*T.MUTED)} ]{T.RESET}"

            )

            self._move(2, 1)

            self._write(" " + self._clip(line, w - 3))

            return

        pad = 2

        logo_w = max(len(r) for r in SKULL_ROWS)

        text_x = pad + logo_w + 2

        model = self.engine.llm_engine.model if self.engine.llm_engine else "offline"

        try:

            cwd = os.path.abspath(os.getcwd())

            home = os.path.expanduser("~")

            if cwd == home:

                cwd = "~"

            elif cwd.startswith(home):

                cwd = "~" + cwd[len(home):]

        except Exception:

            cwd = "~"

        titles = [

            f"{T.BOLD}{_fg(*T.BORDER)}⚡ DELTA // SOC CYBER OPS WORKSPACE{T.RESET}",

            f"{_fg(*T.MUTED)}[ {_fg(*T.GREEN)}AGENT{_fg(*T.MUTED)} : {_fg(*T.CYAN)}{model}{_fg(*T.MUTED)} ]{T.RESET}",

            f"{_fg(*T.MUTED)}[ {_fg(*T.GREEN)}TARGET{_fg(*T.MUTED)}: {_fg(*T.CYAN)}{self._clip(cwd, w - text_x - 4)}{_fg(*T.MUTED)} ]{T.RESET}",

        ]

        t = time.monotonic()
        pulse = (math.sin(t * 1.5) + 1) / 2
        r = int(160 + 95 * pulse)
        g = int(10 + 15 * pulse)
        b = int(15 + 15 * pulse)
        skull_color = _fg(r, g, b)

        for i, art in enumerate(SKULL_ROWS):
            line_color = skull_color
            if glitch and not self._processing:
                rand_val = random.random()
                if rand_val > 0.75:
                    line_color = random.choice([
                        _fg(255, 30, 35),   # Neon Red
                        _fg(0, 240, 255),   # Cyber Cyan
                        _fg(255, 0, 180),   # Glitch Magenta
                        _fg(255, 255, 255), # Flash White
                    ])
                if rand_val > 0.85:
                    offset = random.choice([1, 2])
                    art = " " * offset + art

            line = " " * pad + f"{line_color}{art}{T.RESET}" + " " * 2

            row = 2 + i

            if i < len(titles):

                line += titles[i]

            self._move(row, 1)

            self._write(self._clip(line, w - 3))

    def _draw_sidebar(self, lay: dict, state: str = "ready") -> None:

        x = lay["sidebar_x"]

        w = lay["sidebar_w"]

        if not w: return

        top = lay["transcript_top"] - 1

        last = lay["footer_row"]

        border = _fg(*T.BORDER)

        dim = _fg(*T.BORDER_DIM)

        red = _fg(*T.RED)

        muted = _fg(*T.MUTED)

        yellow = _fg(*T.YELLOW)

        text_c = _fg(*T.TEXT)

        self._move(top, x)

        self._write(f"{border}╭{'─' * (w - 2)}╮{T.RESET}")

        self._move(last, x)

        self._write(f"{border}╰{'─' * (w - 2)}╯{T.RESET}")

        for r in range(top + 1, last):

            self._move(r, x)

            self._write(f"{border}│{T.RESET}")

            self._move(r, x + w - 1)

            self._write(f"{border}│{T.RESET}")

        y = top + 1

        self._move(y, x + 1)

        self._write(f" {red}{T.BOLD}▌ THREAT CONSOLE ▐{T.RESET} ")

        y += 2

        msg_count = len(self.messages)

        uptime = int(time.monotonic() % 100000)

        m, s = divmod(uptime, 60)

        h_val, m = divmod(m, 60)

        if state == "thinking":

            state_str = f"{_fg(*T.THINK)}◐ THINKING{T.RESET}"

        elif state == "error":

            state_str = f"{_fg(*T.RED)}● BREACH{T.RESET}"

        else:

            state_str = f"{_fg(*T.RED)}● ARMED{T.RESET}"

        stats = [

            ("STATE", state_str),

            ("SESSION", f"{yellow}{h_val:02d}:{m:02d}:{s:02d}{T.RESET}"),

            ("MESSAGES", f"{text_c}{msg_count}{muted} / 500{T.RESET}"),

            ("TERMINAL", f"{muted}{lay['w']}x{lay['h']}{T.RESET}"),

        ]

        for label, val in stats:

            self._move(y, x + 1)

            self._write(f" {muted}{label:8s}{T.RESET}: {val}")

            y += 1

        y += 1

        self._move(y, x + 1)

        self._write(f" {red}{T.BOLD}-- ACTIVE MODULES --{T.RESET}")

        y += 1

        modules = []

        if self.engine.llm_engine:

            modules.append(f"{text_c}{self.engine.llm_engine.model}{T.RESET}")

        if hasattr(self.engine, 'plugin_manager'):

            pm = self.engine.plugin_manager

            if hasattr(pm, '_plugins') and pm._plugins:

                for pname in list(pm._plugins.keys())[:3]:

                    modules.append(f"{yellow}{pname}{T.RESET}")

        if not modules:

            modules.append(f"{muted}none{T.RESET}")

        for mod in modules[:4]:

            self._move(y, x + 1)

            self._write(f" {muted}▸{T.RESET} {mod}")

            y += 1

        y += 1

        self._move(y, x + 1)

        self._write(f" {red}{T.BOLD}▌ SYSTEM STATUS ▐{T.RESET}")

        y += 1

        mem_pct = min(msg_count / 500 * 100, 100)

        bar_len = w - 8

        filled = int(mem_pct / 100 * bar_len)

        bar_color = _fg(*T.GREEN) if mem_pct < 50 else (_fg(*T.YELLOW) if mem_pct < 80 else _fg(*T.RED))

        bar = f"{bar_color}{'█' * filled}{'░' * (bar_len - filled)}{T.RESET}"

        self._move(y, x + 2)

        self._write(f"{bar} {yellow}{int(mem_pct)}%{T.RESET}")

        y += 1

        y += 1

        self._move(y, x + 1)

        self._write(f" {muted}» '?' shortcuts{T.RESET}")

        y += 1

        self._move(y, x + 1)

        self._write(f" {muted}» Ctrl+C copy{T.RESET}")

    def _draw_footer(self, lay: dict, state: str = "ready") -> None:

        w = lay["main_w"]

        model = self.engine.llm_engine.model if self.engine.llm_engine else "offline"

        right = f"[ {_fg(*T.RED)}Delta Core{_fg(*T.MUTED)}: {_fg(*T.YELLOW)}{model}{_fg(*T.MUTED)} ]{T.RESET}"

        if state == "thinking":

            dot = f"{_fg(*T.THINK)}◐{T.RESET} {_fg(*T.THINK)}{T.BOLD}THINKING{T.RESET}"

        elif state == "error":

            dot = f"{_fg(*T.RED)}●{T.RESET} {_fg(*T.RED)}{T.BOLD}BREACH{T.RESET}"

        else:

            dot = f"{_fg(*T.RED)}●{T.RESET} {_fg(*T.RED)}{T.BOLD}ARMED{T.RESET}"

        left = f"{_fg(*T.MUTED)}[ {_fg(*T.YELLOW)}?{_fg(*T.MUTED)} shortcuts ]{T.RESET}"

        inner_w = w - 4

        line = dot + "   " + left

        gap = max(inner_w - self._vwidth(DeltaTUI._plain(line)) - self._vwidth(DeltaTUI._plain(right)), 1)

        line += " " * gap + right

        self._move(lay["footer_row"], 2)

        self._write(self._clip(line, inner_w))

    def _input_visible(self, avail: int) -> Tuple[str, int]:

        text = self.input_text

        cur = self.input_pos

        prefix = f"{_fg(*T.RED)}» {T.RESET}"

        max_text_w = max(avail - 2 - self._vwidth(prefix), 2)

        total = self._vwidth(text)

        start = 0

        if total > max_text_w:

            start = len(text)

            acc = 0

            while start > 0:

                ch = text[start - 1]

                cw = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1

                if acc + cw > max_text_w:

                    break

                acc += cw

                start -= 1

        return text, start

    def _draw_input_row(self, lay: dict, cursor: bool = True) -> None:

        w = lay["main_w"]

        inner_w = w - 4

        row1 = lay["input_row"]

        row2 = lay["input_row"] + 1

        row3 = lay["input_row"] + 2

        self._move(row1, 2)

        label = f"{_fg(*T.RED)}PROMPT{_fg(*T.BORDER)}"

        label_w = DeltaTUI._vwidth(DeltaTUI._plain(label))

        self._write(f"{_fg(*T.BORDER)}╭─[ {label}{_fg(*T.BORDER)} ]{'─' * max(inner_w - 5 - label_w, 0)}╮{T.RESET}")

        self._move(row3, 2)

        self._write(f"{_fg(*T.BORDER)}╰{'─' * inner_w}╯{T.RESET}")

        self._move(row2, 2)

        self._write(f"{_fg(*T.BORDER)}│{T.RESET} ")

        prefix = f"{_fg(*T.RED)}» {T.RESET}"

        box_w = inner_w - 4

        text, start = self._input_visible(box_w)

        vis = text[start:]

        pos_rel = self._vwidth(vis[: self.input_pos - start])

        avail = box_w - self._vwidth(prefix)

        tail = self._vwidth(vis) - pos_rel

        cut = max(avail - pos_rel - 2, 0)

        if tail > cut:

            vis = vis[: cut + len(vis) - tail]

        row = f"{_fg(*T.TEXT)}{T.BOLD}{prefix}{T.RESET}{_fg(*T.TEXT)}{vis}{T.RESET}"

        block = f"{_fg(*T.RED)}{T.BOLD}█{T.RESET}"

        if cursor:

            row += block

        pad = box_w - self._vwidth(DeltaTUI._plain(row)) - (0 if not cursor else 1)

        if pad > 0:

            row += " " * pad

        self._write(row)

        self._write(f" {_fg(*T.BORDER)}│{T.RESET}")

    def _style_line(self, text: str) -> str:

        s = text.strip()

        if not s:

            return _fg(*T.MUTED) + "·" + T.RESET

        if s.startswith("✔"):

            return f"{_fg(*T.SUCCESS)}{T.BOLD}┃ {s}{T.RESET}"

        if s.startswith("⚠"):

            return f"{_fg(*T.YELLOW)}{T.BOLD}┃ {s}{T.RESET}"

        if s.startswith("✘"):

            return f"{_fg(*T.RED)}{T.BOLD}┃ {s}{T.RESET}"

        if s.startswith("ℹ"):

            return f"{_fg(*T.CYAN)}{T.BOLD}┃ {s}{T.RESET}"

        m = re.match(r"^(\s*)(\d+)([.)])\s+", text)

        if m:

            return (

                f"{m.group(1)}{_fg(*T.YELLOW)}{T.BOLD}{m.group(2)}{m.group(3)}{T.RESET} "

                f"{_fg(*T.TEXT)}{text[m.end():]}{T.RESET}"

            )

        if re.match(r"^\s*[-•●]\s", text):

            return f"  {_fg(*T.MUTED)}┆{T.RESET} {text.strip()}"

        return f"{_fg(*T.TEXT)}{text}{T.RESET}"

    @staticmethod

    def _md_inline(text: str) -> str:

        t = re.sub(r"\*\*(.+?)\*\*", f"{T.BOLD}\\1{T.RESET}", text)

        t = re.sub(r"(?<!`)\`([^`]+)\`", f"{_fg(*T.CODE)}\\1{T.RESET}", t)

        return t

    def _render_markdown(self, text: str, width: int) -> List[str]:

        out: List[str] = []

        in_fence = False

        fence_lines: List[str] = []

        fence_lang = ""

        blank_count = 0

        for raw in text.split("\n"):

            stripped = raw.strip()

            if not stripped:

                blank_count += 1

                continue

            else:

                blank_count = 0

            if stripped.startswith("```"):

                if in_fence:

                    in_fence = False

                    lang_tag = f" {_fg(*T.MUTED)}# {fence_lang}{T.RESET}" if fence_lang else ""

                    out.append(f"  {_fg(*T.BORDER_DIM)}┌─ code{lang_tag}{'─' * max(width - 12 - len(fence_lang), 0)}┐{T.RESET}")

                    for fl in fence_lines:

                        out.append(f"  {T.DIM}┆{T.RESET} " + self._clip(f"{_fg(*T.CODE)}{fl}{T.RESET}", width - 4))

                    out.append(f"  {_fg(*T.BORDER_DIM)}└{'─' * (width - 4)}┘{T.RESET}")

                    fence_lines = []

                    fence_lang = ""

                else:

                    in_fence = True

                    fence_lang = stripped[3:].strip()

                continue

            if in_fence:

                fence_lines.append(stripped)

                continue

            if blank_count > 0 and out and out[-1] != "":

                for _ in range(min(blank_count, 1)):

                    out.append("")

                continue

            if stripped.startswith("#### "):

                out.append(f"  {_fg(*T.YELLOW)}{T.BOLD}▸ {stripped[5:]}{T.RESET}")

            elif stripped.startswith("### "):

                out.append(f"  {_fg(*T.YELLOW)}{T.BOLD}▸ {stripped[4:]}{T.RESET}")

            elif stripped.startswith("## "):

                out.append(f"  {_fg(*T.RED)}{T.BOLD}█ {stripped[3:]}{T.RESET}")

                out.append(f"  {_fg(*T.BORDER_DIM)}  {'─' * min(width - 4, 38)}{T.RESET}")

            elif stripped.startswith("# "):

                out.append(f"  {_fg(*T.RED)}{T.BOLD}██ {stripped[2:]}{T.RESET}")

                out.append(f"  {_fg(*T.BORDER_DIM)}  {'─' * min(width - 4, 38)}{T.RESET}")

            elif stripped.startswith("> "):

                out.append(f"  {_fg(*T.MUTED)}{T.DIM}┆ {T.ITALIC}{self._md_inline(stripped[2:])}{T.RESET}")

            elif re.match(r"^\s*[-*•]\s+", stripped):

                body = re.sub(r"^\s*[-*•]\s+", "", stripped)

                styled_body = self._md_inline(body)

                out.append(f"  {_fg(*T.YELLOW)}•{T.RESET} {styled_body}")

            elif re.match(r"^\s*\d+[.)]\s+", stripped):

                m = re.match(r"^\s*\d+[.)]\s+", stripped)

                num = f"{m.group(0).strip()}"

                styled_body = self._md_inline(stripped[m.end():])

                out.append(f"  {_fg(*T.YELLOW)}{num}{T.RESET} {styled_body}")

            else:

                for ln in self._wrap(self._md_inline(stripped), width):

                    out.append(f"  {ln}")

        if fence_lines:

            lang_tag = f" {_fg(*T.MUTED)}# {fence_lang}{T.RESET}" if fence_lang else ""

            out.append(f"  {_fg(*T.BORDER_DIM)}┌─ code{lang_tag}{'─' * max(width - 12 - len(fence_lang), 0)}┐{T.RESET}")

            for fl in fence_lines:

                out.append(f"  {T.DIM}┆{T.RESET} " + self._clip(f"{_fg(*T.CODE)}{fl}{T.RESET}", width - 4))

            out.append(f"  {_fg(*T.BORDER_DIM)}└{'─' * (width - 4)}┘{T.RESET}")

        return out

    def _render_message(self, msg: dict, width: int) -> List[str]:

        kind = msg.get("kind", "text")

        out: List[str] = []

        if kind == "user":

            inner = width - 4

            lines = self._wrap(msg["text"], max(inner, 10)) or [""]

            border = _fg(*T.USER_BORDER)

            head = f"{_fg(*T.TEXT)}{T.BOLD}YOU{T.RESET}"

            head_w = DeltaTUI._vwidth(DeltaTUI._plain(head))

            top = f"  {border}╭─[ {head}{border} ]{'─' * max(inner - 4 - head_w, 0)}╮{T.RESET}"

            out.append(top)

            for ln in lines:

                plain = DeltaTUI._clip(ln, inner)

                pad = inner - DeltaTUI._vwidth(DeltaTUI._plain(plain))

                out.append(f"  {border}│{T.RESET} {_fg(*T.TEXT)}{plain}{' ' * max(pad, 0)} {border}│{T.RESET}")

            out.append(f"  {border}╰{'─' * (inner + 2)}╯{T.RESET}")

            out.append("")

        elif kind == "ai":

            inner = width - 6

            border = _fg(*T.AI_BORDER)

            head = f"{_fg(*T.RED)}{T.BOLD}Δ AI{T.RESET}"

            head_w = DeltaTUI._vwidth(DeltaTUI._plain(head))

            top = f"  {border}╭─[ {head}{border} ]{'─' * max(inner - 4 - head_w, 0)}╮{T.RESET}"

            out.append(top)

            body = self._render_markdown(msg["text"], inner)

            if not body:

                body = [""]

            for ln in body:

                plain = ln

                if DeltaTUI._vwidth(DeltaTUI._plain(ln)) > inner:

                    plain = DeltaTUI._clip(ln, inner)

                pad = inner - DeltaTUI._vwidth(DeltaTUI._plain(plain))

                out.append(f"  {border}│{T.RESET} {plain}{' ' * max(pad, 0)} {border}│{T.RESET}")

            out.append(f"  {border}╰{'─' * (inner + 2)}╯{T.RESET}")

            out.append("")

        elif kind == "success":

            out.append(f"  {_fg(*T.SUCCESS)}┃ ✔ {msg['text']}{T.RESET}")

        elif kind == "thought":

            out.append(f"  {_fg(*T.MUTED)}{T.DIM}┆ {T.ITALIC}{msg['text']}{T.RESET}")

        elif kind == "agent":

            out.append(f"  {_fg(*T.ORANGE)}{T.BOLD}▸ {msg['text']}{T.RESET}")

        elif kind == "tool":

            bullet = f"{_fg(*T.TOOL)}{T.BOLD}◈{T.RESET}"

            name = f"{_fg(*T.TOOL)}{T.BOLD}{msg['bullet']}{T.RESET}"

            call = msg.get("call", "")

            result = msg.get("result", "")

            head = f"  {bullet} {name}(\"{self._clip(call, width - 20)}\")"

            if result:

                head += f" {_fg(*T.MUTED)}→{T.RESET} {self._clip(result, width - 14)}"

            out.append(self._clip(head, width))

            for ln in msg.get("lines", []):

                out.append(f"  {T.DIM}┆{T.RESET} " + self._clip(self._style_line(ln), width - 4))

        elif kind == "notice":

            out.append(f"  {_fg(*T.CYAN)}┃ // {msg['text']}{T.RESET}")

        elif kind == "text":

            for ln in self._wrap(msg["text"], width):

                out.append(f"  {_fg(*T.TEXT)}{self._style_line(ln)}{T.RESET}")

        else:

            out.append(f"  {_fg(*T.TEXT)}{self._clip(self._style_line(msg['text']), width - 2)}{T.RESET}")

        return out

    def _repaint(self, state: str = "ready", cursor: bool = True) -> None:

        lay = self._layout()

        w, h = lay["w"], lay["h"]

        with self._draw_lock:

            self._clear_screen()

            self._draw_chrome(lay)

            self._draw_header(lay)

            cw = lay["main_w"] - 4

            rows: List[str] = []

            for msg in self.messages:

                rows.extend(self._render_message(msg, cw))

            avail = lay["transcript_last"] - lay["transcript_top"] + 1

            total = len(rows)

            start = max(0, total - avail - self.scroll)

            row = lay["transcript_top"]

            muted = _fg(*T.MUTED)

            has_scroll = total > avail

            if self.scroll > 0:

                self._move(row - 1, w - 3)

                self._write(f"{muted}▲{T.RESET}")

            for i in range(avail):

                self._move(row, 2)

                if start + i < total:

                    text_out = self._clip(rows[start + i], cw)

                    self._write(text_out)

                    pad = cw - self._vwidth(self._plain(text_out))

                    if pad > 0:

                        self._write(" " * pad)

                else:

                    self._write(" " * cw)

                row += 1

            if has_scroll and self.scroll > 0 and row - 1 <= lay["input_row"] - 3:

                self._move(row - 1, w - 3)

                self._write(f"{muted}▼{T.RESET}")

            self._draw_footer(lay, state)

            self._draw_input_row(lay, cursor=cursor)

            if lay.get("sidebar_w"):

                self._draw_sidebar(lay, state)

    def _repaint_input_only(self, cursor: bool = True) -> None:

        lay = self._layout()

        with self._draw_lock:

            self._draw_input_row(lay, cursor=cursor)

    def _add_welcome(self, welcome: str) -> None:

        text = re.sub(r"\s*\u25cf\s*", " · ", welcome).strip()

        self.messages.append({

            "kind": "success",

            "text": f"Δ DELTA Initialized — Hostile AI Security Assessment Ready",

        })

        self.messages.append({

            "kind": "notice",

            "text": f"Session started · Type 'help' for commands · '?' for shortcuts",

        })

    def _toggle_help(self) -> None:

        if self._help_idx is not None:

            del self.messages[self._help_idx:]

            self._help_idx = None

        else:

            lines = [

                {"kind": "notice", "text": "Shortcuts"},

                {"kind": "text", "text": "↑ / ↓    input history"},

                {"kind": "text", "text": "mouse wheel / PgUp PgDn  scroll transcript"},

                {"kind": "text", "text": "Ctrl+C    copy transcript ke clipboard (kosongkan input dulu)"},

                {"kind": "text", "text": "Ctrl+C    cancel input saat sedang mengetik"},

                {"kind": "text", "text": "?         close this help"},

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

        plain = [self._plain(ln).rstrip() for ln in lines]

        header = f"Delta session transcript — {datetime.now():%Y-%m-%d %H:%M:%S}"

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

    @staticmethod

    def _copy_posix(text: str) -> bool:

        if os.name == "nt":

            return False

        import base64

        import shutil as _shutil

        import subprocess

        for prog in ("xclip", "pbcopy", "wl-copy"):

            path = _shutil.which(prog)

            if not path:

                continue

            try:

                p = subprocess.run(

                    [path], input=text.encode("utf-8"),

                    timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,

                )

                if p.returncode == 0:

                    return True

            except Exception:

                pass

        try:

            b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")

            sys.__stdout__.write(f"\x1b]52;c;{b64}\x07")

            sys.__stdout__.flush()

            return True

        except Exception:

            return False

    def _copy_transcript(self) -> Tuple[bool, str, str]:

        text = self._transcript_text()

        if self._copy_win32(text):

            return True, "Windows clipboard", ""

        if self._copy_posix(text):

            return True, "OSC52/xclip/pbcopy", ""

        try:

            path = os.path.join(self.engine.config.data_dir, "delta_copy.txt")

            with open(path, "w", encoding="utf-8") as f:

                f.write(text)

            return True, "file", path

        except Exception:

            return False, "", ""

    def _read_key(self) -> str:

        import msvcrt

        if self._hin is not None:

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
                    self._notice("Stop requested (Ctrl+C)...", color="yellow")
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

            if ch == "\t":

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

            time.sleep(0.53)

    def _skull_animator(self, stop: threading.Event) -> None:

        while not stop.is_set():

            if not self._processing and not self.compact:

                with self._draw_lock:

                    lay = self._layout()

                    if random.random() > 0.95:

                        self._draw_header(lay, glitch=True)

                    else:

                        self._draw_header(lay, glitch=False)

                    if lay.get("sidebar_w"):

                        self._draw_sidebar(lay, "hunting")

            time.sleep(0.2)

    def _process_captured(self, fn) -> Tuple[str, Any]:

        buf = io.StringIO()

        old = sys.stdout

        sys.stdout = buf

        try:

            ret = fn()

        finally:

            sys.stdout = old

        text = ANSI_STRIP.sub("", buf.getvalue())

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

    @staticmethod

    def _summarize(lines: List[str]) -> str:

        for ln in lines:

            s = ln.strip()

            low = s.lower()

            if any(k in low for k in (

                "completed", "found", "saved", "failed", "error", "granted",

                "denied", "success", "resolved", "generated", "decoded",

                "matches", "analyzed", "report",

            )):

                return s

        return lines[-1].strip() if lines else "done"

    def _add_tool_call(self, raw: str, captured: str) -> None:

        try:

            parts = shlex.split(raw)

        except ValueError:

            parts = raw.split()

        name = (parts[0] if parts else raw).lower()

        name = self.engine._aliases.get(name, name)

        arg_str = " ".join(parts[1:]) if parts else ""

        lines = [ln for ln in captured.split("\n") if ln.strip()]

        result = self._summarize(lines)

        self.messages.append({

            "kind": "tool",

            "bullet": name.title(),

            "call": arg_str,

            "result": result,

            "lines": lines,

        })

    def _add_agent_line(self, text: str) -> None:

        clipped = text if len(text) <= 48 else text[:47] + "…"

        self.messages.append({

            "kind": "agent",

            "text": f"DELTA :: HOSTILE AGENT{_fg(*T.YELLOW)}({clipped})",

        })

    def _submit(self, text: str) -> None:

        self._history.append(text)

        self._hist_idx = len(self._history)

        self.scroll = 0

        self.input_text, self.input_pos = "", 0

        if text.strip().lower() in ("/clear", "/cls", "/clean", "/bersihkan", "clear", "cls", "ai reset"):

            self.messages = []

            self.scroll = 0

            if self.engine.llm_engine:

                self.engine.llm_engine.reset_conversation()

            self.messages.append({"kind": "notice", "text": "Chat dibersihkan — Delta siap bantu kamu."})

            self._repaint()

            return

        self.messages.append({"kind": "user", "text": text})

        llm = self.engine.llm_engine

        llm_msgs_before = len(llm.messages) if llm else 0

        start = time.monotonic()

        self._processing = True

        self.engine._stop_event = threading.Event()

        spin_stop = threading.Event()

        spinner = threading.Thread(

            target=self._spinner, args=(spin_stop,), daemon=True

        )

        spinner.start()

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

        spin_stop.set()

        spinner.join(timeout=1.0)

        self._processing = False

        elapsed = time.monotonic() - start

        llm_used = False

        tokens = 0

        if llm and len(llm.messages) > llm_msgs_before:

            assistant_msgs = [m for m in llm.messages if m.get("role") == "assistant"]

            if assistant_msgs and not assistant_msgs[-1]["content"].startswith("ERROR"):

                llm_used = True

                usage = llm.last_usage or {}

                tokens = (

                    usage.get("total_tokens")

                    or (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))

                    or 0

                )

                if not tokens:

                    tokens = max(1, len(assistant_msgs[-1]["content"].split()))

        first = text.split()[0].lower() if text.split() else ""

        is_command = first in self.engine._builtin_commands or first in self.engine._aliases

        if isinstance(result, dict):

            if llm_used:

                self.messages.append({

                    "kind": "thought",

                    "text": f"Hunted for {elapsed:.1f}s, {tokens} tokens burned · "

                            f"Striking {first.title() if first else 'Target'}",

                })

            err = result.get("error") or ""

            response = result.get("response") or ""

            command = result.get("command") or ""

            if err:

                self.messages.append({"kind": "notice", "text": err})

            if response:

                self.messages.append({"kind": "ai", "text": response})

            if command:

                self._add_tool_call(command, captured)

            elif err and captured.strip():

                self._add_tool_call(first or text, captured)

            elif captured.strip():

                for ln in captured.split("\n"):

                    if ln.strip():

                        self.messages.append({"kind": "text", "text": ln})

        elif llm_used:

            self.messages.append({

                "kind": "thought",

                "text": f"Hunted for {elapsed:.1f}s, {tokens} tokens burned · "

                        f"Striking {first.title() if first else 'Target'}",

            })

            if is_command or (captured and not captured.startswith("ERROR")):

                if is_command:

                    self._add_agent_line(f"planning: {text}")

                    self._add_tool_call(text, captured)

                else:

                    from delta.ai.llm import parse_command_from_response

                    assistant_msgs = [m for m in llm.messages if m.get("role") == "assistant"]

                    cmd = parse_command_from_response(assistant_msgs[-1]["content"]) if assistant_msgs else None

                    if cmd:

                        self._add_agent_line(f"planning: {text}")

                        self._add_tool_call(cmd, captured)

                    else:

                        self._add_agent_line(f"\"{text}\"")

                        response = self.engine.last_llm_response or ""

                        for ln in response.split("\n"):

                            if ln.strip():

                                self.messages.append({"kind": "text", "text": ln})

        elif is_command:

            self._add_tool_call(text, captured)

        else:

            if captured.strip():

                for ln in captured.split("\n"):

                    if ln.strip():

                        self.messages.append({"kind": "text", "text": ln})

            else:

                self.messages.append({"kind": "notice", "text": "No output."})

        if len(self.messages) > 500:

            self.messages = self.messages[-500:]

        self._repaint()

    def _spinner(self, stop: threading.Event) -> None:

        i = 0

        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        model = self.engine.llm_engine.model if self.engine.llm_engine else "offline"

        while not stop.is_set():

            lay = self._layout()

            w = lay["main_w"]

            inner_w = w - 4

            row = lay["input_row"] + 1

            dots = "." * (i % 4)

            with self._draw_lock:

                self._move(row, 2)

                self._write(f"{_fg(*T.BORDER)}│{T.RESET} ")

                box_w = inner_w - 4

                spin = frames[i % len(frames)]

                line = f"{_fg(*T.THINK)}{spin} Thinking{dots}{T.RESET}"

                self._write(self._clip(line, box_w).ljust(box_w))

                self._write(f" {_fg(*T.BORDER)}│{T.RESET}")

            i += 1

            time.sleep(0.12)

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

        animator: Optional[threading.Thread] = None

        if os.name == "nt":

            blinker = threading.Thread(

                target=self._cursor_blinker, args=(blinker_stop,), daemon=True

            )

            blinker.start()

            animator = threading.Thread(

                target=self._skull_animator, args=(blinker_stop,), daemon=True

            )

            animator.start()

        try:

            while self.engine.running:

                action, payload = self._read_line()

                if action == "submit":

                    if not (payload or "").strip():

                        self._repaint()

                        continue

                    self._submit(payload)

                elif action == "cancel":

                    self._notice("[Use 'exit' to quit]", color="dim")

                elif action == "copy":

                    ok, how, path = self._copy_transcript()

                    if ok:

                        if how == "file":

                            self._notice(f"Clipboard tidak tersedia — transcript disimpan ke {path}")

                        else:

                            self._notice(f"✔ Transcript disalin ke {how} (Ctrl+C)", color="success")

                    else:

                        self._notice("Gagal menyalin transcript ke clipboard")

                elif action == "help":

                    self._toggle_help()

                elif action == "exit":

                    self.engine.running = False

                    break

        finally:

            blinker_stop.set()

            if blinker:

                blinker.join(timeout=1.0)

            if animator:

                animator.join(timeout=1.0)

        self.messages.append({

            "kind": "notice",

            "text": "Goodbye, Tuan. Delta is going dark — it doesn't forget.",

        })

        self.scroll = 0

        self._repaint(cursor=False)

        time.sleep(0.5)

        self._show_real_cursor()

        self._clear_screen()

        print()

        print(f"  {_fg(*T.BORDER)}▐ {_fg(*T.RED)}DELTA{_fg(*T.BORDER)} ▌{_fg(*T.MUTED)} — Hostile AI Security Assessment CLI{T.RESET}")

        print()

        print(f"  {_fg(*T.RED)}Goodbye, Tuan. Delta is going dark — it doesn't forget.{T.RESET}")

        print()

    def show_login(self, config, max_attempts: int = 3) -> bool:

        import getpass

        self._clear_screen()

        w, h = self._size()

        box_w = min(58, w - 4)

        left = (w - box_w) // 2

        top = max(2, h // 2 - 4)

        border = _fg(*T.BORDER)

        muted = _fg(*T.MUTED)

        txt = _fg(*T.TEXT)

        def edge(row, start_char, end_char) -> None:

            self._move(top + row, left + 1)

            self._write(

                f"{border}{start_char}{'─' * (box_w - 2)}{end_char}{T.RESET}"

            )

        def line(row, content: str) -> None:

            self._move(top + row, left + 1)

            self._write(f"{border}│{T.RESET} " + self._clip(content, box_w - 4))

            self._write(f" {border}│{T.RESET}")

        edge(0, "╭", "╮")

        self._move(top, left + 2)

        self._write(

            f"{_fg(*T.RED)}●{T.RESET}  {_fg(*T.YELLOW)}●{T.RESET}  {_fg(*T.GREEN)}●{T.RESET}"

        )

        line(1, f"{_fg(*T.RED)}[ {_fg(*T.TEXT)}DELTA :: RESTRICTED ACCESS{_fg(*T.RED)} ]{T.RESET}")

        line(2, f"{_fg(*T.MUTED)}» Every unverified attempt is logged.{T.RESET}")

        line(3, "")

        line(4, f"{_fg(*T.RED)}Username:{T.RESET}")

        line(5, f"{_fg(*T.RED)}Password:{T.RESET}")

        line(6, "")

        edge(7, "╰", "╯")

        input_row = top + 4

        for attempt in range(max_attempts):

            self._move(input_row, left + 12)

            self._clear_line()

            self._write(f"{txt}{T.BOLD}> {T.RESET}")

            username = input()

            self._move(input_row + 1, left + 12)

            self._clear_line()

            self._write(f"{txt}{T.BOLD}> {T.RESET}")

            password = getpass.getpass("")

            if verify_credentials(config, username.strip(), password):

                self._move(input_row + 2, left + 2)

                self._write(

                    f"{_fg(*T.SUCCESS)}✔ Access granted. Selamat datang, "

                    f"{username.strip()}. It was watching for you.{T.RESET}"

                )

                time.sleep(0.6)

                return True

            remaining = max_attempts - attempt - 1

            msg = f"✘ Access denied. Intrusion logged.{f' {remaining} attempt(s) remaining.' if remaining else ''}"

            self._move(input_row + 2, left + 2)

            self._clear_line()

            self._write(f"{_fg(*T.RED)}{msg}{T.RESET}")

        return False

def run_tui(engine) -> bool:

    try:

        tui = DeltaTUI(engine)

        tui.run()

        return True

    except Exception as e:

        print(f"[!] TUI error ({e}); falling back to standard REPL.")

        return False