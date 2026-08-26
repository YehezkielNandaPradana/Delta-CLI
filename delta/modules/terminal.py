# Refactor: terminal exec
# delta/modules/terminal.py

"""

Terminal Module for Delta AI Coding Agent.

Provides safe sub-process command execution with timeouts, output capture,

and non-interactive execution mode.

"""

import os

import shlex

import subprocess

from typing import Any, Dict, Optional

class TerminalModule:

    """Terminal execution module with timeout & safety boundaries."""

    def __init__(self, timeout: int = 30) -> None:

        self.default_timeout = timeout

        self.forbidden_commands = {

            "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "shutdown", "reboot"

        }

    def execute(self, command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:

        """Execute a shell command and capture stdout/stderr safely.

        Args:

            command: Command string to execute

            cwd: Working directory (defaults to current CWD)

            timeout: Execution timeout in seconds

        """

        cmd_str = command.strip()

        if not cmd_str:

            return {"success": False, "output": "", "error": "Empty command provided."}

        for dangerous in self.forbidden_commands:

            if dangerous in cmd_str:

                return {"success": False, "output": "", "error": f"Command blocked by safety policy: dangerous pattern '{dangerous}' detected."}

        exec_timeout = timeout or self.default_timeout

        work_dir = os.path.abspath(cwd) if cwd else os.getcwd()

        use_shell = True if os.name == "nt" else False

        process = None

        try:

            process = subprocess.Popen(

                cmd_str if use_shell else shlex.split(cmd_str),

                shell=use_shell,

                cwd=work_dir,

                stdout=subprocess.PIPE,

                stderr=subprocess.PIPE,

                text=True,

                encoding="utf-8",

                errors="replace",

            )

            stdout, stderr = process.communicate(timeout=exec_timeout)

            success = (process.returncode == 0)

            combined = stdout

            if stderr and stderr.strip():

                combined += ("\n--- STDERR ---\n" + stderr if combined else stderr)

            return {

                "success": success,

                "exit_code": process.returncode,

                "output": combined.strip(),

                "error": stderr.strip() if not success else None,

            }

        except subprocess.TimeoutExpired:

            if process:

                process.kill()

            return {

                "success": False,

                "exit_code": -1,

                "output": "",

                "error": f"Command execution timed out after {exec_timeout} seconds.",

            }

        except Exception as e:

            return {

                "success": False,

                "exit_code": -1,

                "output": "",

                "error": f"Execution error: {str(e)}",

            }

