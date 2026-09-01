# tests/test_tui_workflow.py
"""Tests for Delta TUI text wrapping engine, shared workflow rendering, and responsive widths."""

import unittest
from delta.core.tui import wrap_terminal_text, visual_width, plain_text

class TestTUIWrappingAndWorkflow(unittest.TestCase):
    def test_plain_and_visual_width(self):
        text = "\033[38;2;56;189;248mDelta CLI\033[0m"
        self.assertEqual(plain_text(text), "Delta CLI")
        self.assertEqual(visual_width(text), 9)

    def test_wrap_terminal_text_basic(self):
        long_str = "Delta is an autonomous AI agent for software engineering, penetration testing, and code analysis."
        lines = wrap_terminal_text(long_str, available_width=30, indent="> ", continuation_prefix="  ")
        self.assertTrue(len(lines) >= 3)
        self.assertTrue(lines[0].startswith("> "))
        self.assertTrue(lines[1].startswith("  "))
        for ln in lines:
            self.assertTrue(visual_width(ln) <= 30)

    def test_wrap_terminal_text_unbroken_tokens(self):
        long_path = "D:\\VeryLongProjectDirectoryName\\NestedModules\\ExtremelyLongFileOrClassIdentifierNameHere.cs"
        lines = wrap_terminal_text(long_path, available_width=25, indent="├─ ", continuation_prefix="│  ")
        self.assertTrue(len(lines) >= 3)
        for ln in lines:
            self.assertTrue(visual_width(ln) <= 25)

    def test_wrap_terminal_text_no_horizontal_scroll(self):
        for width in [40, 60, 80, 120, 160]:
            cmd = "dotnet build --configuration Release --property:AssemblyVersion=2.0.0 /p:GenerateDocumentation=true /verbosity:diagnostic"
            lines = wrap_terminal_text(cmd, available_width=width, indent="Run: ", continuation_prefix="     ")
            for ln in lines:
                self.assertTrue(visual_width(ln) <= width, f"Line '{ln}' exceeds width {width}")

if __name__ == "__main__":
    unittest.main()
