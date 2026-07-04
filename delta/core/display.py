# delta/core/display.py
"""
Terminal display manager for Delta.
Provides modern terminal UI with colors, animations, panels, progress bars, and banners.
Uses Rich library if available, with pure Standard Library fallback.
"""

import sys
import time
import os
import threading
from typing import Any, Callable, List, Optional, Dict
from dataclasses import dataclass, field


# Try to import Rich for enhanced display
try:
    from rich.console import Console as RichConsole
    from rich.panel import Panel as RichPanel
    from rich.table import Table as RichTable
    from rich.progress import Progress as RichProgress
    from rich.progress import SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.markdown import Markdown as RichMarkdown
    from rich.syntax import Syntax as RichSyntax
    from rich.tree import Tree as RichTree
    from rich.layout import Layout as RichLayout
    from rich.live import Live as RichLive
    from rich.text import Text as RichText
    from rich.columns import Columns as RichColumns
    from rich import box as RichBox
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# --- Fallback ANSI color codes for terminal ---
class ANSI:
    """ANSI escape codes for terminal styling."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Bright foreground colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    @staticmethod
    def colorize(text: str, color: str, bold: bool = False) -> str:
        """Apply ANSI color to text."""
        prefix = ANSI.BOLD if bold else ""
        return f"{prefix}{color}{text}{ANSI.RESET}"

    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove ANSI escape codes from text."""
        import re
        return re.sub(r'\033\[[0-9;]*m', '', text)


class Spinner:
    """Simple spinner for terminal loading animation."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    FRAMES_DOTS = ["⣷", "⣯", "⣟", "⡿", "⢿", "⣻", "⣽", "⣾"]
    FRAMES_CLASSIC = ["|", "/", "-", "\\"]
    FRAMES_BRAILLE = ["⠁", "⠃", "⠇", "⠧", "⠷", "⠿", "⠾", "⠽", "⠻", "⠛", "⠋", "⠉"]

    def __init__(self, message: str = "Processing...", style: str = "braille"):
        """
        Initialize spinner.

        Args:
            message: Text to display next to spinner
            style: Spinner style ('braille', 'dots', 'classic')
        """
        self.message = message
        self.frames = {
            "braille": self.FRAMES_BRAILLE,
            "dots": self.FRAMES_DOTS,
            "classic": self.FRAMES_CLASSIC,
        }.get(style, self.FRAMES_BRAILLE)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._hide_cursor = False

    def _spin(self) -> None:
        """Spinner animation loop."""
        i = 0
        while self.running:
            frame = self.frames[i % len(self.frames)]
            sys.stdout.write(f"\r{ANSI.CYAN}{frame}{ANSI.RESET} {self.message}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)
        # Clear line
        sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
        sys.stdout.flush()

    def start(self) -> None:
        """Start spinner animation."""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop spinner animation."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)


class ProgressBar:
    """Simple terminal progress bar with Standard Library fallback."""

    def __init__(self, total: int = 100, prefix: str = "Progress:",
                 suffix: str = "Complete", length: int = 40):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.length = length
        self.current = 0

    def update(self, iteration: int) -> None:
        """Update progress bar."""
        self.current = iteration
        percent = f"{100 * (iteration / float(self.total)):.1f}"
        filled = int(self.length * iteration // self.total)
        bar = "█" * filled + "─" * (self.length - filled)
        sys.stdout.write(f"\r{ANSI.GREEN}{self.prefix}{ANSI.RESET} |{ANSI.CYAN}{bar}{ANSI.RESET}| {ANSI.BOLD}{percent}%{ANSI.RESET} {self.suffix}")
        sys.stdout.flush()
        if iteration == self.total:
            print()

    def __enter__(self) -> "ProgressBar":
        return self

    def __exit__(self, *args) -> None:
        self.update(self.total)


class DisplayManager:
    """
    Central display manager for Delta.
    Provides rich terminal output with Rich library or pure Standard Library fallback.
    """

    def __init__(self):
        """Initialize display manager."""
        self.rich = HAS_RICH
        if self.rich:
            self.console = RichConsole(color_system="auto")
        self._banner_shown = False

    def show_banner(self) -> None:
        """Display Delta ASCII banner."""
        if self._banner_shown:
            return
        self._banner_shown = True

        banner = self._get_banner()
        if self.rich:
            from rich.panel import Panel
            from rich.text import Text
            from rich import box

            text = Text(banner, style="bold cyan")
            panel = Panel(
                text,
                border_style="bright_blue",
                box=box.DOUBLE_EDGE,
                padding=(1, 4),
                subtitle="[bold yellow]AI-Powered Security Assessment CLI[/bold yellow]",
            )
            self.console.print(panel)
            self.console.print()

            # Tool info
            info_text = Text()
            info_text.append("  ⚡ ", style="yellow")
            info_text.append("Version 1.0.0", style="bold white")
            info_text.append("  |  ", style="dim white")
            info_text.append("🔒 ", style="yellow")
            info_text.append("Authorized Security Testing Only", style="green")
            info_text.append("  |  ", style="dim white")
            info_text.append("📡 ", style="yellow")
            info_text.append("Offline Mode", style="cyan")
            self.console.print(info_text)
            self.console.print()
        else:
            print(ANSI.BRIGHT_CYAN + banner + ANSI.RESET)
            print(ANSI.BOLD + ANSI.YELLOW + "=" * 60 + ANSI.RESET)
            print(ANSI.GREEN + "  Delta v1.0.0 - AI-Powered Security Assessment CLI" + ANSI.RESET)
            print(ANSI.CYAN + "  Authorized Security Testing Only | Offline Mode" + ANSI.RESET)
            print(ANSI.YELLOW + "=" * 60 + ANSI.RESET)
            print()

    def _get_banner(self) -> str:
        """Generate ASCII art banner."""
        return r"""
    ██████╗ ███████╗██╗  ████████╗ █████╗
    ██╔══██╗██╔════╝██║  ╚══██╔══╝██╔══██╗
    ██║  ██║█████╗  ██║     ██║   ███████║
    ██║  ██║██╔══╝  ██║     ██║   ██╔══██║
    ██████╔╝███████╗███████╗██║   ██║  ██║
    ╚═════╝ ╚══════╝╚══════╝╚═╝   ╚═╝  ╚═╝
    """

    def print(self, text: str = "", style: Optional[str] = None, end: str = "\n") -> None:
        """Print colored text."""
        if self.rich:
            if style:
                self.console.print(text, style=style, end=end)
            else:
                self.console.print(text, end=end)
        else:
            color_map = {
                "red": ANSI.RED, "green": ANSI.GREEN, "yellow": ANSI.YELLOW,
                "blue": ANSI.BLUE, "cyan": ANSI.CYAN, "magenta": ANSI.MAGENTA,
                "white": ANSI.WHITE, "gray": ANSI.GRAY, "bold": ANSI.BOLD,
                "red bold": ANSI.BOLD + ANSI.RED,
                "green bold": ANSI.BOLD + ANSI.GREEN,
                "yellow bold": ANSI.BOLD + ANSI.YELLOW,
                "blue bold": ANSI.BOLD + ANSI.BLUE,
                "cyan bold": ANSI.BOLD + ANSI.CYAN,
                "magenta bold": ANSI.BOLD + ANSI.MAGENTA,
            }
            if style and style in color_map:
                print(f"{color_map[style]}{text}{ANSI.RESET}", end=end)
            else:
                print(text, end=end)

    def info(self, message: str) -> None:
        """Print info message."""
        self.print(f"ℹ  {message}", style="cyan")

    def success(self, message: str) -> None:
        """Print success message."""
        self.print(f"✔  {message}", style="green")

    def warning(self, message: str) -> None:
        """Print warning message."""
        self.print(f"⚠  {message}", style="yellow")

    def error(self, message: str) -> None:
        """Print error message."""
        self.print(f"✘  {message}", style="red")

    def debug(self, message: str) -> None:
        """Print debug message."""
        self.print(f"🔍 {message}", style="gray")

    def section(self, title: str) -> None:
        """Print section header."""
        if self.rich:
            from rich.panel import Panel
            self.console.print(Panel(title, border_style="blue", padding=(0, 2)))
        else:
            print(f"\n{ANSI.BOLD}{ANSI.BLUE}─── {title} ───{ANSI.RESET}\n")

    def panel(self, title: str, content: str, style: str = "blue") -> None:
        """Display content in a panel."""
        if self.rich:
            from rich.panel import Panel
            from rich import box
            border_styles = {
                "info": "blue", "success": "green", "warning": "yellow",
                "error": "red", "critical": "red bold",
            }
            bs = border_styles.get(style, style)
            panel = Panel(content, title=title, border_style=bs, box=box.ROUNDED, padding=(1, 2))
            self.console.print(panel)
        else:
            border_styles = {
                "info": ANSI.BLUE, "success": ANSI.GREEN, "warning": ANSI.YELLOW,
                "error": ANSI.RED, "critical": ANSI.BOLD + ANSI.RED,
            }
            border = border_styles.get(style, ANSI.BLUE)
            width = 60
            print(f"\n{border}╔{'═' * width}╗{ANSI.RESET}")
            print(f"{border}║{ANSI.RESET} {ANSI.BOLD}{title}{ANSI.RESET}{' ' * (width - len(title) - 1)}{border}║{ANSI.RESET}")
            print(f"{border}╠{'═' * width}╣{ANSI.RESET}")
            for line in content.split("\n"):
                line = line[:width]
                print(f"{border}║{ANSI.RESET} {line}{' ' * (width - len(line) - 1)}{border}║{ANSI.RESET}")
            print(f"{border}╚{'═' * width}╝{ANSI.RESET}\n")

    def table(self, title: str, columns: List[str], rows: List[List[Any]]) -> None:
        """Display data in a table."""
        if self.rich:
            table = RichTable(title=title, box=RichBox.MINIMAL_HEAVY_HEAD,
                              border_style="blue", header_style="bold cyan")
            for col in columns:
                table.add_column(col)
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            self.console.print(table)
        else:
            print(f"\n{ANSI.BOLD}{ANSI.CYAN}{title}{ANSI.RESET}")
            col_widths = []
            for i, col in enumerate(columns):
                max_w = len(col)
                for row in rows:
                    max_w = max(max_w, len(str(row[i] if i < len(row) else "")))
                col_widths.append(min(max_w + 2, 40))

            # Header
            header = "│"
            sep = "├"
            for i, col in enumerate(columns):
                header += f" {col:<{col_widths[i]-1}}│"
                sep += "─" * col_widths[i] + "┼"
            sep = sep[:-1] + "┤"
            print(f"┌{'─' * (sum(col_widths) + len(columns) - 1)}┐")
            print(f"│{ANSI.BOLD}{header[1:]}{ANSI.RESET}")
            print(sep)

            # Rows
            for row in rows:
                row_str = "│"
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        row_str += f" {str(cell):<{col_widths[i]-1}}│"
                print(row_str)
            print(f"└{'─' * (sum(col_widths) + len(columns) - 1)}┘\n")

    def tree(self, title: str, items: Dict[str, Any], indent: int = 0) -> None:
        """Display hierarchical tree structure."""
        if self.rich:
            tree = RichTree(title, style="blue", guide_style="cyan")
            self._build_tree(tree, items)
            self.console.print(tree)
        else:
            prefix = "  " * indent
            print(f"\n{ANSI.BOLD}{ANSI.CYAN}{title}{ANSI.RESET}")
            self._print_tree_plain(items, indent + 1)

    def _build_tree(self, tree: Any, items: Dict[str, Any]) -> None:
        """Recursively build Rich tree."""
        for key, value in items.items():
            if isinstance(value, dict):
                branch = tree.add(f"📁 {key}")
                self._build_tree(branch, value)
            else:
                style = "green" if value in ["✓", "✔", "pass"] else "yellow" if value in ["⚠", "warn"] else "white"
                tree.add(f"{value}  {key}")

    def _print_tree_plain(self, items: Any, indent: int = 0) -> None:
        """Print tree without Rich."""
        prefix = "  " * indent
        if isinstance(items, dict):
            for key, value in items.items():
                if isinstance(value, dict):
                    print(f"{prefix}{ANSI.YELLOW}📁 {key}{ANSI.RESET}")
                    self._print_tree_plain(value, indent + 1)
                else:
                    print(f"{prefix}{ANSI.GREEN}├──{ANSI.RESET} {key}: {value}")

    def progress(self, iterable, description: str = "Processing...") -> Any:
        """Progress bar wrapper for iterables."""
        if self.rich:
            from rich.progress import track
            return track(iterable, description=description)
        else:
            return self._progress_generator(iterable, description)

    def _progress_generator(self, iterable, description: str = "Processing..."):
        """Progress bar generator for fallback."""
        items = list(iterable)
        total = len(items)
        for i, item in enumerate(items):
            percent = (i + 1) / total * 100
            bar_len = 30
            filled = int(bar_len * (i + 1) // total)
            bar = "█" * filled + "─" * (bar_len - filled)
            sys.stdout.write(f"\r{ANSI.CYAN}{description}{ANSI.RESET} |{ANSI.GREEN}{bar}{ANSI.RESET}| {ANSI.BOLD}{percent:3.0f}%{ANSI.RESET}")
            sys.stdout.flush()
            yield item
        print()

    def typing_animation(self, text: str, delay: float = 0.02) -> None:
        """Display text with typing animation."""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    def live(self, renderable: Any) -> Any:
        """Create a live updating display."""
        if self.rich:
            from rich.live import Live
            return Live(renderable, refresh_per_second=10)
        return None

    def markdown(self, text: str) -> None:
        """Render markdown text."""
        if self.rich:
            md = RichMarkdown(text)
            self.console.print(md)
        else:
            # Simple markdown rendering
            for line in text.split("\n"):
                if line.startswith("# "):
                    print(f"\n{ANSI.BOLD}{ANSI.CYAN}{line[2:]}{ANSI.RESET}\n{'─' * 40}")
                elif line.startswith("## "):
                    print(f"\n{ANSI.BOLD}{ANSI.BLUE}{line[3:]}{ANSI.RESET}\n{'─' * 30}")
                elif line.startswith("### "):
                    print(f"\n{ANSI.BOLD}{line[4:]}{ANSI.RESET}")
                elif line.startswith("- "):
                    print(f"  {ANSI.CYAN}•{ANSI.RESET} {line[2:]}")
                elif line.startswith("**") and line.endswith("**"):
                    print(ANSI.BOLD + line.strip("*") + ANSI.RESET)
                elif line.startswith("`") and line.endswith("`"):
                    print(f"{ANSI.GREEN}{line}{ANSI.RESET}")
                else:
                    print(line)

    def code(self, code: str, language: str = "python") -> None:
        """Display syntax highlighted code."""
        if self.rich:
            from rich.syntax import Syntax
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            self.console.print(syntax)
        else:
            print(f"{ANSI.GRAY}{'─' * 50}{ANSI.RESET}")
            print(f"{ANSI.GREEN}{code}{ANSI.RESET}")
            print(f"{ANSI.GRAY}{'─' * 50}{ANSI.RESET}")

    def columns(self, items: List[str]) -> None:
        """Display items in columns."""
        if self.rich:
            from rich.columns import Columns
            self.console.print(Columns([RichText(item) for item in items]))
        else:
            for item in items:
                print(f"  {ANSI.CYAN}•{ANSI.RESET} {item}")