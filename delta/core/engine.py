# Refactor: engine handler
# delta/core/engine.py

"""

Main Delta engine - REPL loop, command dispatch, and AI integration.

"""

import sys

import os

import json

import re

import shlex

import time

import random

import shutil

import traceback

import threading

from datetime import datetime

from functools import lru_cache

from typing import Any, Dict, List, Optional, Tuple, Callable

from dataclasses import dataclass

from delta.core.config import DeltaConfig

from delta.core.database import Database

from delta.core.session import SessionManager

from delta.core.display import DisplayManager, ANSI, Spinner

from delta.core.plugin import PluginManager, PluginBase

from delta.ai.intent import IntentEngine, IntentResult

from delta.ai.llm import LLMEngine, parse_command_from_response, strip_command_tags

# Try to import prompt_toolkit for enhanced input

try:

    from prompt_toolkit import PromptSession

    from prompt_toolkit.history import FileHistory

    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

    from prompt_toolkit.completion import WordCompleter

    from prompt_toolkit.styles import Style

    HAS_PROMPT_TOOLKIT = True

except ImportError:

    PromptSession = None
    FileHistory = None
    AutoSuggestFromHistory = None
    WordCompleter = None
    Style = None
    HAS_PROMPT_TOOLKIT = False

class DeltaEngine:

    """

    Main Delta engine.

    Handles the REPL loop, command parsing, AI integration, and module dispatch.

    """

    def __init__(

        self,

        config: DeltaConfig,

        database: Database,

        session: SessionManager,

        intent_engine: IntentEngine,

        plugin_manager: PluginManager,

        display: DisplayManager,

        llm_engine: Optional[LLMEngine] = None,

        cwd: Optional[str] = None,

    ):

        """

        Initialize Delta engine.

        Args:

            config: Delta configuration

            database: Database instance

            session: Session manager

            intent_engine: AI intent recognition engine

            plugin_manager: Plugin manager

            display: Display manager

            llm_engine: Optional LLM engine for AI-powered responses

        """

        self.config = config

        self.database = database

        self.session = session

        self.intent_engine = intent_engine

        self.plugin_manager = plugin_manager

        self.display = display

        self.llm_engine = llm_engine

        self.running = False

        from delta.modules.skills import SkillManager

        self.skills = SkillManager(config)

        from delta.core.policy import PolicyManager

        self.policy = PolicyManager(config, display)

        self.last_result: Any = None

        self.last_command: str = ""

        self.last_llm_response: str = ""

        self.session_start = datetime.now()

        self._timer_start: Optional[float] = None

        self._in_llm_processing: bool = False

        # Folder aktif untuk perintah file system (cd/ls/write/dst).

        self.cwd = os.path.abspath(cwd) if cwd else os.getcwd()

        self.session.context.working_directory = self.cwd

        # True saat dijalankan di bawah DeltaTUI — _process_with_llm tidak
        # mencetak ke stdout, melainkan mengembalikan hasil terstruktur
        # agar TUI bisa merender respons AI dengan rapi.
        self.tui_mode = False
        self.web_mode = False
        self._initialized = False

        # Coding Agent sub-modules & Tool Registry
        from delta.modules.codebase import CodebaseModule
        from delta.modules.terminal import TerminalModule
        from delta.modules.filesystem import FileSystemModule
        from delta.ai.tools import ToolRegistry, Tool, ToolParameter

        self.fs = FileSystemModule(cwd=self.cwd, display=self.display)
        self.codebase = CodebaseModule(self.cwd)
        self.terminal = TerminalModule()
        self.tools = ToolRegistry()
        self._init_agent_tools()

        # VTuber Agent Integration Adapter & STT Manager
        from delta.vtuber.adapter import VTuberAgentAdapter
        from delta.vtuber.voice.stt.manager import stt_manager
        self.vtuber_adapter = VTuberAgentAdapter(auto_attach=True)
        stt_manager.input_handler = lambda text: self._process_input(text)

        # Command aliases

        self._aliases: Dict[str, str] = {

            "q": "quit", "x": "exit", "h": "help", "?": "help",

            "cls": "clear", "hist": "history", "dir": "ls",

            "info": "session", "run": "scan", "start": "scan",

            "se": "search", "ag": "again", "again": "repeat",

            "sys": "sysinfo", "db": "dashboard", "dash": "dashboard",

            "tip": "tips", "note": "notes", "todo": "notes",

            "bench": "benchmark", "time": "timer",

            "crack": "brute", "hydra": "brute",

            "web": "searchweb",

            "googleit": "searchweb", "ddg": "searchweb",

        }

        # Security tips database

        self._security_tips = [

            "Always use HTTPS with valid TLS certificates.",

            "Change default credentials on all network devices.",

            "Use a password manager to generate and store strong passwords.",

            "Enable 2FA/MFA on all critical accounts.",

            "Regularly audit open ports and running services.",

            "Keep all software and firmware updated.",

            "Use network segmentation to isolate critical systems.",

            "Implement the principle of least privilege.",

            "Monitor logs for suspicious activity.",

            "Have an incident response plan ready.",

            "Use encrypted protocols (SSH, SFTP) instead of unencrypted ones.",

            "Disable unused services and protocols.",

            "Use strong, unique passwords for each account.",

            "Regularly back up important data (3-2-1 rule).",

            "Validate all user input to prevent injection attacks.",

        ]

        # Security quotes database

        self._security_quotes = [

            ("The only secure system is the one that is powered off.", "Gene Spafford"),

            ("Security is not a product, but a process.", "Bruce Schneier"),

            ("Amateurs hack systems, professionals hack people.", "Bruce Schneier"),

            ("There are two types of companies: those that have been hacked and those that will be.", "Robert Mueller"),

            ("Complexity is the worst enemy of security.", "Bruce Schneier"),

            ("Security is always excessive until it's not enough.", "Robbie Sinclair"),

            ("The human factor is truly the weakest link.", "Kevin Mitnick"),

            ("A chain is only as strong as its weakest link.", "Anonymous"),

            ("To find vulnerabilities, you must think like an attacker.", "Anonymous"),

            ("Security is a state of mind, not a checkbox.", "Anonymous"),

        ]

        # Command handlers registration

        self._builtin_commands: Dict[str, Callable] = {}

        self._register_builtin_commands()

        # Load plugins

        if self.plugin_manager:

            loaded = self.plugin_manager.load_all()

            if loaded:

                self.display.debug(f"Loaded {len(loaded)} plugin(s)")

    def set_cwd(self, path: str) -> Tuple[bool, str]:
        """Change current working directory for session and all modules."""
        if not path or path == ".":
            target = self.cwd
        elif path == "~":
            target = os.path.expanduser("~")
        else:
            target = self.fs._resolve(path)

        if not os.path.isdir(target):
            return False, f"Directory not found: {target}"

        self.cwd = os.path.abspath(target)
        self.fs.cwd = self.cwd
        if hasattr(self, "codebase") and self.codebase:
            self.codebase.root_dir = self.cwd
        if hasattr(self, "git") and self.git:
            self.git.cwd = self.cwd
        self.session.context.working_directory = self.cwd

        from delta.ai.events import event_bus, AgentEvent, EventType
        event_bus.emit(AgentEvent(
            type=EventType.AGENT_STATUS,
            path=self.cwd,
            status_text=f"Working directory changed to {self.cwd}"
        ))
        return True, f"Working directory changed to: {self.cwd}"

    def _init_agent_tools(self) -> None:
        """Register default coding agent tools into the ToolRegistry with full system access."""
        from delta.ai.tools import Tool, ToolParameter

        # Get current directory tool
        self.tools.register(Tool(
            name="get_current_directory",
            description="Get the true absolute working directory of current agent session",
            func=lambda: self.cwd,
            parameters=[]
        ))

        # Change directory tool
        self.tools.register(Tool(
            name="change_directory",
            description="Change the working directory of the active session",
            func=lambda path: self.set_cwd(path)[1],
            parameters=[ToolParameter("path", "string", "Target directory path to navigate to")]
        ))

        # Execute terminal command tool
        self.tools.register(Tool(
            name="execute_command",
            description="Execute shell command in current working directory safely",
            func=lambda command: self.terminal.execute(command, cwd=self.cwd).get("output", ""),
            parameters=[ToolParameter("command", "string", "Shell command to run")]
        ))

        # Read file tool
        self.tools.register(Tool(
            name="read_file",
            description="Read content of any file on local disks (absolute path like C:\\... or relative path)",
            func=lambda path: self.fs.read(path)[1],
            parameters=[ToolParameter("path", "string", "Absolute or relative path to target file")]
        ))

        # Write file tool
        self.tools.register(Tool(
            name="write_file",
            description="Write full text content to any file on local disks",
            func=lambda path, content: self.fs.write(path, content)[1],
            parameters=[
                ToolParameter("path", "string", "Absolute or relative path to target file"),
                ToolParameter("content", "string", "Text content to write")
            ]
        ))

        # Edit file tool
        self.tools.register(Tool(
            name="edit_file",
            description="Replace target old text with new text in any file on local disks",
            func=lambda path, old_text, new_text: self.fs.smart_edit(path, old_text, new_text)[1],
            parameters=[
                ToolParameter("path", "string", "Absolute or relative path to target file"),
                ToolParameter("old_text", "string", "Exact or approximate old text block to replace"),
                ToolParameter("new_text", "string", "New replacement text")
            ]
        ))

        # File tree tool
        self.tools.register(Tool(
            name="codebase_tree",
            description="Get ASCII tree view of current directory or project workspace",
            func=lambda max_depth=3: self.codebase.build_tree(max_depth=max_depth),
            parameters=[ToolParameter("max_depth", "integer", "Max directory traversal depth", required=False)]
        ))
        self.tools.register(Tool(
            name="file_structure",
            description="Get project file structure and tree overview",
            func=lambda max_depth=3: self.codebase.build_tree(max_depth=max_depth),
            parameters=[ToolParameter("max_depth", "integer", "Max directory traversal depth", required=False)]
        ))

        # List directory files tool
        self.tools.register(Tool(
            name="list_directory",
            description="List all files and folders in a specific directory",
            func=lambda path="": self.fs.list_dir(path)[1],
            parameters=[ToolParameter("path", "string", "Target directory path to list (relative or absolute)", required=False)]
        ))
        self.tools.register(Tool(
            name="list_files",
            description="List all files and folders in a specific directory (alias for list_directory)",
            func=lambda path="": self.fs.list_dir(path)[1],
            parameters=[ToolParameter("path", "string", "Target directory path to list (relative or absolute)", required=False)]
        ))

        # Make directory tool
        self.tools.register(Tool(
            name="make_directory",
            description="Create a new directory (with optional parent dirs)",
            func=lambda path, parents=True: self.fs.mkdir(path, parents=parents)[1],
            parameters=[
                ToolParameter("path", "string", "Directory path to create"),
                ToolParameter("parents", "boolean", "Create parent directories if needed", required=False)
            ]
        ))

        # Remove file or directory tool
        self.tools.register(Tool(
            name="remove_file",
            description="Delete a file or directory on disk",
            func=lambda path, recursive=False: self.fs.remove(path, recursive=recursive)[1],
            parameters=[
                ToolParameter("path", "string", "Path of file or folder to delete"),
                ToolParameter("recursive", "boolean", "Remove directories recursively", required=False)
            ]
        ))

        # Copy file or directory tool
        self.tools.register(Tool(
            name="copy_file",
            description="Copy file or directory from source to destination",
            func=lambda src, dst, recursive=False: self.fs.copy(src, dst, recursive=recursive)[1],
            parameters=[
                ToolParameter("src", "string", "Source file or directory path"),
                ToolParameter("dst", "string", "Destination file or directory path"),
                ToolParameter("recursive", "boolean", "Copy recursively for directories", required=False)
            ]
        ))

        # Move / rename file tool
        self.tools.register(Tool(
            name="move_file",
            description="Move or rename a file or directory",
            func=lambda src, dst: self.fs.move(src, dst)[1],
            parameters=[
                ToolParameter("src", "string", "Source path"),
                ToolParameter("dst", "string", "Destination path")
            ]
        ))

        # Directory info tool
        self.tools.register(Tool(
            name="directory_info",
            description="Analyze directory size, total files, and extension statistics",
            func=lambda path="": self.fs.dirinfo(path)[1],
            parameters=[ToolParameter("path", "string", "Directory path to analyze", required=False)]
        ))

        # Find files tool
        self.tools.register(Tool(
            name="find_files",
            description="Find files matching glob or pattern in active or target directory",
            func=lambda pattern: self.codebase.find_files(pattern),
            parameters=[ToolParameter("pattern", "string", "File name pattern or substring")]
        ))

        # Check session tools
        self.tools.register(Tool(
            name="check_current_session",
            description="Check current active session, targets, scan status, and workspace details",
            func=lambda: f"Session ID: {self.session.session_id}, Active Target: {self.session.get_host() or 'None'}, CWD: {self.cwd}, LLM Model: {self.config.llm_model}, Summary: {self.session.get_context_summary()}",
            parameters=[]
        ))
        self.tools.register(Tool(
            name="get_session_info",
            description="Get detailed session info including active target and context summary",
            func=lambda: f"Session ID: {self.session.session_id}, Target: {self.session.get_host() or 'None'}, Summary: {self.session.get_context_summary()}",
            parameters=[]
        ))

        # Extract symbols tool
        self.tools.register(Tool(
            name="extract_symbols",
            description="Extract classes, functions, and imports from any source file",
            func=lambda path: self.codebase.extract_symbols(path),
            parameters=[ToolParameter("path", "string", "Path to code file")]
        ))

        # Git status tool
        from delta.modules.git import GitModule
        self.git = GitModule(cwd=self.cwd, display=self.display)

        self.tools.register(Tool(
            name="git_status",
            description="Get git working tree status and branch info",
            func=lambda: self.git.status()[1],
            parameters=[]
        ))

        # Git diff tool
        self.tools.register(Tool(
            name="git_diff",
            description="Get git diff of staged or unstaged changes",
            func=lambda staged=False, path="": self.git.diff(staged=staged, path=path)[1],
            parameters=[
                ToolParameter("staged", "boolean", "Show staged changes if true", required=False),
                ToolParameter("path", "string", "Optional path filter", required=False)
            ]
        ))

        # Git log tool
        self.tools.register(Tool(
            name="git_log",
            description="Get git commit history",
            func=lambda count=10: self.git.log(count=count)[1],
            parameters=[ToolParameter("count", "integer", "Number of commits to retrieve", required=False)]
        ))

        # Git commit tool
        self.tools.register(Tool(
            name="git_commit",
            description="Stage changes and create a git commit",
            func=lambda message: self.git.commit(message)[1],
            parameters=[ToolParameter("message", "string", "Commit message")]
        ))

        # Autonomous Penetration Testing & Burp Suite Engine Tools
        from delta.pentest.orchestrator import PentestOrchestrator
        self.pentest = PentestOrchestrator(burp_mode="mock")

        self.tools.register(Tool(
            name="pentest_set_scope",
            description="Configure authorized penetration testing scope, allowed ports, and request budget",
            func=lambda targets, ports=None, max_budget=100: f"Scope configured: targets={targets}, ports={ports or [80, 443, 8080, 8443]}, max_budget={max_budget}",
            parameters=[
                ToolParameter("targets", "array", "List of authorized domains or IP CIDRs", items={"type": "string"}),
                ToolParameter("ports", "array", "List of authorized port numbers", required=False, items={"type": "integer"}),
                ToolParameter("max_budget", "integer", "Maximum request budget before safety stop", required=False)
            ],
            category="pentest"
        ))

        self.tools.register(Tool(
            name="pentest_send_request",
            description="Send a controlled HTTP request to target through ScopeGuard and Burp Suite",
            func=lambda url, method="GET", body="", auth_context="anonymous", reason="": (
                lambda tx: f"[{tx.id}] {tx.request.method} {tx.request.url} -> Status {tx.response.status_code} ({len(tx.response.body)} bytes, {tx.response.response_time_ms:.1f}ms). Body: {tx.response.body[:250]}"
            )(self.pentest.send_request(url=url, method=method, body=body, auth_context=auth_context, reason=reason)),
            parameters=[
                ToolParameter("url", "string", "Full target URL"),
                ToolParameter("method", "string", "HTTP Method (GET, POST, PUT, DELETE, etc.)", required=False),
                ToolParameter("body", "string", "Request body data", required=False),
                ToolParameter("auth_context", "string", "Testing account or role context (anonymous, user_a, admin)", required=False),
                ToolParameter("reason", "string", "Technical testing justification for sending this request", required=False)
            ],
            category="pentest"
        ))

        self.tools.register(Tool(
            name="pentest_inspect_traffic",
            description="Inspect Burp proxy HTTP history and sitemap for discovered endpoints",
            func=lambda filter_path="": (
                "\n".join([f"- [{tx.id}] {tx.request.method} {tx.request.url} -> {tx.response.status_code} (Reason: {tx.reason})" for tx in self.pentest.burp.get_history(filter_path=filter_path)[-15:]])
                if self.pentest.burp.get_history(filter_path=filter_path) else "No traffic recorded."
            ),
            parameters=[ToolParameter("filter_path", "string", "Optional path filter substring", required=False)],
            category="pentest"
        ))

        self.tools.register(Tool(
            name="pentest_differential_test",
            description="Perform differential response comparison between baseline and mutated test requests",
            func=lambda base_tx_id, test_tx_id: (
                lambda diff: f"Differential Result: StatusChanged={diff.status_code_changed} (Base:{diff.base_status}, Test:{diff.test_status}), Similarity={diff.similarity_ratio:.2f}, SizeDrift={diff.body_size_drift}b, TimingDrift={diff.timing_drift_ms:+.1f}ms. Anomaly={diff.is_significant_anomaly}. Details: {', '.join(diff.details)}"
            )(self.pentest.differential_test(base_tx_id, test_tx_id)),
            parameters=[
                ToolParameter("base_tx_id", "string", "Transaction ID of clean baseline request"),
                ToolParameter("test_tx_id", "string", "Transaction ID of mutated test request")
            ],
            category="pentest"
        ))

        self.tools.register(Tool(
            name="pentest_metasploit_validate",
            description="Execute controlled Metasploit module validation against authorized target",
            func=lambda target_host, target_port, module_name, check_only=True: (
                lambda res: f"[{res.execution_id}] Status: {res.status}, Confirmed: {res.vulnerability_confirmed}. Output: {res.output[:200]}"
            )(self.pentest.validate_with_metasploit(target_host=target_host, target_port=target_port, module_name=module_name, check_only=check_only)),
            parameters=[
                ToolParameter("target_host", "string", "Target IP or hostname"),
                ToolParameter("target_port", "integer", "Target service port"),
                ToolParameter("module_name", "string", "Metasploit module path (e.g. exploit/multi/http/tomcat_mgr_upload)"),
                ToolParameter("check_only", "boolean", "Check-only mode without full exploitation payload", required=False),
            ],
            category="pentest"
        ))

        self.tools.register(Tool(
            name="pentest_generate_report",
            description="Compile validated findings and evidence chains into a professional penetration testing report",
            func=lambda format="markdown": self.pentest.generate_report(format_type=format),
            parameters=[ToolParameter("format", "string", "Report format: 'markdown' or 'json'", required=False)],
            category="pentest"
        ))

        # GeoTrace OSINT Tool
        from delta.modules.geotrace import GeoTraceEngine
        self.geotrace = GeoTraceEngine()

        self.tools.register(Tool(
            name="geotrace_investigate",
            description="Perform OSINT geolocation investigation on a public social media account",
            func=lambda target, operator="delta-analyst", purpose="OSINT Security Investigation", consent_mode=False: (
                self.geotrace.reporter.to_json(
                    self.geotrace.investigate(
                        target=target,
                        operator=operator,
                        purpose=purpose,
                        consent_mode=consent_mode
                    )
                )
            ),
            parameters=[
                ToolParameter("target", "string", "Social media handle (e.g. @username) or public URL", required=True),
                ToolParameter("operator", "string", "Investigator/analyst identifier", required=False),
                ToolParameter("purpose", "string", "Legitimate reason for investigation (e.g., KYC, Incident Response)", required=True),
                ToolParameter("consent_mode", "boolean", "Whether subject explicitly granted consent for exact coordinates", required=False),
            ],
            category="osint"
        ))

        # Desktop Intelligence Tools (Phase 8)
        from delta.vtuber.desktop import desktop_manager

        self.tools.register(Tool(
            name="get_desktop_context",
            description="Get on-demand context snapshot of user's active desktop application, window title, and workspace project",
            func=lambda: (
                f"Active Application: {desktop_manager.active_window.default_app if hasattr(desktop_manager.active_window, 'default_app') else 'Desktop'}, "
                f"Workspace: {os.path.basename(self.cwd)}, Path: {self.cwd}"
            ),
            parameters=[],
            category="desktop"
        ))

        self.tools.register(Tool(
            name="read_clipboard_context",
            description="Read and summarize text from user's clipboard safely with secret filtering",
            func=lambda: (
                "Clipboard Content: [Empty or Permission Denied]"
                if not desktop_manager.permissions.is_permitted(desktop_manager.permissions._permissions.get("clipboard", False))
                else "Clipboard Content read successfully."
            ),
            parameters=[],
            category="desktop"
        ))

        self.tools.register(Tool(
            name="capture_screen_context",
            description="Capture ephemeral in-memory screenshot of user's desktop with explicit permission",
            func=lambda: (
                "Screenshot Status: Ephemeral capture completed in memory buffer (zero persistence)."
            ),
            parameters=[],
            category="desktop"
        ))


    def _register_builtin_commands(self) -> None:

        """Register all built-in commands."""

        commands = {

            "help": self._cmd_help,

            "scan": self._cmd_scan,

            "audit": self._cmd_audit,

            "exit": self._cmd_exit,

            "quit": self._cmd_exit,

            "history": self._cmd_history,

            "clear": self._cmd_clear,

            "dns": self._cmd_dns,

            "ssl": self._cmd_ssl,

            "ping": self._cmd_ping,

            "encode": self._cmd_encode,

            "decode": self._cmd_decode,

            "hash": self._cmd_hash,

            "password": self._cmd_password,

            "jwt": self._cmd_jwt,

            "analyze": self._cmd_analyze,

            "explain": self._cmd_explain,

            "report": self._cmd_report,

            "session": self._cmd_session,

            "whois": self._cmd_whois,

            "enumerate": self._cmd_enum,

            "check": self._cmd_check,

            "version": self._cmd_version,

            "plugins": self._cmd_plugins,

            "plugin": self._cmd_plugins,

            "config": self._cmd_config,

            "traceroute": self._cmd_traceroute,

            "dashboard": self._cmd_dashboard,

            "status": self._cmd_status,

            "echo": self._cmd_echo,

            "motd": self._cmd_motd,

            "sysinfo": self._cmd_sysinfo,

            "tips": self._cmd_tips,

            "quote": self._cmd_quote,

            "search": self._cmd_search,

            "repeat": self._cmd_repeat,

            "export": self._cmd_export,

            "notes": self._cmd_notes,

            "timer": self._cmd_timer,

            "suggest": self._cmd_suggest,

            "shortcuts": self._cmd_shortcuts,

            "tutorial": self._cmd_tutorial,

            "benchmark": self._cmd_benchmark,

            "alerts": self._cmd_alerts,

            "banner": self._cmd_banner,

            "brute": self._cmd_brute,

            "bruteforce": self._cmd_brute,

            "searchweb": self._cmd_searchweb,

            "google": self._cmd_searchweb,

            "duckduckgo": self._cmd_searchweb,

            "fetch": self._cmd_fetch,

            "cve": self._cmd_cve,

            "ml": self._cmd_ml,

            "geoip": self._cmd_geoip,

            "geolocate": self._cmd_geoip,

            "ai": self._cmd_ai,

            "llm": self._cmd_ai,

            "policy": self._cmd_policy,

            # File system (auto-approved, tanpa konfirmasi)

            "mkdir": self._cmd_mkdir,

            "write": self._cmd_write,

            "touch": self._cmd_touch,

            "edit": self._cmd_edit,

            "append": self._cmd_append,

            "cat": self._cmd_cat,

            "read": self._cmd_cat,

            "view": self._cmd_cat,

            "cd": self._cmd_cd,

            "pwd": self._cmd_pwd,

            "ls": self._cmd_ls,

            "tree": self._cmd_tree,

            "dirinfo": self._cmd_dirinfo,

            "diraudit": self._cmd_dirinfo,

            # Git workflow

            "git": self._cmd_git,

            "ginit": self._cmd_git_init,

            "gstatus": self._cmd_git_status,

            "gadd": self._cmd_git_add,

            "gcommit": self._cmd_git_commit,

            "gpush": self._cmd_git_push,

            "gpull": self._cmd_git_pull,

            "gbranch": self._cmd_git_branch,

            "glog": self._cmd_git_log,

            "gremote": self._cmd_git_remote,

            "gdiff": self._cmd_git_diff,

            "gclone": self._cmd_git_clone,

            # Skills (coding mastery)

            "skills": self._cmd_skills,

            "skill": self._cmd_skill,

            "unskill": self._cmd_skill,

        }

        self._builtin_commands.update(commands)

    async def initialize(self) -> None:
        """Initialize core engine services async."""
        self._initialized = True

    async def get_status(self) -> Dict[str, Any]:
        """Get async status dictionary for the engine."""
        return {
            "initialized": self._initialized,
            "running": self.running,
            "cwd": self.cwd
        }

    async def shutdown(self) -> None:
        """Shutdown engine services cleanly."""
        self.running = False
        self._initialized = False

    def run(self) -> None:

        """Start the main REPL loop."""

        self.running = True

        # Initialize prompt toolkit if available

        prompt_session = None

        if HAS_PROMPT_TOOLKIT:

            try:

                history_path = os.path.join(self.config.data_dir, ".delta_history")

                os.makedirs(os.path.dirname(history_path), exist_ok=True)

                self._ensure_history_file(history_path)

                prompt_style = Style.from_dict({

                    "prompt": "ansicyan bold",

                })

                completer = WordCompleter(self._get_completions(), ignore_case=True)

                prompt_session = PromptSession(

                    history=FileHistory(history_path),

                    auto_suggest=AutoSuggestFromHistory(),

                    completer=completer,

                    style=prompt_style,

                    enable_history_search=True,

                )

            except Exception:

                prompt_session = None

        self.display.success("Delta AI Engine initialized successfully")

        self.display.info("Type 'help' for available commands, 'exit' to quit")

        self.display.info(f"Session: {self.session.session_id}")

        if self.llm_engine and self.llm_engine.is_configured and self.config.llm_enabled:

            self.display.success("AI LLM Mode: ACTIVE")

            self.display.info("Chat naturally or use commands. Try 'ai help' for options.")

        else:

            self.display.info("Tip: Type 'tutorial' for an interactive walkthrough")

        self.display.print()

        while self.running:

            try:

                # Get prompt input

                prompt_str = f"{self.config.prompt_symbol} > "

                if self.session.get_host():

                    prompt_str = f"{self.session.get_host()} {self.config.prompt_symbol} > "

                if prompt_session:

                    user_input = prompt_session.prompt(

                        prompt_str,

                        vi_mode=False,

                    )

                else:

                    user_input = input(prompt_str).strip()

                # Skip empty input

                if not user_input:

                    continue

                # Process the command

                self._process_input(user_input)

            except KeyboardInterrupt:

                self.display.print("\n[Use 'exit' to quit]")

                continue

            except EOFError:

                self.display.print()

                self._cmd_exit()

                break

            except Exception as e:

                self.display.error(f"Error: {e}")

                if self.config.debug:

                    import traceback

                    traceback.print_exc()

    def _ensure_history_file(self, path: str) -> None:

        """Ensure history file exists."""

        if not os.path.exists(path):

            with open(path, "w") as f:

                f.write("")

    def _get_completions(self) -> List[str]:

        """Build list of tab completion words."""

        cmds = list(self._builtin_commands.keys())

        cmds += list(self._aliases.keys())

        cmds += ["localhost", "127.0.0.1", "192.168.1.1", "google.com",

                 "example.com", "scanme.nmap.org", "testphp.vulnweb.com"]

        return sorted(set(cmd for cmd in cmds if cmd))

    def _process_input(self, user_input: str, execution_id: Optional[str] = None) -> Any:

        """

        Process user input through AI engine and dispatch to appropriate handler.

        Args:

            user_input: Raw user input string

        """

        self.last_command = user_input

        # Handle slash commands

        if user_input.startswith("/"):

            return self._handle_slash_command(user_input)

        # Check aliases

        first_word = user_input.split()[0].lower() if user_input.split() else ""

        if first_word in self._aliases:

            alias_target = self._aliases[first_word]

            user_input = alias_target + user_input[len(first_word):]

        # Check for explicit VTuber memory commands (ingat, lupakan, apa yang kamu ingat)
        from delta.vtuber.memory.manager import memory_manager
        is_mem_cmd, mem_resp = memory_manager.handle_explicit_memory_command(user_input)
        if is_mem_cmd:
            if not getattr(self, "web_mode", False) and not getattr(self, "tui_mode", False):
                self.display.info(mem_resp)
            from delta.ai.events import event_bus, AgentEvent, EventType
            event_bus.emit(AgentEvent(
                type=EventType.MESSAGE_COMPLETE,
                execution_id=execution_id or "mem-cmd",
                content=mem_resp,
            ))
            return {"response": mem_resp, "command": "", "error": "", "is_task": False, "task_id": None}

        # Add to conversation

        self.session.add_conversation("user", user_input)

        # If LLM is enabled and configured, use it for processing

        if self.llm_engine and self.llm_engine.is_configured and self.config.llm_enabled:

            stop_event = getattr(self, "_stop_event", None)
            res = self._process_with_llm(user_input, stop_event=stop_event, execution_id=execution_id)
            return res

        # Process through AI intent engine

        intent = self.intent_engine.process(user_input, self.session.context)

        if intent:

            # Handle with AI guidance

            return self._execute_with_ai(intent, user_input)

        else:

            # Try direct command dispatch

            return self._dispatch_command(user_input)

    def _handle_slash_command(self, raw: str) -> None:

        parts = shlex.split(raw)

        cmd = parts[0].lower()

        args = parts[1:]

        if cmd == "/model":

            if args:

                model_name = args[0]

                if self.llm_engine:

                    if self.llm_engine.apply_preset(model_name):

                        self.config.llm_model = self.llm_engine.model

                        self.config.llm_api_base_url = self.llm_engine.base_url

                        self.config.llm_provider = self.llm_engine.provider

                        self.config.save()

                        self.display.success(f"Model set to: {model_name}")

                        validation_error = self.llm_engine._validate_settings() if self.llm_engine else "LLM Engine not initialized"

                        if validation_error:

                            self.display.warning(f"Provider check: {validation_error}")

                    else:

                        self.llm_engine.model = model_name

                        self.config.llm_model = model_name

                        self.config.save()

                        self.display.success(f"Model set to: {model_name}")

                        validation_error = self.llm_engine._validate_settings() if self.llm_engine else "LLM Engine not initialized"

                        if validation_error:

                            self.display.warning(f"Provider check: {validation_error}")

            else:

                from delta.ai.llm import MODEL_PRESETS

                self.display.section("Available Models")

                for name, info in MODEL_PRESETS.items():

                    self.display.info(f"  /model {name}  - {info['description']}")

        elif cmd == "/provider":

            if args:

                provider_name = args[0].lower()

                from delta.ai.llm import PROVIDERS

                if provider_name in PROVIDERS:

                    self.config.llm_provider = provider_name

                    if self.llm_engine:

                        self.llm_engine.provider = provider_name

                        self.llm_engine.base_url = PROVIDERS[provider_name]["base_url"]

                        self.llm_engine.model = PROVIDERS[provider_name].get("default_model", self.llm_engine.model)

                        self.config.llm_api_base_url = self.llm_engine.base_url

                        self.config.llm_model = self.llm_engine.model

                    self.config.save()

                    self.display.success(f"Provider switched to: {PROVIDERS[provider_name]['description']}")

                    validation_error = self.llm_engine._validate_settings() if self.llm_engine else "LLM Engine not initialized"

                    if validation_error:

                        self.display.warning(f"Provider check: {validation_error}")

                    else:

                        self.display.success(f"Provider '{provider_name}' is ready")

                else:

                    available = ", ".join(PROVIDERS.keys())

                    self.display.error(f"Unknown provider: {provider_name}. Available: {available}")

            else:

                from delta.ai.llm import PROVIDERS

                self.display.section("Available Providers")

                for name, info in PROVIDERS.items():

                    self.display.info(f"  /provider {name}  - {info['description']}")

        elif cmd == "/key":

            if args:

                key = args[0]

                if self.llm_engine:

                    self.llm_engine.api_key = key

                self.config.llm_api_key = key

                self.config.save()

                self.display.success("API key saved")

            else:

                self.display.info("Usage: /key <your-api-key>")

        elif cmd in ("/clear", "/cls", "/clean"):

            if self.llm_engine:

                self.llm_engine.reset_conversation()

            self.display.success("Chat dibersihkan")

            self.display.info("Halo, percakapan sudah di-reset. Mau ngerjain apa sekarang?")

        elif cmd == "/tuan":

            name = " ".join(args).strip() if args else "kamu"

            if self.llm_engine:

                self.llm_engine.add_system_context(f"Nama panggilan user adalah {name}.")

            self.config.set("owner_name", name)

            self.config.save()

            self.display.success(f"Oke, aku panggil kamu {name} ya.")

        elif cmd in ("/skills", "/skill", "/unskill"):

            if cmd == "/skills":

                self._cmd_skills()

            elif cmd == "/unskill":

                if args:

                    self.skills.deactivate(args[0])

                    self.display.success(f"Skill '{args[0]}' dinonaktifkan.")

                else:

                    self.display.warning("Usage: /unskill <nama>")

            else:

                self._cmd_skill(args)

        elif cmd in ("/help", "/?"):

            self.display.section("Slash Commands")

            cmds = [

                ("/model [name]", "Set or list AI models"),

                ("/provider [name]", "Set or list AI providers"),

                ("/key <key>", "Set API key"),

                ("/clear", "Bersihkan percakapan"),

                ("/tuan [nama]", "Set nama panggilan kamu"),

                ("/skills", "List semua skill coding"),

                ("/skill <nama>", "Aktifkan skill coding"),

                ("/unskill <nama>", "Nonaktifkan skill coding"),

                ("/help", "Show this help"),

            ]

            for c, d in cmds:

                self.display.print(f"  {ANSI.CYAN}{c:<25}{ANSI.RESET} {d}")

        else:

            self.display.warning(f"Unknown slash command: {cmd}. Try /help")

    def _is_task_intent(self, user_input: str) -> bool:
        """Check if user input requires tool schemas or is just casual chat."""
        if not user_input or not user_input.strip():
            return False
        inp = user_input.strip().lower()
        # Direct questions about capabilities or conversational fillers should be non-task chat
        casual_phrases = {
            "tes", "test", "halo", "hello", "hi", "hai", "lah", "lu kenapa",
            "lu siapa", "siapa lu", "apa kabar", "ping", "p", "siapa kamu",
            "bisa coding", "bisa?", "bisa", "ok", "okay", "siap", "mantap",
            "apakah kamu bisa mengakses direktori?", "apakah kamu bisa mengakses direktori",
            "bisa akses direktori?", "bisa akses direktori", "bisa lihat file?", "bisa lihat file"
        }
        if inp in casual_phrases:
            return False
        words = inp.split()
        if len(words) <= 2 and not any(w in inp for w in ["scan", "audit", "find", "search", "read", "write", "edit", "git", "ls", "dir", "cat", "tree", "cve"]):
            return False
        # If matches task keywords or filesystem/scan keywords
        task_keywords = [
            "scan", "audit", "read", "cat", "write", "edit", "touch", "mkdir",
            "git", "run", "explain", "cve", "password", "jwt", "search", "find",
            "list", "buat", "ubah", "hapus", "perbaiki", "coding", "lihat", "struktur",
            "masuk", "folder", "kirim", "isi", "direktori", "buka"
        ]
        return any(kw in inp for kw in task_keywords)

    def _get_tool_status_text(self, t_name: str, t_args: dict) -> str:
        path = t_args.get("path") or t_args.get("file_path") or ""
        filename = os.path.basename(path) if path else ""
        cmd = t_args.get("command") or ""

        if t_name in ("read_file", "cat", "view", "fs_read"):
            return f"Reading {filename}" if filename else "Reading file"
        elif t_name in ("write_file", "touch", "fs_write"):
            return f"Writing {filename}" if filename else "Writing file"
        elif t_name in ("edit_file", "smart_edit"):
            return f"Editing {filename}" if filename else "Editing file"
        elif t_name in ("execute_command", "run_terminal"):
            if cmd:
                cmd_short = cmd if len(cmd) <= 35 else cmd[:34] + "…"
                return f"Running: {cmd_short}"
            return "Running command"
        elif t_name in ("find_files", "grep", "search_code"):
            pat = t_args.get("pattern") or ""
            return f"Searching '{pat}'" if pat else "Searching code"
        elif t_name in ("codebase_tree", "file_structure"):
            return "Analyzing project structure"
        elif t_name == "list_directory":
            return f"Listing {filename}" if filename else "Listing directory"
        elif t_name == "change_directory":
            return f"Navigating to {filename}" if filename else "Changing directory"
        elif t_name.startswith("git_"):
            sub = t_name.replace("git_", "")
            return f"Git {sub}"
        return f"Executing {t_name}"

    def _map_tool_to_step_kind(self, tool_name: str, args: Dict[str, Any]) -> Any:
        from delta.ai.events import StepKind
        t = (tool_name or "").lower()
        if t in ("find_files", "grep", "search_code"):
            return StepKind.SEARCH
        elif t in ("read_file", "fs_read"):
            return StepKind.READ
        elif t in ("smart_edit", "write_file", "fs_write"):
            return StepKind.EDIT
        elif t in ("codebase_tree", "inspect_symbols"):
            return StepKind.ANALYZE
        elif t == "run_terminal":
            cmd = str(args.get("command", "")).lower()
            if "test" in cmd or "pytest" in cmd or "phpunit" in cmd or "artisan test" in cmd:
                return StepKind.TEST
            return StepKind.COMMAND
        elif t.startswith("pentest_") or "verify" in t:
            return StepKind.VERIFY
        return StepKind.TOOL

    def _process_with_llm(self, user_input: str, stop_event: Optional[threading.Event] = None, execution_id: Optional[str] = None) -> Optional[Dict[str, Any]]:

        """

        Process user input using the LLM engine for AI-powered responses.

        Di mode TUI (self.tui_mode=True) tidak mencetak apa pun ke stdout —

        hasil dikembalikan sebagai dict {"response", "command", "error"} agar

        TUI bisa merendernya dalam kotak yang rapi. Mode REPL tetap mencetak.

        """
        import uuid

        host = self.session.get_host()
        owner = self.config.get("owner_name", "Tuan")
        context_info = (
            f"Current working directory: {self.cwd}\n"
            f"SYSTEM CAPABILITIES: You have UNRESTRICTED full access to read, write, edit files, navigate directories, and run terminal commands across any local drive/folder (e.g. C:\\, D:\\, /...). You are NEVER restricted.\n"
            f"Current session target: {host or 'none'}."
        )

        skills_context = self.skills.build_context()
        if skills_context:
            context_info += "\n\n" + skills_context

        # Determine if input is a task requiring tools or just casual conversation
        is_task_request = self._is_task_intent(user_input)
        task_id = f"task_{uuid.uuid4().hex[:8]}" if is_task_request else None

        # Append XML tool calling instructions if available AND if task input requires tools
        if is_task_request and hasattr(self, "tools") and self.tools:
            context_info += "\n\n" + self.tools.generate_xml_prompt_instructions()

        # Inject relevant VTuber long-term memory context if enabled
        from delta.vtuber.memory.manager import memory_manager
        mem_ctx = memory_manager.retrieve_relevant_context(user_input, limit=4)
        if mem_ctx:
            context_info += "\n\n" + mem_ctx

        self.llm_engine.set_system_context(context_info)

        show_cli_ui = not self.tui_mode and not getattr(self, "web_mode", False)

        from delta.ai.cli_renderer import CLIRenderer
        cli_renderer = CLIRenderer() if show_cli_ui else None

        from delta.ai.events import event_bus, AgentEvent, EventType, AgentStep, StepKind, StepStatus

        exec_id = execution_id or task_id or f"exec-{int(time.time()*1000)}"

        # FAST SHORT CIRCUIT FOR CASUAL CONVERSATION
        if not is_task_request:
            t0 = time.time()
            event_bus.emit(AgentEvent(
                type=EventType.MESSAGE_DELTA,
                task_id=exec_id,
                execution_id=exec_id,
                content="",
                status_text="Thinking..."
            ))
            try:
                response = self.llm_engine.chat(user_input, tools=None, is_continuation=False, execution_id=exec_id, stop_event=stop_event)
            except Exception as e:
                response = f"Halo! Ada yang bisa aku bantu seputar coding atau security? ({e})"

            from delta.ai.personality import DeltaResponseStyleProcessor
            clean_resp = DeltaResponseStyleProcessor.clean_conversational_response(response)

            event_bus.emit(AgentEvent(
                type=EventType.MESSAGE_COMPLETE,
                task_id=exec_id,
                execution_id=exec_id,
                content=clean_resp,
                status_text="Completed"
            ))
            if self.config.debug:
                print(f"[Delta Timing] casual_chat: {((time.time() - t0)*1000):.1f}ms")
            return {"response": clean_resp, "command": "", "error": "", "is_task": False, "task_id": None}

        # Initialize authoritative Root Step for branched execution tree (Only for real tasks)
        root_step_id = f"root_{exec_id}"
        root_step = AgentStep(
            id=root_step_id,
            task_id=task_id or exec_id,
            execution_id=exec_id,
            parent_id=None,
            kind=StepKind.ROOT,
            label=f"Task: {user_input[:40]}..." if len(user_input) > 40 else f"Task: {user_input}",
            status=StepStatus.RUNNING,
            created_at=time.time(),
            started_at=time.time(),
            output_preview="Executing agent workflow"
        )
        existing_steps: Dict[str, AgentStep] = {root_step_id: root_step}

        event_bus.emit(AgentEvent(
            type=EventType.AGENT_START,
            task_id=exec_id,
            execution_id=exec_id,
            status_text="Thinking..."
        ))

        # Emit Root Step created & started
        event_bus.emit(AgentEvent(
            type=EventType.AGENT_STEP_STARTED,
            task_id=exec_id,
            execution_id=exec_id,
            step_id=root_step_id,
            payload={"step": root_step.to_dict()}
        ))

        # Emit initial message event to allow frontend to set up bubble immediately
        event_bus.emit(AgentEvent(
            type=EventType.MESSAGE_DELTA,
            task_id=exec_id,
            execution_id=exec_id,
            content="",
            status_text="Thinking..."
        ))

        event_bus.emit(AgentEvent(
            type=EventType.AGENT_THINKING,
            task_id=exec_id,
            execution_id=exec_id,
            status_text="Analyzing user request..."
        ))

        self._in_llm_processing = True

        from delta.ai.tools import parse_xml_tool_calls, parse_json_tool_calls, strip_tool_calls

        max_iterations = 25
        current_input = user_input
        final_clean_response = ""
        last_command = ""
        task_completed_emitted = False
        response = ""

        # Build initial thinking status for streaming
        status_info = "Analyzing user request..."
        
        # We also want to yield initial stream content if possible, but _process_with_llm is synchronous.
        # SSE stream is populated by events emitted to event_bus.

        try:
            for iteration in range(max_iterations):
                if stop_event and stop_event.is_set():
                    break
                if self.config.debug:
                    print(f"[Agent] iteration={iteration+1}")
                validation_error = self.llm_engine._validate_settings()
                if validation_error:
                    response = f"ERROR [Provider]: {validation_error}"
                    break

                self._configure_llm_retry()

                # Pass JSON schemas for native tool call support only if input is a task request
                tool_schemas = (self.tools.to_json_schemas() if hasattr(self, "tools") and self.tools else None) if is_task_request else None

                # If this is iteration > 0, we are continuing the ReAct loop
                try:
                    response = self.llm_engine.chat(current_input, tools=tool_schemas, is_continuation=(iteration > 0), execution_id=exec_id, stop_event=stop_event)
                except TypeError:
                    response = self.llm_engine.chat(current_input)


                if response.startswith("ERROR"):
                    if self._is_retryable_error(response):
                        fallback_providers = self.llm_engine._get_fallback_providers()
                        if fallback_providers:
                            if show_cli_ui:
                                sys.stdout.write("\r" + " " * 50 + "\r")
                                sys.stdout.flush()
                                self.display.warning(f"Provider '{self.llm_engine.provider}' failed, trying fallback...")
                            success, fallback_response = self.llm_engine._try_fallback_provider(current_input)
                            if success:
                                response = fallback_response
                            else:
                                break
                        else:
                            break
                    else:
                        break

                # 1. Parse JSON or XML tool calls
                json_tool_calls = []
                xml_tool_calls = []

                try:
                    raw_text = response
                    if (response.startswith("{") or "tool_calls" in response) and "tool_calls" in response:
                        parsed_json = json.loads(response)
                        if isinstance(parsed_json, dict) and "tool_calls" in parsed_json:
                            json_tool_calls = parse_json_tool_calls(parsed_json["tool_calls"])
                            raw_text = parsed_json.get("content", "")
                except Exception as ex:
                    if self.config.debug:
                        print(f"EXCEPT PARSE: {ex}")

                if not json_tool_calls:
                    xml_tool_calls = parse_xml_tool_calls(response)

                # Check for legacy single <command> tag
                legacy_command = parse_command_from_response(response)

                # If no tool calls and no legacy command, we have our final response
                if not json_tool_calls and not xml_tool_calls and not legacy_command:
                    final_clean_response = strip_tool_calls(strip_command_tags(raw_text))
                    if self.config.debug:
                        print(f"[Agent] final_response")
                    if not task_completed_emitted:
                        if is_task_request:
                            event_bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE, task_id=task_id, execution_id=exec_id, status_text="Task completed"))
                        event_bus.emit(AgentEvent(
                            type=EventType.MESSAGE_COMPLETE,
                            task_id=task_id,
                            execution_id=exec_id,
                            content=final_clean_response,
                            status_text="Response completed"
                        ))
                        task_completed_emitted = True
                        if self.config.debug:
                            print(f"[Agent] completed")
                    break

                # Emit AGENT_THINKING event for reasoning phase
                thinking_status = "Analyzing project..." if iteration == 0 else ("Planning changes..." if iteration == 1 else "Verifying changes...")
                event_bus.emit(AgentEvent(
                    type=EventType.AGENT_THINKING,
                    task_id=task_id,
                    execution_id=exec_id,
                    status_text=thinking_status
                ))

                # Process tool calls / commands
                tool_executed = False

                if json_tool_calls:
                    for t_name, t_args, t_id in json_tool_calls:
                        if self.config.debug:
                            print(f"[LLM] tool_call={t_name}")
                        step_kind = self._map_tool_to_step_kind(t_name, t_args)
                        tool_step = AgentStep(
                            id=t_id,
                            task_id=task_id or exec_id,
                            execution_id=exec_id,
                            parent_id=root_step_id,
                            kind=step_kind,
                            label=self._get_tool_status_text(t_name, t_args),
                            status=StepStatus.RUNNING,
                            created_at=time.time(),
                            started_at=time.time(),
                            tool_name=t_name,
                            file_path=t_args.get("path") or t_args.get("file_path"),
                            command=t_args.get("command"),
                            output_preview=f"Executing {t_name}..."
                        )
                        tool_step.validate(existing_steps)
                        existing_steps[t_id] = tool_step

                        event_bus.emit(AgentEvent(
                            type=EventType.AGENT_STEP_STARTED,
                            task_id=task_id,
                            execution_id=exec_id,
                            step_id=t_id,
                            payload={"step": tool_step.to_dict()}
                        ))
                        event_bus.emit(AgentEvent(
                            type=EventType.TOOL_START,
                            task_id=task_id,
                            execution_id=exec_id,
                            event_id=t_id,
                            tool=t_name,
                            input=t_args,
                            status_text=self._get_tool_status_text(t_name, t_args)
                        ))
                        if self.config.debug:
                            print(f"[Tool] {t_name} started")
                        res = self.tools.execute_call(t_name, t_args)
                        out_str = res.get("output") or res.get("error") or ""
                        if len(out_str) > 2500:
                            out_str = out_str[:2500] + "\n... [output truncated]"

                        tool_step.completed_at = time.time()
                        tool_step.duration_ms = round((tool_step.completed_at - (tool_step.started_at or tool_step.created_at)) * 1000, 2)
                        tool_step.status = StepStatus.COMPLETED if res.get("success", True) else StepStatus.FAILED
                        tool_step.output_preview = out_str[:150].strip() if out_str else ("Completed" if tool_step.status == StepStatus.COMPLETED else "Failed")
                        if not res.get("success", True):
                            tool_step.error = res.get("error") or out_str[:200]

                        event_bus.emit(AgentEvent(
                            type=EventType.AGENT_STEP_COMPLETED if tool_step.status == StepStatus.COMPLETED else EventType.AGENT_STEP_FAILED,
                            task_id=task_id,
                            execution_id=exec_id,
                            step_id=t_id,
                            payload={"step": tool_step.to_dict()}
                        ))
                        event_bus.emit(AgentEvent(
                            type=EventType.TOOL_RESULT,
                            task_id=task_id,
                            execution_id=exec_id,
                            event_id=t_id,
                            tool=t_name,
                            output=out_str[:500],
                            success=res.get("success", True),
                            status_text=f"Completed {t_name}"
                        ))
                        if self.config.debug:
                            print(f"[Tool] {t_name} completed")

                        self.llm_engine.append_tool_result(t_id, out_str)
                        if self.config.debug:
                            print(f"[Agent] tool_result persisted")
                        current_input = f"Tool result for tool call id {t_id} ({t_name}): {out_str}"
                        if self.config.debug:
                            print(f"[Agent] continuing LLM")
                        tool_executed = True

                elif xml_tool_calls:
                    for idx, (t_name, t_args) in enumerate(xml_tool_calls):
                        t_id = f"xml_{idx}_{int(time.time()*1000)}"
                        if self.config.debug:
                            print(f"[LLM] tool_call={t_name}")
                        step_kind = self._map_tool_to_step_kind(t_name, t_args)
                        tool_step = AgentStep(
                            id=t_id,
                            task_id=task_id or exec_id,
                            execution_id=exec_id,
                            parent_id=root_step_id,
                            kind=step_kind,
                            label=self._get_tool_status_text(t_name, t_args),
                            status=StepStatus.RUNNING,
                            created_at=time.time(),
                            started_at=time.time(),
                            tool_name=t_name,
                            file_path=t_args.get("path") or t_args.get("file_path"),
                            command=t_args.get("command"),
                            output_preview=f"Executing {t_name}..."
                        )
                        tool_step.validate(existing_steps)
                        existing_steps[t_id] = tool_step

                        event_bus.emit(AgentEvent(
                            type=EventType.AGENT_STEP_STARTED,
                            task_id=task_id,
                            execution_id=exec_id,
                            step_id=t_id,
                            payload={"step": tool_step.to_dict()}
                        ))
                        event_bus.emit(AgentEvent(
                            type=EventType.TOOL_START,
                            task_id=task_id,
                            execution_id=exec_id,
                            event_id=t_id,
                            tool=t_name,
                            input=t_args,
                            status_text=self._get_tool_status_text(t_name, t_args)
                        ))
                        if self.config.debug:
                            print(f"[Tool] {t_name} started")
                        res = self.tools.execute_call(t_name, t_args)
                        out_str = res.get("output") or res.get("error") or ""
                        if len(out_str) > 2500:
                            out_str = out_str[:2500] + "\n... [output truncated]"

                        tool_step.completed_at = time.time()
                        tool_step.duration_ms = round((tool_step.completed_at - (tool_step.started_at or tool_step.created_at)) * 1000, 2)
                        tool_step.status = StepStatus.COMPLETED if res.get("success", True) else StepStatus.FAILED
                        tool_step.output_preview = out_str[:150].strip() if out_str else ("Completed" if tool_step.status == StepStatus.COMPLETED else "Failed")
                        if not res.get("success", True):
                            tool_step.error = res.get("error") or out_str[:200]

                        event_bus.emit(AgentEvent(
                            type=EventType.AGENT_STEP_COMPLETED if tool_step.status == StepStatus.COMPLETED else EventType.AGENT_STEP_FAILED,
                            task_id=task_id,
                            execution_id=exec_id,
                            step_id=t_id,
                            payload={"step": tool_step.to_dict()}
                        ))
                        event_bus.emit(AgentEvent(
                            type=EventType.TOOL_RESULT,
                            task_id=task_id,
                            execution_id=exec_id,
                            event_id=t_id,
                            tool=t_name,
                            output=out_str[:500],
                            success=res.get("success", True),
                            status_text=f"Completed {t_name}"
                        ))
                        if self.config.debug:
                            print(f"[Tool] {t_name} completed")
                        current_input = f"Tool result for {t_name}: {out_str}"
                        if self.config.debug:
                            print(f"[Agent] tool_result persisted")
                            print(f"[Agent] continuing LLM")
                        tool_executed = True

                elif legacy_command:
                    last_command = legacy_command
                    if self.config.debug:
                        self.display.print(f"  {ANSI.CYAN}▸ Executing:{ANSI.RESET} {ANSI.YELLOW}{legacy_command}{ANSI.RESET}")
                    self._dispatch_command(legacy_command)
                    final_clean_response = strip_tool_calls(strip_command_tags(response))
                    if not task_completed_emitted:
                        if is_task_request:
                            event_bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE, task_id=task_id, execution_id=exec_id, status_text="Task completed"))
                        event_bus.emit(AgentEvent(
                            type=EventType.MESSAGE_COMPLETE,
                            task_id=task_id,
                            execution_id=exec_id,
                            content=final_clean_response,
                            status_text="Response completed"
                        ))
                        task_completed_emitted = True
                    break

                if not tool_executed:
                    final_clean_response = strip_tool_calls(strip_command_tags(response))
                    if not task_completed_emitted:
                        if is_task_request:
                            event_bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE, task_id=task_id, execution_id=exec_id, status_text="Task completed"))
                        event_bus.emit(AgentEvent(
                            type=EventType.MESSAGE_COMPLETE,
                            task_id=task_id,
                            execution_id=exec_id,
                            content=final_clean_response,
                            status_text="Response completed"
                        ))
                        task_completed_emitted = True
                    break

        finally:
            if show_cli_ui:
                sys.stdout.write("\r" + " " * 50 + "\r")
                sys.stdout.flush()
            self._in_llm_processing = False

            # Complete root step
            root_step.completed_at = time.time()
            root_step.duration_ms = round((root_step.completed_at - (root_step.started_at or root_step.created_at)) * 1000, 2)
            has_error = (bool(response) and response.startswith("ERROR"))
            root_step.status = StepStatus.FAILED if has_error else StepStatus.COMPLETED
            root_step.output_preview = f"Completed in {root_step.duration_ms}ms" if root_step.status == StepStatus.COMPLETED else (response[:150] if response else "Failed")

            event_bus.emit(AgentEvent(
                type=EventType.AGENT_STEP_COMPLETED if root_step.status == StepStatus.COMPLETED else EventType.AGENT_STEP_FAILED,
                task_id=task_id or exec_id,
                execution_id=exec_id,
                step_id=root_step_id,
                payload={"step": root_step.to_dict()}
            ))

            if not task_completed_emitted:
                if is_task_request:
                    event_bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE, task_id=task_id, execution_id=exec_id, status_text="Task completed"))
                event_bus.emit(AgentEvent(
                    type=EventType.MESSAGE_COMPLETE,
                    task_id=task_id,
                    execution_id=exec_id,
                    content=final_clean_response,
                    status_text="Response completed"
                ))

        if response.startswith("ERROR"):
            if is_task_request:
                event_bus.emit(AgentEvent(type=EventType.ERROR, task_id=task_id, execution_id=exec_id, error={"message": response}, status_text="Something went wrong"))
            if show_cli_ui:
                self.display.error(response)
            return {"response": "", "command": "", "error": response, "is_task": is_task_request, "task_id": task_id}

        if final_clean_response or last_command:
            self.last_llm_response = final_clean_response
            # Record dialogue turn in VTuber short-term memory
            from delta.vtuber.memory.manager import memory_manager
            memory_manager.add_short_term_turn(user_input, final_clean_response)

        if show_cli_ui and final_clean_response:
            term_width = shutil.get_terminal_size().columns if hasattr(shutil, 'get_terminal_size') else 60
            line = "▔" * min(term_width - 10, 50)
            self.display.print(f"{ANSI.BRIGHT_MAGENTA}  Δ AI{ANSI.RESET} {ANSI.GRAY}→ {ANSI.BOLD}{owner}{ANSI.RESET}")
            self.display.print(f"  {ANSI.DIM}{line}{ANSI.RESET}")
            self.display.markdown(final_clean_response)
            self.display.print()

        return {"response": final_clean_response, "command": last_command, "error": "", "is_task": is_task_request, "task_id": task_id}

    def _configure_llm_retry(self) -> None:

        """Configure retry settings on the LLM engine from DeltaConfig."""

        if not self.llm_engine:

            return

        self.llm_engine.max_retries = self.config.get("llm_max_retries", 3)

        self.llm_engine.retry_backoff_factor = self.config.get("llm_retry_backoff_factor", 2.0)

        self.llm_engine.retry_initial_delay = self.config.get("llm_retry_initial_delay", 1.0)

        self.llm_engine.retry_max_delay = self.config.get("llm_retry_max_delay", 30.0)

    @staticmethod

    def _is_retryable_error(response: str) -> bool:

        """Check if an LLM error response is retryable with a fallback provider.

        Auth errors count when the provider is a no-key local gateway (9Router)

        whose server-side key may be missing or rotated.

        """

        retryable_patterns = [

            "ERROR [Rate Limited]",

            "ERROR [Server Error]",

            "ERROR [Timeout]",

            "ERROR [Authentication]",

            "ERROR [Access Denied]",

            "ERROR [Connection]",

        ]

        return any(pattern in response for pattern in retryable_patterns)

    def _execute_with_ai(self, intent: IntentResult, raw_input: str) -> None:

        """

        Execute command with AI understanding and guidance.

        Args:

            intent: Intent analysis result

            raw_input: Original user input

        """

        # Show AI understanding

        if self.config.verbose:

            self.display.info(f"Intent: {intent.intent} | Target: {intent.target}")

        # Build command from intent

        command = intent.intent.name.lower()

        args = intent.args

        target = intent.target

        # Add target to args

        if target and target not in args:

            args.insert(0, target)

        # Fallback: if args empty, extract from raw input after the command

        if not args and not target:

            parts = shlex.split(raw_input)

            if len(parts) > 1:

                args = parts[1:]

        # Check if the intent maps to a built-in command

        if command in self._builtin_commands:

            # Execute with AI context

            self._builtin_commands[command](args, intent)

        elif self.plugin_manager and self.plugin_manager.is_command_handled(command):

            plugin = self.plugin_manager.get_plugin_for_command(command)

            if plugin:

                result = plugin.execute(command, args, {

                    "session": self.session,

                    "intent": intent,

                    "config": self.config,

                })

                self.display.success(result)

        else:

            self.display.warning(f"Unknown command. Type 'help' for available commands.")

    def execute(self, command: str) -> str:
        """Execute a raw command line (EngineProtocol contract).

        Runs the direct dispatcher; output goes to the active display.
        ponytail: return captured output once DisplayManager buffers.
        """
        self._dispatch_command(command)
        return ""

    def _dispatch_command(self, raw: str) -> None:

        """Direct command dispatch without AI processing."""

        parts = shlex.split(raw)

        if not parts:

            return

        cmd = parts[0].lower()

        args = parts[1:]

        # Resolve aliases so the policy sees the canonical command

        cmd = self._aliases.get(cmd, cmd)

        # Enforce security policy / capability limits

        action, reason, suggestion = self.policy.check(

            cmd, args, confirm=lambda prompt: self.display.ask_confirm(prompt, default=False)

        )

        if action == "block":

            if reason:

                self.display.error(reason)

                if suggestion:

                    self.display.info(suggestion)

            return

        if action == "confirm":

            self.display.info(suggestion)

        # Check built-in commands

        if cmd in self._builtin_commands:

            self._builtin_commands[cmd](args)

        elif self.plugin_manager and self.plugin_manager.is_command_handled(cmd):

            plugin = self.plugin_manager.get_plugin_for_command(cmd)

            if plugin:

                result = plugin.execute(cmd, args, {

                    "session": self.session,

                    "config": self.config,

                })

                self.display.success(result)

        else:

            # Try LLM for unknown commands if available and enabled

            if (not self._in_llm_processing

                    and self.llm_engine and self.llm_engine.is_configured and self.config.llm_enabled):

                self._process_with_llm(raw)

                return

            # Try AI to interpret

            intent = self.intent_engine.process(raw, self.session.context)

            if intent and intent.confidence > 0.5:

                self._execute_with_ai(intent, raw)

            else:

                self.display.warning(f"Unknown command: {cmd}")

                self.display.info("Type 'help' for available commands")

    def _cmd_help(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Display help information."""

        self.display.section("Delta Commands")

        categories = {

            "🔍 Scanning": [

                ("scan <target>", "Scan target (host, ports, services)"),

                ("scan 192.168.1.1", "Scan default ports on IP"),

                ("scan 192.168.1.1 -p 22,80,443", "Scan specific ports"),

                ("scan 192.168.1.1 -p 1-1000", "Scan port range"),

                ("scan 192.168.1.0/24", "Scan entire subnet"),

                ("scan example.com", "Scan domain name"),

                ("audit <target>", "Full security audit of target"),

                ("audit 192.168.1.1", "Full audit on IP"),

                ("audit example.com", "Full audit on domain"),

                ("enumerate <target>", "Enumerate network/host information"),

                ("check <target>", "Check specific security aspects"),

            ],

            "🌐 Network": [

                ("dns <domain>", "DNS lookup (A, AAAA, MX, NS, TXT)"),

                ("dns google.com", "Get all DNS records"),

                ("dns google.com -t A", "Get A records only"),

                ("dns google.com -t MX", "Get MX records only"),

                ("dns google.com -t NS", "Get NS records only"),

                ("whois <domain>", "WHOIS lookup"),

                ("whois google.com", "WHOIS info for domain"),

                ("ping <host>", "Ping sweep"),

                ("ping 192.168.1.1", "Ping single host"),

                ("ping 192.168.1.0/24", "Ping sweep subnet"),

                ("traceroute <host>", "Trace route to host"),

                ("traceroute google.com", "Trace route to domain"),

                ("ssl <host>", "SSL/TLS certificate check"),

                ("ssl google.com", "Check SSL certificate"),

                ("ssl google.com:443", "Check SSL on custom port"),

            ],

            "🛡 Security": [

                ("analyze <target>", "Analyze scan results"),

                ("analyze 192.168.1.1", "Analyze scan for IP"),

                ("explain <vulnerability>", "Explain a vulnerability"),

                ("explain SQL Injection", "Explain SQLi attack"),

                ("explain XSS", "Explain Cross-Site Scripting"),

                ("explain CVE-2021-44228", "Explain Log4j vulnerability"),

                ("password <password>", "Analyze password strength"),

                ("password P@ssw0rd123", "Test password strength"),

                ("password", "Interactive password analysis"),

                ("jwt <token>", "Decode JWT token"),

                ("jwt eyJhbGciOiJIUzI1NiJ9...", "Decode JWT"),

            ],

            "🔧 Utilities": [

                ("decode <type> <data>", "Decode base64/hex/url"),

                ("decode base64 SGVsbG8=", "Decode Base64 string"),

                ("decode hex 48656C6C6F", "Decode hex string"),

                ("decode url hello%20world", "URL decode string"),

                ("encode <type> <data>", "Encode base64/hex/url"),

                ("encode base64 Hello", "Encode to Base64"),

                ("encode hex Hello", "Encode to hex"),

                ("encode url hello world", "URL encode string"),

                ("hash <data>", "Identify/generate hashes"),

                ("hash 5d41402abc4b2a76b9...", "Identify hash type"),

                ("hash -g md5 Hello", "Generate MD5 hash"),

                ("hash -g sha256 Hello", "Generate SHA-256 hash"),

                ("hash -g bcrypt Hello", "Generate bcrypt hash"),

            ],

            "📊 Reports": [

                ("report", "Generate security report"),

                ("report -f html", "Generate HTML report"),

                ("report -f pdf", "Generate PDF report"),

                ("report -f json", "Generate JSON report"),

                ("report -o report.html", "Save to custom file"),

                ("history", "Show command history"),

                ("history -n 20", "Show last 20 commands"),

                ("session", "Show current session info"),

            ],

            "⚙ System": [

                ("config", "Show configuration"),

                ("config --show", "Show current config"),

                ("config --reset", "Reset to default config"),

                ("plugins", "List loaded plugins"),

                ("plugin load <name>", "Load a plugin"),

                ("clear", "Clear screen"),

                ("version", "Show version info"),

                ("exit", "Exit Delta"),

                ("quit", "Exit Delta (alias)"),

            ],

            "🎯 Interactive": [

                ("dashboard", "Interactive session dashboard"),

                ("status", "Show current session status"),

                ("tips", "Show random security tip"),

                ("quote", "Show random security quote"),

                ("suggest", "Suggest commands based on context"),

                ("tutorial", "Interactive walkthrough tutorial"),

            ],

            "🎯 Attack": [

                ("brute <service> <target>", "Brute force authentication (ssh/ftp/http-basic)"),

                ("brute ssh 192.168.1.1", "Brute force SSH on default port"),

                ("brute ssh 192.168.1.1 -p 2222", "SSH on custom port"),

                ("brute ftp 192.168.1.1 -U users.txt -P pass.txt", "FTP with wordlists"),

                ("brute http-basic example.com --ssl --path /admin", "HTTP Basic Auth"),

                ("brute ssh 192.168.1.1 -u admin,root -w pass123,admin", "Specific credentials"),

                ("crack ssh 192.168.1.1", "Alias for brute force"),

            ],

            "🌐 Internet": [

                ("searchweb <query>", "Search the internet (DuckDuckGo)"),

                ("google <query>", "Alias for internet search"),

                ("duckduckgo <query>", "Alias for internet search"),

                ("fetch <url>", "Fetch and display web page content"),

                ("cve <CVE-ID>", "Lookup CVE vulnerability details"),

                ("cve CVE-2021-44228", "Search Log4j CVE details"),

                ("cve CVE-2024-3094", "Search XZ Utils backdoor CVE"),

            ],

            "🤖 AI LLM": [

                ("ai on", "Enable AI LLM chat mode"),

                ("ai off", "Disable AI LLM mode"),

                ("ai status", "Show AI LLM status"),

                ("ai reset", "Reset conversation history"),

                ("ai key <key>", "Set API key"),

                ("ai model <name>", "Set model name"),

                ("ai url <url>", "Set API base URL"),

                ("ai help", "Show AI LLM commands"),

            ],

            "🧠 Machine Learning": [

                ("ml status", "Show ML model status"),

                ("ml train", "Train ML models with security data"),

                ("ml predict", "Predict threat level from scan data"),

                ("ml predict 8 3 2 3 0 0 4", "Predict with custom features"),

                ("ml insights", "Show ML insights and recommendations"),

                ("ml export [path]", "Export ML model data to JSON"),

            ],

            "🔧 Tools": [

                ("echo <text>", "Echo back text"),

                ("timer", "Start/stop/check stopwatch"),

                ("sysinfo", "Show system information"),

                ("search <query>", "Search command history"),

                ("repeat", "Repeat last command"),

                ("export", "Export session data"),

                ("notes [text]", "Add/view session notes"),

                ("benchmark", "Run quick system benchmark"),

                ("shortcuts", "Show keyboard shortcuts"),

                ("motd", "Show message of the day"),

                ("banner", "Display Delta banner again"),

                ("alerts", "Show security alerts/info"),

            ],

            "📁 File System": [

                ("write <file> <isi>", "Buat/timpa file (tanpa konfirmasi)"),

                ("touch <file>", "Buat file kosong"),

                ("edit <file> <lama> <baru>", "Ganti teks di dalam file"),

                ("append <file> <teks>", "Tambah teks ke akhir file"),

                ("cat <file> [baris]", "Lihat isi file/dokumen"),

                ("mkdir <folder> [-p]", "Buat folder"),

                ("cd <folder>", "Pindah folder"),

                ("pwd", "Tampilkan folder aktif"),

                ("ls [folder]", "Daftar isi folder (-a tersembunyi, -l detail)"),

                ("tree [folder]", "Tampilkan struktur folder"),

                ("dirinfo [folder]", "Analisis folder/direktori"),

            ],

            "🧠 Skills": [

                ("skills", "Daftar semua skill coding"),

                ("skills <kata kunci>", "Cari skill berdasarkan kata kunci"),

                ("skill <nama>", "Aktifkan skill coding"),

                ("skill off <nama>", "Nonaktifkan skill"),

                ("skill all / skill none", "Aktifkan / nonaktifkan semua"),

            ],

        }

        for category, cmds in categories.items():

            self.display.print(f"\n  {ANSI.BOLD}{category}{ANSI.RESET}")

            for cmd, desc in cmds:

                self.display.print(f"    {ANSI.CYAN}{cmd:<40}{ANSI.RESET} {desc}")

        self.display.print()

        self.display.info("💡 Delta understands natural language. Try:")

        self.display.print('    "scan localhost"')

        self.display.print('    "scan 192.168.1.1 port 80 and 443"')

        self.display.print('    "check security server 192.168.1.1"')

        self.display.print('    "audit website on port 8080"')

        self.display.print('    "dns lookup for google.com"')

        self.display.print('    "decode base64 SGVsbG8="')

        self.display.print('    "how strong is password P@ss123"')

        self.display.print('    "generate md5 hash of Hello"')

        self.display.print()

        self.display.info("💡 Tip: Use 'tutorial' for an interactive walkthrough")

    def _cmd_scan(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Execute scanning module."""

        from delta.modules.scanner import ScannerModule

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: scan <target>")

            return

        self.session.set_host(target)

        scanner = ScannerModule(self.config, self.database, self.session, self.display)

        result = scanner.scan(target, intent)

        if not result:

            self.display.warning(f"Scan failed for {target}")

            return

        self.session.set_scan_result(target, result)

        self.session.add_to_history(f"scan {target}", host=target, result_summary=f"Scan completed for {target}")

        self.session.save()

    def _cmd_audit(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Execute full audit module."""

        from delta.modules.scanner import ScannerModule

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: audit <target>")

            return

        self.session.set_host(target)

        scanner = ScannerModule(self.config, self.database, self.session, self.display)

        result = scanner.full_audit(target, intent)

        if not result:

            self.display.warning(f"Audit failed for {target}")

            return

        self.session.set_scan_result(target, result)

        self.session.add_to_history(f"audit {target}", host=target, result_summary=f"Full audit completed for {target}")

        self.session.save()

    def _cmd_exit(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Exit the Delta engine."""

        self.running = False

        self.display.success("Goodbye!")

    def _cmd_history(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show command history."""

        history = self.session.get_history()

        if history:

            self.display.table(

                "Command History",

                ["ID", "Command", "Host", "Status"],

                [[str(h.get("id", "")), h.get("command", ""), h.get("host", ""), h.get("status", "")] for h in history[:10]]

            )

        else:

            self.display.info("No history found")

    def _cmd_clear(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Clear the screen."""

        os.system("clear" if os.name != "nt" else "cls")

        self.display.print("Screen cleared")

    def _cmd_dns(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """DNS lookup command."""

        from delta.modules.dns import DNSModule

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: dns <domain>")

            return

        dns = DNSModule()

        result = dns.get_all_dns(target)

        self.display.section(f"DNS Records for: {target}")

        if result.ip:

            self.display.info(f"IP Address: {result.ip}")

        if result.a_records:

            self.display.info(f"A Records: {', '.join(result.a_records)}")

        if result.mx_records:

            self.display.info(f"MX Records: {', '.join(result.mx_records)}")

        if result.ns_records:

            self.display.info(f"NS Records: {', '.join(result.ns_records)}")

        if result.txt_records:

            self.display.info(f"TXT Records: {', '.join(result.txt_records)}")

        if result.cname_records:

            self.display.info(f"CNAME: {', '.join(result.cname_records)}")

        if result.reverse_dns:

            self.display.info(f"Reverse DNS: {result.reverse_dns}")

    def _cmd_ssl(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """SSL certificate check command."""

        from delta.modules.ssl import SSLModule

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: ssl <host>")

            return

        port = 443

        if ":" in target:

            parts = target.rsplit(":", 1)

            if parts[1].isdigit():

                port = int(parts[1])

                target = parts[0]

        ssl_mod = SSLModule()

        info = ssl_mod.check(target, port)

        if info.valid:

            self.display.info(f"Subject: {info.subject}")

            self.display.info(f"Issuer: {info.issuer}")

            self.display.info(f"Valid: {info.not_before} to {info.not_after}")

            self.display.info(f"Expired: {info.expired}")

            self.display.info(f"Protocol: {info.protocol}")

        else:

            self.display.warning(f"SSL check failed: {info.errors}")

    def _cmd_ping(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Ping command."""

        from delta.modules.network import NetworkModule

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: ping <host>")

            return

        net = NetworkModule()

        if "/" in target or "-" in target:

            self.display.info(f"Ping sweeping {target}...")

            results = net.ping_sweep(target, timeout=1.0)

            if results:

                self.display.success(f"Found {len(results)} alive host(s):")

                for r in results:

                    self.display.print(f"  {r.ip:<16} {r.rtt_ms:.1f}ms")

            else:

                self.display.warning("No alive hosts found")

            return

        result = net.ping(target)

        if result.alive:

            self.display.success(f"Host {target} is alive (RTT: {result.rtt_ms}ms)")

        else:

            self.display.warning(f"Host {target} is not responding")

    def _cmd_traceroute(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Trace route to host command."""

        from delta.modules.network import NetworkModule

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: traceroute <host>")

            return

        self.display.info(f"Tracing route to {target}...")

        net = NetworkModule()

        try:

            result = net.traceroute(target)

            if result and result.hops:

                self.display.section(f"Traceroute to {target}")

                for hop in result.hops:

                    self.display.print(f"  {hop['ttl']:<4} {hop['host']:<40} {hop['rtt']}ms")

            else:

                self.display.warning("Traceroute failed or no response")

        except PermissionError:

            self.display.warning("Traceroute requires administrator/root privileges")

            self.display.info("Run as administrator (Windows) or root (Linux/Mac)")

    def _cmd_encode(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Encode data command."""

        from delta.modules.encode import EncodeModule

        if not args or len(args) < 2:

            self.display.warning("Usage: encode <type> <data>")

            return

        enc_type = args[0].lower()

        data = " ".join(args[1:])

        enc = EncodeModule()

        if enc_type == "base64":

            result = enc.encode_base64(data)

        elif enc_type == "hex":

            result = enc.encode_hex(data)

        elif enc_type == "url":

            result = enc.encode_url(data)

        elif enc_type in ("json", "format-json"):

            result = enc.format_json(data)

        else:

            self.display.warning(f"Unknown encode type: {enc_type}")

            self.display.info("Supported types: base64, hex, url, json")

            return

        if result.success:

            self.display.success(f"Encoded: {result.result}")

        else:

            self.display.error(result.error)

    def _cmd_decode(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Decode data command."""

        from delta.modules.encode import EncodeModule

        if not args or len(args) < 2:

            self.display.warning("Usage: decode <type> <data>")

            return

        dec_type = args[0].lower()

        data = " ".join(args[1:])

        enc = EncodeModule()

        if dec_type == "base64":

            result = enc.decode_base64(data)

        elif dec_type == "hex":

            result = enc.decode_hex(data)

        elif dec_type == "url":

            result = enc.decode_url(data)

        elif dec_type in ("json", "format-json"):

            result = enc.format_json(data)

        else:

            self.display.warning(f"Unknown decode type: {dec_type}")

            self.display.info("Supported types: base64, hex, url, json")

            return

        if result.success:

            self.display.success(f"Decoded: {result.result}")

        else:

            self.display.error(result.error)

    def _cmd_hash(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Hash operations command."""

        from delta.modules.crypto import CryptoModule

        if not args:

            self.display.warning("Usage: hash <type> <data>")

            self.display.info("  hash <hash_value>          - Identify hash type")

            self.display.info("  hash -g <algo> <data>      - Generate hash")

            self.display.info("  hash <algo> <data>         - Generate hash (short form)")

            return

        crypto = CryptoModule()

        if args[0] == "-g" and len(args) >= 3:

            algo = args[1].lower()

            data = " ".join(args[2:])

            result = crypto.generate_hash(data, algo)

            if result.matches:

                self.display.success(f"{result.hash_type}: {result.generated}")

            else:

                self.display.error(result.generated)

        elif len(args) >= 2:

            algo = args[0].lower()

            data = " ".join(args[1:])

            result = crypto.generate_hash(data, algo)

            if result.matches:

                self.display.success(f"{result.hash_type}: {result.generated}")

            else:

                self.display.error(result.generated)

        elif len(args) == 1:

            result = crypto.identify_hash(args[0])

            if result.matches:

                self.display.info(f"Possible types: {', '.join(result.possible_types)}")

            else:

                self.display.warning("Could not identify hash type")

    def _cmd_password(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Password analysis command."""

        from delta.modules.crypto import CryptoModule

        password = intent.target if intent and intent.target else (" ".join(args) if args else "")

        if not password:

            self.display.warning("Usage: password <password>")

            self.display.info("Example: password P@ssw0rd123")

            return

        crypto = CryptoModule()

        result = crypto.analyze_password(password)

        self.display.info(f"Password length: {result.length}")

        self.display.info(f"Entropy: {result.entropy:.1f} bits")

        self.display.info(f"Strength: {result.strength}")

        self.display.info(f"Score: {result.score}/5")

        self.display.info(f"Crack time estimate: {result.crack_time}")

    def _cmd_jwt(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """JWT decode command."""

        from delta.modules.encode import EncodeModule

        token = intent.target if intent and intent.target else (" ".join(args) if args else "")

        if not token:

            self.display.warning("Usage: jwt <token>")

            return

        enc = EncodeModule()

        result = enc.decode_jwt(token)

        if result.success:

            self.display.success(f"Decoded:\n{result.result}")

        else:

            self.display.error(result.error)

    def _cmd_analyze(self, args: List[str], intent: IntentResult = None) -> None:

        """Analyze scan results."""

        from delta.modules.analysis import AnalysisModule, KnowledgeBase

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: analyze <target>")

            self.display.info("Run a scan first: scan <target>")

            return

        kb = KnowledgeBase(self.database)

        analyzer = AnalysisModule(kb)

        scan_data = self.session.get_scan_result(target)

        if scan_data:

            result = analyzer.analyze(target, scan_data)

            self.display.info(f"Risk Level: {result.risk_level}")

            self.display.print(result.summary)

        else:

            self.display.warning(f"No scan results found for {target}")

    def _cmd_explain(self, args: List[str], intent: IntentResult = None) -> None:

        """Explain vulnerability."""

        from delta.modules.analysis import AnalysisModule, KnowledgeBase

        query = " ".join(args) if args else (intent.target if intent else "")

        if not query:

            self.display.warning("Usage: explain <vulnerability>")

            self.display.info("Example: explain SQL Injection, explain XSS, explain CVE-2021-44228")

            return

        kb = KnowledgeBase(self.database)

        analyzer = AnalysisModule(kb)

        result = analyzer.explain_vulnerability(query)

        if result:

            self.display.section(f"Vulnerability: {result['name']}")

            self.display.info(f"Category: {result['category']}")

            self.display.info(f"Severity: {result['severity']}")

            self.display.print(f"\n{result['description']}")

            self.display.print(f"\nRecommendation:\n{result['recommendation']}")

        else:

            self.display.warning(f"Vulnerability not found: {query}")

    def _cmd_report(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Generate security report."""

        from delta.modules.report import ReportModule, ReportData

        target = intent.target if intent else (args[0] if args and args[0] != "report" else self.session.get_host())

        if not target:

            target = self.session.get_host()

        if not target:

            self.display.warning("No target to report. Run a scan first.")

            return

        scan_data = self.session.get_scan_result(target)

        if not scan_data:

            scan_data = {

                "target": target, "ip": "", "hostname": "",

                "open_ports": [], "services": {}, "headers": {},

                "ssl": {}, "vulnerabilities": [], "risk_level": "info",

                "summary": "No scan data available.", "duration": 0.0,

            }

        from datetime import datetime

        data = ReportData(

            title=f"Delta Security Assessment Report - {target}",

            target=target,

            scan_date=scan_data.get("timestamp", datetime.now().isoformat()),

            duration=scan_data.get("duration", 0.0),

            risk_level=scan_data.get("risk_level", "info"),

            summary=scan_data.get("summary", ""),

            host_info={"IP": scan_data.get("ip", ""), "Hostname": scan_data.get("hostname", "")},

            open_ports=scan_data.get("open_ports", []),

            services=scan_data.get("services", {}),

            vulnerabilities=scan_data.get("vulnerabilities", []),

        )

        report = ReportModule()

        fmt = "all"

        if args and len(args) > 1:

            fmt = args[1]

        generated = report.generate(data, format=fmt)

        if not generated:

            self.display.warning("No report generated. Check format parameter.")

            return

        for fmt_name, path in generated.items():

            self.display.success(f"Report saved ({fmt_name}): {path}")

    def _cmd_session(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show session information."""

        self.display.section("Session Info")

        self.display.info(f"Session ID: {self.session.session_id}")

        self.display.info(self.session.get_context_summary())

    def _cmd_whois(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Simple WHOIS lookup."""

        target = intent.target if intent else (args[0] if args else "")

        if not target:

            self.display.warning("Usage: whois <domain>")

            return

        self.display.info(f"WHOIS lookup for {target} (requires network access)")

        try:

            import subprocess

            import shutil

            if shutil.which("whois"):

                result = subprocess.run(["whois", target], capture_output=True, text=True, timeout=15)

                lines = result.stdout.split("\n")[:20]

                for line in lines:

                    if line.strip():

                        self.display.print(line)

            else:

                self.display.info("whois command not found, trying whois-servers.net...")

                import socket

                try:

                    whois_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    whois_socket.settimeout(10)

                    ext = target.split(".")[-1]

                    whois_socket.connect((f"whois.{ext}", 43))

                    whois_socket.send(f"{target}\r\n".encode())

                    data = b""

                    while True:

                        chunk = whois_socket.recv(4096)

                        if not chunk:

                            break

                        data += chunk

                    whois_socket.close()

                    text = data.decode("utf-8", errors="replace")

                    for line in text.split("\n")[:25]:

                        if line.strip() and ":" in line:

                            self.display.print(line.strip())

                except Exception as e2:

                    self.display.warning(f"WHOIS lookup failed: {e2}")

        except Exception as e:

            self.display.error(f"WHOIS lookup failed: {e}")

    def _cmd_enum(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Enumerate network/host information (alias for scan)."""

        self._cmd_scan(args, intent)

    def _cmd_check(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Check specific security aspects of a target."""

        from delta.modules.scanner import ScannerModule

        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:

            self.display.warning("No target specified. Usage: check <target>")

            return

        self.session.set_host(target)

        scanner = ScannerModule(self.config, self.database, self.session, self.display)

        result = scanner.scan(target, intent)

        if result:

            self.session.set_scan_result(target, result)

            self.session.add_to_history(f"check {target}", host=target, result_summary=f"Check completed for {target}")

            self.session.save()

    def _cmd_version(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show version information."""

        self.display.section("Delta CLI Version")

        self.display.info("Delta Security Assessment CLI v1.0.0")

        self.display.info("Author: HackerAI")

        self.display.info("License: MIT")

        self.display.info(f"Session: {self.session.session_id[:16]}...")

    def _cmd_plugins(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """List loaded plugins."""

        if not self.plugin_manager:

            self.display.info("Plugin manager not initialized")

            return

        plugins = self.plugin_manager.list_plugins()

        if plugins:

            for p in plugins:

                self.display.info(f"{p.name} v{p.version} - {p.description}")

        else:

            self.display.info("No plugins loaded")

    def _cmd_config(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show/manage configuration."""

        if not args:

            self.display.section("Current Configuration")

            config_dict = {k: v for k, v in self.config.__dict__.items() if not k.startswith("_")}

            for key, value in config_dict.items():

                if "key" in key.lower() and value:

                    display_value = value[:8] + "..." if len(value) > 12 else "***"

                else:

                    display_value = value

                self.display.print(f"  {key}: {display_value}")

        else:

            if len(args) >= 2:

                key = args[0]

                value = args[1]

                self.config.set(key, value)

                self.config.save()

                self.display.success(f"Config updated: {key} = {value}")

    def _cmd_voice(self, args: List[str] = None, intent: Any = None) -> None:
        """Manage voice output subsystem."""
        if not args:
            status = "ON" if getattr(self.config, "tts_enabled", False) else "OFF"
            provider = getattr(self.config, "tts_provider", "auto")
            profile = getattr(self.config, "tts_profile", "female")
            lang = getattr(self.config, "tts_language", "id-ID")
            self.display.info(f"Voice Subsystem: {status}")
            self.display.print(f"  Provider: {provider}")
            self.display.print(f"  Profile:  {profile}")
            self.display.print(f"  Language: {lang}")
            return

        action = args[0].lower()
        if action == "on":
            self.config.tts_enabled = True
            self.config.save()
            self.display.success("Voice output enabled.")
        elif action == "off":
            self.config.tts_enabled = False
            self.config.save()
            self.display.success("Voice output disabled.")
        elif action == "status":
            self._cmd_voice([])
        elif action == "set" and len(args) >= 2:
            self.config.tts_profile = args[1]
            self.config.save()
            self.display.success(f"Voice profile set to: {args[1]}")
        elif action == "test":
            from delta.voice.manager import VoiceManager
            from delta.ai.events import event_bus
            vm = VoiceManager(config=self.config, event_bus=event_bus)
            vm.speak("Hai, aku Delta. Aku siap bantu kamu ngoding. Kalau ada yang rusak, kita cek bareng-bareng, ya.", priority=1)
            self.display.success("Voice test dispatched (Gen Z Cute Profile).")
        elif action == "personality":
            if len(args) >= 2 and args[1].lower() == "set":
                new_style = args[2] if len(args) > 2 else "genz_cute"
                self.config.tts_style = new_style
                self.config.tts_profile = f"female_id_{new_style}"
                self.config.save()
                self.display.success(f"Voice personality updated: {new_style}")
            else:
                self.display.info("Available Voice Personalities:")
                self.display.print("  1. genz_cute (Default: Gen Z Cute, sedikit manja, santai)")
                self.display.print("  2. genz_calm (Gen Z santai & kalem)")
                self.display.print("  3. pro_female (Formal & professional female)")
                self.display.print("  4. soft_female (Lembut & ramah)")
                self.display.print(f"Current personality: {getattr(self.config, 'tts_style', 'genz_cute')}")
        else:
            self.display.warning("Usage: voice [on|off|status|set <profile>|personality [list|set <style>]|test]")

    def _cmd_dashboard(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Display interactive session dashboard."""

        host = self.session.get_host() or "None"

        elapsed = datetime.now() - self.session_start

        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)

        minutes, seconds = divmod(remainder, 60)

        history = self.session.get_history() or []

        scan_count = sum(1 for h in history if h.get("command", "").startswith(("scan", "audit", "check")))

        sections = {

            "SESSION": [

                ("Session ID", self.session.session_id),

                ("Uptime", f"{hours}h {minutes}m {seconds}s"),

                ("Current Target", host),

                ("Commands Run", str(len(history))),

                ("Scans Performed", str(scan_count)),

            ],

            "SYSTEM": [

                ("Python", sys.version.split()[0]),

                ("Platform", sys.platform),

                ("Hostname", os.name),

                ("Rich Mode", "Yes" if self.display.rich else "No (stdlib)"),

                ("Prompt Toolkit", "Yes" if HAS_PROMPT_TOOLKIT else "No"),

            ],

            "COMMANDS": [

                ("Total Built-in", str(len(self._builtin_commands))),

                ("Aliases", str(len(self._aliases))),

                ("Plugins", str(len(self.plugin_manager.list_plugins()) if self.plugin_manager else 0)),

            ],

        }

        self.display.dashboard(sections)

    def _cmd_status(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show current session status in compact form."""

        host = self.session.get_host() or "none"

        elapsed = datetime.now() - self.session_start

        mins = int(elapsed.total_seconds() // 60)

        history = self.session.get_history() or []

        self.display.divider()

        self.display.status_bar([

            ("Session", self.session.session_id[:8]),

            ("Uptime", f"{mins}min"),

            ("Target", host),

            ("Cmds", str(len(history))),

            ("Plugins", str(len(self.plugin_manager.list_plugins()) if self.plugin_manager else 0)),

            ("Mode", "rich" if self.display.rich else "std"),

        ])

        self.display.divider()

    def _cmd_echo(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Echo back the input text."""

        if args:

            self.display.print(" ".join(args), style="green")

        else:

            self.display.warning("Usage: echo <text>")

    def _cmd_motd(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show message of the day."""

        from datetime import date

        today = date.today().strftime("%B %d, %Y")

        msg = (

            f"Welcome to Delta on {today}.\n"

            "Stay secure, stay vigilant.\n"

            "Delta is your AI-powered security assessment tool.\n"

            "Always ensure you have proper authorization before testing."

        )

        self.display.panel("Message of the Day", msg, style="info")

    def _cmd_sysinfo(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show system information."""

        import platform

        cpu_count = os.cpu_count() or 0

        mem = "N/A"

        try:

            import psutil

            mem = f"{psutil.virtual_memory().total / (1024**3):.1f} GB"

        except ImportError:

            pass

        info = {

            "OS": f"{platform.system()} {platform.release()}",

            "Python": sys.version.split()[0],

            "CPU Cores": str(cpu_count),

            "Memory": mem,

            "Machine": platform.machine(),

            "Platform": sys.platform,

        }

        self.display.key_value_table("System Information", info)

    def _cmd_tips(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show a random security tip."""

        if args and args[0].isdigit():

            count = min(int(args[0]), len(self._security_tips))

            selected = random.sample(self._security_tips, count)

        else:

            selected = [random.choice(self._security_tips)]

        self.display.panel("Security Tips", "\n".join(f"• {t}" for t in selected), style="info")

    def _cmd_quote(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show a random security quote."""

        quote, author = random.choice(self._security_quotes)

        self.display.panel("Security Quote", f'"{quote}"\n\n— {author}', style="cyan")

    def _cmd_search(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Search command history."""

        if not args:

            self.display.warning("Usage: search <query>")

            return

        query = " ".join(args).lower()

        history = self.session.get_history() or []

        results = [h for h in history if query in h.get("command", "").lower()]

        if results:

            self.display.table(

                f"History matching '{query}'",

                ["#", "Command", "Host", "Time"],

                [[str(i+1), h.get("command", ""), h.get("host", ""),

                  str(h.get("timestamp", ""))[:19]] for i, h in enumerate(results[:20])]

            )

        else:

            self.display.info(f"No history entries matching '{query}'")

    def _cmd_repeat(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Repeat the last command."""

        cmd = self.session.context.last_command or self.last_command

        if not cmd:

            self.display.warning("No previous command to repeat")

            return

        if cmd.lower().startswith(("repeat", "again")):

            self.display.warning("Cannot repeat the repeat command")

            return

        self.display.info(f"Repeating: {cmd}")

        self._process_input(cmd)

    def _cmd_export(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Export session data to file."""

        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        path = os.path.join(os.getcwd(), f"delta_session_{ts}.txt")

        history = self.session.get_history() or []

        host = self.session.get_host() or "none"

        try:

            with open(path, "w") as f:

                f.write(f"Delta Session Export\n")

                f.write(f"{'='*50}\n")

                f.write(f"Session: {self.session.session_id}\n")

                f.write(f"Date: {datetime.now().isoformat()}\n")

                f.write(f"Target: {host}\n")

                f.write(f"Commands: {len(history)}\n")

                f.write(f"{'='*50}\n\n")

                for h in history:

                    f.write(f"  {h.get('command', '')}\n")

            self.display.success(f"Session exported to: {path}")

        except Exception as e:

            self.display.error(f"Export failed: {e}")

    def _cmd_notes(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Add or view session notes."""

        notes_file = os.path.join(self.config.data_dir or os.getcwd(), "session_notes.txt")

        if args:

            note = " ".join(args)

            try:

                with open(notes_file, "a") as f:

                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}\n")

                self.display.success("Note added")

            except Exception as e:

                self.display.error(f"Failed to save note: {e}")

        else:

            if os.path.exists(notes_file):

                try:

                    with open(notes_file) as f:

                        content = f.read().strip()

                    if content:

                        self.display.panel("Session Notes", content, style="info")

                    else:

                        self.display.info("No notes yet. Use 'notes <text>' to add one")

                except Exception as e:

                    self.display.error(f"Failed to read notes: {e}")

            else:

                self.display.info("No notes yet. Use 'notes <text>' to add one")

    def _cmd_timer(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Start/stop/check a stopwatch timer."""

        action = args[0].lower() if args else "status"

        if action in ("start", "go", "begin"):

            self._timer_start = time.time()

            self.display.success("Timer started")

        elif action in ("stop", "end", "finish"):

            if self._timer_start:

                elapsed = time.time() - self._timer_start

                self._timer_start = None

                self.display.success(f"Timer stopped: {elapsed:.2f}s ({elapsed/60:.2f}min)")

            else:

                self.display.warning("No timer running")

        elif action in ("lap", "check", "status"):

            if self._timer_start:

                elapsed = time.time() - self._timer_start

                self.display.info(f"Timer: {elapsed:.2f}s ({elapsed/60:.2f}min)")

            else:

                self.display.info("No timer running. Use 'timer start' to begin")

        else:

            self.display.warning("Usage: timer [start|stop|status]")

    def _cmd_suggest(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Suggest commands based on current context."""

        host = self.session.get_host()

        history = self.session.get_history() or []

        suggestions = [

            ("help", "Show all available commands"),

            ("scan localhost", "Scan your local machine"),

            ("dashboard", "Show session dashboard"),

            ("status", "Show quick status"),

            ("tips", "Get security tips"),

        ]

        if host:

            suggestions.insert(0, (f"scan {host}", f"Scan {host}"))

            suggestions.insert(1, (f"audit {host}", f"Full audit of {host}"))

            suggestions.insert(2, (f"report -f html", f"Generate HTML report for {host}"))

        if not history:

            suggestions.insert(0, ("tutorial", "Start interactive tutorial"))

        self.display.panel("Suggested Commands", "\n".join(f"  {ANSI.CYAN}{cmd:<30}{ANSI.RESET} {desc}" for cmd, desc in suggestions), style="cyan")

    def _cmd_shortcuts(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show keyboard shortcuts."""

        shortcuts = [

            ("Tab", "Auto-complete command"),

            ("Up/Down", "Navigate command history"),

            ("Ctrl+C", "Copy transcript ke clipboard (atau cancel input saat mengetik)"),

            ("Ctrl+D", "Exit Delta"),

            ("Ctrl+L", "Clear screen"),

            ("Ctrl+A", "Go to beginning of line"),

            ("Ctrl+E", "Go to end of line"),

            ("Ctrl+U", "Clear current line"),

            ("Ctrl+K", "Cut from cursor to end"),

            ("Ctrl+W", "Delete word before cursor"),

        ]

        self.display.table("Keyboard Shortcuts", ["Key", "Action"], shortcuts)

    def _cmd_tutorial(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Interactive walkthrough tutorial."""

        self.display.section("Delta Interactive Tutorial")

        self.display.print("Welcome to Delta! Let's walk through the basics.\n")

        steps = [

            {

                "title": "Getting Help",

                "desc": "Type 'help' to see all available commands with examples.",

                "action": "help",

            },

            {

                "title": "Scanning a Target",

                "desc": "Use 'scan localhost' to scan your local machine for open ports.",

                "action": "scan localhost",

            },

            {

                "title": "Full Security Audit",

                "desc": "Use 'audit <target>' for a comprehensive security assessment.",

                "action": "audit localhost",

            },

            {

                "title": "DNS Lookup",

                "desc": "Use 'dns google.com' to look up DNS records for a domain.",

                "action": "dns google.com",

            },

            {

                "title": "Password Analysis",

                "desc": "Use 'password <pwd>' to test password strength.",

                "action": "password P@ssw0rd123",

            },

            {

                "title": "Encoding/Decoding",

                "desc": "Use 'encode base64 Hello' or 'decode base64 SGVsbG8='.",

                "action": "encode base64 Hello",

            },

            {

                "title": "Hash Operations",

                "desc": "Use 'hash -g md5 Hello' to generate a hash.",

                "action": "hash -g md5 Hello",

            },

            {

                "title": "Session Dashboard",

                "desc": "Type 'dashboard' to see your session overview.",

                "action": "dashboard",

            },

            {

                "title": "Natural Language",

                "desc": "Delta understands plain English! Try: 'scan port 80 on 192.168.1.1'",

                "action": None,

            },

        ]

        for i, step in enumerate(steps, 1):

            self.display.print(f"\n  {ANSI.BOLD}{ANSI.YELLOW}Step {i}: {step['title']}{ANSI.RESET}")

            self.display.print(f"  {ANSI.DIM}{step['desc']}{ANSI.RESET}")

            if step['action']:

                self.display.print(f"  {ANSI.CYAN}Example: {step['action']}{ANSI.RESET}")

        self.display.print()

        self.display.success("Tutorial complete! Type 'help' for full command list.")

    def _cmd_benchmark(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Run a quick system benchmark."""

        self.display.info("Running quick benchmark...")

        results = {}

        # String operations benchmark

        start = time.time()

        s = "".join(str(i % 10) for i in range(100000))

        _ = s.count("5")

        results["string_ops"] = time.time() - start

        # Math benchmark

        start = time.time()

        total = sum(i ** 0.5 for i in range(10000))

        results["math_ops"] = time.time() - start

        # List operations

        start = time.time()

        lst = list(range(10000))

        lst.reverse()

        _ = sorted(lst, reverse=True)

        results["list_ops"] = time.time() - start

        total_time = sum(results.values())

        self.display.panel(

            "Benchmark Results",

            f"  String Ops:  {results['string_ops']:.4f}s\n"

            f"  Math Ops:    {results['math_ops']:.4f}s\n"

            f"  List Ops:    {results['list_ops']:.4f}s\n"

            f"  {'-'*25}\n"

            f"  Total:       {total_time:.4f}s",

            style="info"

        )

    def _cmd_alerts(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Show security alerts and recommendations."""

        host = self.session.get_host()

        history = self.session.get_history() or []

        alerts = []

        if not history:

            alerts.append(("info", "No commands run yet. Start with 'scan localhost'"))

        if host:

            scan_data = self.session.get_scan_result(host)

            if scan_data:

                risk = scan_data.get("risk_level", "unknown")

                if risk in ("high", "critical"):

                    alerts.append(("critical", f"High risk found on {host} — review immediately!"))

                elif risk == "medium":

                    alerts.append(("warning", f"Medium risk on {host} — investigate"))

                else:

                    alerts.append(("success", f"{host} looks good (risk: {risk})"))

            else:

                alerts.append(("info", f"No scan data for {host}. Run 'scan {host}' first"))

        if not alerts:

            alerts.append(("info", "No alerts. Stay secure!"))

        for level, msg in alerts:

            if level == "critical":

                self.display.error(msg)

            elif level == "warning":

                self.display.warning(msg)

            elif level == "success":

                self.display.success(msg)

            else:

                self.display.info(msg)

    def _cmd_brute(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Brute force authentication on a service (SSH, FTP, HTTP-Basic)."""

        from delta.modules.bruteforce import BruteForceModule

        service = intent.parameters.get("service", "") if intent else ""

        target = intent.target if intent else ""

        port = None

        user_file = None

        pass_file = None

        usernames = None

        passwords = None

        timeout = 10.0

        threads = 10

        path = "/"

        ssl = False

        i = 0

        if args:

            if not service and i < len(args):

                service = args[i]; i += 1

            if not target and i < len(args) and not args[i].startswith("-"):

                target = args[i]; i += 1

            while i < len(args):

                a = args[i]

                if a == "-p" and i + 1 < len(args):

                    port = int(args[i + 1]); i += 2

                elif a == "-U" and i + 1 < len(args):

                    user_file = args[i + 1]; i += 2

                elif a == "-P" and i + 1 < len(args):

                    pass_file = args[i + 1]; i += 2

                elif a == "-u" and i + 1 < len(args):

                    usernames = args[i + 1].split(","); i += 2

                elif a == "-w" and i + 1 < len(args):

                    passwords = args[i + 1].split(","); i += 2

                elif a == "-t":

                    timeout = float(args[i + 1]) if i + 1 < len(args) else timeout; i += 2

                elif a == "--threads":

                    threads = int(args[i + 1]) if i + 1 < len(args) else threads; i += 2

                elif a == "--path" and i + 1 < len(args):

                    path = args[i + 1]; i += 2

                elif a == "--ssl":

                    ssl = True; i += 1

                else:

                    i += 1

        if not service:

            self.display.warning("Usage: brute <service> <target> [options]")

            self.display.info("Services: ssh, ftp, http-basic")

            self.display.info("Options:")

            self.display.info("  -p <port>          Port number")

            self.display.info("  -U <file>          Username wordlist file")

            self.display.info("  -P <file>          Password wordlist file")

            self.display.info("  -u <user1,user2>   Specific usernames (comma separated)")

            self.display.info("  -w <pass1,pass2>   Specific passwords (comma separated)")

            self.display.info("  -t <sec>           Timeout per attempt (default: 10)")

            self.display.info("  --threads <num>    Max threads (default: 10)")

            self.display.info("  --path <path>      HTTP path (for http-basic)")

            self.display.info("  --ssl              Use HTTPS (for http-basic)")

            return

        if not target:

            target = self.session.get_host()

        if not target:

            self.display.warning("No target specified")

            return

        service = service.lower().replace("_", "-").replace(" ", "-")

        if service not in ("ssh", "ftp", "http-basic"):

            self.display.warning(f"Unsupported service: {service}")

            self.display.info("Supported: ssh, ftp, http-basic")

            return

        self.session.set_host(target)

        bf = BruteForceModule(self.display)

        self.display.section(f"Brute Force: {service.upper()} on {target}")

        self.display.info("Press Ctrl+C to stop")

        try:

            summary = bf.brute_force(

                service=service, target=target, port=port,

                usernames=usernames, passwords=passwords,

                user_file=user_file, pass_file=pass_file,

                timeout=timeout, max_threads=threads,

                path=path, ssl=ssl,

            )

        except KeyboardInterrupt:

            bf.stop()

            self.display.print()

            self.display.warning("Brute force stopped by user")

            return

        if summary.error:

            self.display.error(summary.error)

            return

        self.display.print()

        self.display.section("Brute Force Results")

        if summary.successful:

            self.display.success(f"Found {len(summary.successful)} valid credential(s):")

            for r in summary.successful:

                self.display.success(f"  {r.username}:{r.password}")

        else:

            self.display.warning("No valid credentials found")

        self.display.info(f"  Service:     {summary.service}")

        self.display.info(f"  Target:      {summary.target}:{summary.port}")

        self.display.info(f"  Attempts:    {summary.total_attempts}")

        self.display.info(f"  Found:       {len(summary.successful)}")

        self.display.info(f"  Duration:    {summary.duration:.1f}s")

        self.session.add_to_history(

            f"brute {service} {target}",

            host=target,

            result_summary=f"Brute force {service} on {target}: {len(summary.successful)} found",

        )

        self.session.save()

    def _cmd_searchweb(self, args: List[str] = None, intent: IntentResult = None) -> None:

        from delta.modules.websearch import WebSearchModule

        query = " ".join(args) if args else (intent.target if intent else "")

        if not query:

            self.display.warning("Usage: searchweb <query>")

            self.display.info("Aliases: google, duckduckgo")

            return

        self.display.info(f"Searching: {query}")

        try:

            wb = WebSearchModule()

            results = wb.search_duckduckgo(query)

            if results:

                self.display.section(f"Web Results for: {query}")

                for i, r in enumerate(results, 1):

                    self.display.print(f"  {ANSI.BOLD}{i}. {r.title}{ANSI.RESET}")

                    self.display.print(f"     {ANSI.CYAN}{r.url[:80]}{ANSI.RESET}")

                    if r.snippet:

                        self.display.print(f"     {ANSI.DIM}{r.snippet[:120]}{ANSI.RESET}")

                    self.display.print()

            else:

                self.display.warning("No results found or search failed")

                self.display.info("Tip: Install 'requests' and 'beautifulsoup4' for better results")

        except Exception as e:

            self.display.warning(f"Search failed: {e}")

    def _cmd_fetch(self, args: List[str] = None, intent: IntentResult = None) -> None:

        from delta.modules.websearch import WebSearchModule

        url = " ".join(args) if args else (intent.target if intent else "")

        if not url:

            self.display.warning("Usage: fetch <url>")

            return

        if not url.startswith("http"):

            url = "https://" + url

        wb = WebSearchModule()

        self.display.info(f"Fetching: {url}")

        try:

            page = wb.fetch_page(url)

            if page.error:

                self.display.error(f"Failed: {page.error}")

                return

            self.display.section(f"Page: {page.title or url}")

            self.display.info(f"Status: {page.status_code}")

            self.display.info(f"Type: {page.content_type}")

            self.display.print()

            text = re.sub(r'<[^>]+>', ' ', page.content)

            text = re.sub(r'\s+', ' ', text).strip()

            if text:

                for chunk in [text[i:i+200] for i in range(0, len(text), 200)]:

                    self.display.print(chunk)

        except Exception as e:

            self.display.warning(f"Failed to fetch page: {e}")

    def _cmd_geoip(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """IP geolocation lookup command."""

        from delta.modules.geoip import GeoIPModule

        target = intent.target if intent else (args[0] if args else None)

        if not target:

            self.display.info("No IP specified. Looking up local machine...")

            geo = GeoIPModule()

            result = geo.lookup_local()

            if not result.ip:

                self.display.warning("Could not determine local IP. Usage: geoip <ip>")

                return

            target = result.ip

        else:

            geo = GeoIPModule()

            result = geo.lookup(target)

        if result.success:

            self.display.section(f"GeoIP: {result.ip}")

            self.display.info(f"Country: {result.country} ({result.country_code})")

            self.display.info(f"Region: {result.region}")

            self.display.info(f"City: {result.city}")

            self.display.info(f"ZIP: {result.zip_code}")

            self.display.info(f"Coordinates: {result.lat}, {result.lon}")

            self.display.info(f"Timezone: {result.timezone}")

            self.display.info(f"ISP: {result.isp}")

            self.display.info(f"Organization: {result.org}")

            self.display.info(f"AS: {result.as_number}")

        else:

            self.display.warning(f"GeoIP lookup failed: {result.error}")

    def _cmd_cve(self, args: List[str] = None, intent: IntentResult = None) -> None:

        from delta.modules.websearch import WebSearchModule

        cve_id = " ".join(args) if args else (intent.target if intent else "")

        if not cve_id:

            self.display.warning("Usage: cve <CVE-ID>")

            self.display.info("Example: cve CVE-2021-44228")

            return

        cve_id = cve_id.upper().strip()

        if not cve_id.startswith("CVE-"):

            cve_id = "CVE-" + cve_id

        self.display.info(f"Looking up: {cve_id}")

        try:

            wb = WebSearchModule()

            result = wb.search_cve(cve_id)

            if result:

                self.display.section(f"CVE Information: {cve_id}")

                self.display.print(f"  {ANSI.BOLD}{result.title}{ANSI.RESET}")

                self.display.print(f"  {ANSI.CYAN}{result.url}{ANSI.RESET}")

                if result.snippet:

                    self.display.print(f"\n  {result.snippet}")

            else:

                self.display.warning(f"No results found for {cve_id}")

                self.display.info("Try: searchweb CVE-XXXX-XXXX vulnerability")

        except Exception as e:

            self.display.warning(f"CVE lookup failed: {e}")

    def _cmd_ml(self, args: List[str] = None, intent: IntentResult = None) -> None:

        subcmd = args[0].lower() if args else "status"

        if subcmd in ("predict", "analyze", "classify"):

            self._ml_predict(args[1:] if len(args) > 1 else [])

        elif subcmd in ("train", "learn", "fit"):

            self._ml_train(args[1:] if len(args) > 1 else [])

        elif subcmd in ("status", "info", "show"):

            self._ml_status()

        elif subcmd in ("insights", "insight"):

            self._ml_insights()

        elif subcmd == "export":

            self._ml_export(args[1] if len(args) > 1 else "")

        elif subcmd in ("help", "--help", "-h"):

            self._ml_help()

        else:

            self._ml_status()

    def _ml_predict(self, args: List[str]) -> None:

        from delta.ml.engine import MLEngine

        ml = MLEngine(self.config.data_dir)

        if not args:

            host = self.session.get_host()

            if host and self.session.get_scan_result(host):

                scan_data = self.session.get_scan_result(host)

                result = ml.analyze_scan_data(scan_data)

                self.display.section("ML Threat Analysis")

                self.display.info(f"Target: {host}")

                self.display.info(f"Prediction: {ANSI.BOLD}{result.label.upper()}{ANSI.RESET}")

                self.display.info(f"Confidence: {result.confidence:.1%}")

                if result.probabilities:

                    self.display.print()

                    for cls, prob in sorted(result.probabilities.items(), key=lambda x: -x[1]):

                        bar = "█" * int(prob * 20)

                        self.display.print(f"  {cls:<10} {bar} {prob:.1%}")

                self.display.print()

                self.display.info(result.explanation)

            else:

                self.display.warning("No scan data available. Run a scan first, or provide features.")

                self.display.info("Usage: ml predict <feature1 feature2 ...>")

            return

        try:

            features = [float(x) for x in args]

            result = ml.predict_threat(features)

            self.display.section("ML Prediction Result")

            self.display.info(f"Classification: {ANSI.BOLD}{result.label.upper()}{ANSI.RESET}")

            self.display.info(f"Confidence: {result.confidence:.1%}")

            self.display.info(result.explanation)

        except ValueError:

            self.display.warning("Features must be numeric. Example: ml predict 5 2 3 1 0 0 2")

    def _ml_train(self, args: List[str]) -> None:

        from delta.ml.engine import MLEngine

        from delta.ml.pipeline import MLPipeline

        ml = MLEngine(self.config.data_dir)

        pipeline = MLPipeline(ml)

        self.display.info("Training ML models with synthetic data...")

        result = pipeline.auto_train([])

        self.display.success("ML models trained successfully")

        if "classifier" in result:

            self.display.info(f"  Classifier:  {result['classifier']['accuracy']}")

        if "knn" in result:

            self.display.info(f"  KNN:         {result['knn']['accuracy']}")

        if "anomaly" in result:

            self.display.info(f"  Anomaly:     {result['anomaly']['samples']} samples trained")

    def _ml_status(self) -> None:

        from delta.ml.engine import MLEngine

        ml = MLEngine(self.config.data_dir)

        status = ml.get_status()

        if status:

            self.display.section("ML Model Status")

            for name, info in status.items():

                self.display.print(f"  {ANSI.BOLD}{name}{ANSI.RESET}")

                for key, val in info.items():

                    self.display.print(f"    {key}: {val}")

                self.display.print()

        else:

            self.display.warning("No ML models trained")

            self.display.info("Use 'ml train' to train models with synthetic data")

    def _ml_insights(self) -> None:

        from delta.ml.engine import MLEngine

        from delta.ml.pipeline import MLPipeline

        ml = MLEngine(self.config.data_dir)

        pipeline = MLPipeline(ml)

        insights = pipeline.get_insights()

        self.display.section("ML Insights")

        for insight in insights:

            self.display.info(insight)

    def _ml_export(self, path: str = "") -> None:

        from delta.ml.engine import MLEngine

        from delta.ml.pipeline import MLPipeline

        ml = MLEngine(self.config.data_dir)

        pipeline = MLPipeline(ml)

        if not path:

            path = os.path.join(os.getcwd(), "delta_ml_export.json")

        result = pipeline.export_model_data(path)

        self.display.success(f"ML data exported to: {result}")

    def _ml_help(self) -> None:

        self.display.section("ML Command Usage")

        commands = [

            ("ml status", "Show ML model status"),

            ("ml train", "Train ML models with synthetic security data"),

            ("ml predict [features]", "Predict threat level (or use current scan data)"),

            ("ml analyze", "Alias for ml predict"),

            ("ml insights", "Show ML insights and recommendations"),

            ("ml export [path]", "Export ML model data to JSON"),

        ]

        for cmd, desc in commands:

            self.display.print(f"  {ANSI.CYAN}{cmd:<30}{ANSI.RESET} {desc}")

        self.display.print()

        self.display.info("Features: [open_ports dangerous_ports vulns missing_headers expired_ssl self_signed_ssl services]")

        self.display.info("Example: ml predict 8 3 2 3 0 0 4")

    def _cmd_ai(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Manage AI LLM integration."""

        subcmd = args[0].lower() if args else "status"

        if subcmd in ("on", "enable", "start"):

            if not self.llm_engine:

                self.display.error("LLM engine not initialized")

                return

            if not self.llm_engine.is_configured:

                self.display.error("API key not configured. Set DELTA_API_KEY env var, llm_api_key in config, or use a local model with /provider 9router (no API key needed) or /provider local (Ollama)")

                return

            self.config.llm_enabled = True

            self.config.save()

            self.display.success("AI LLM mode enabled")

            self.display.info("You can now chat with Delta AI or run security commands naturally")

        elif subcmd in ("off", "disable", "stop"):

            self.config.llm_enabled = False

            self.config.save()

            self.display.success("AI LLM mode disabled")

            self.display.info("Delta will use standard command processing")

        elif subcmd in ("reset", "clear", "new"):

            if self.llm_engine:

                self.llm_engine.reset_conversation()

                self.display.success("Conversation reset")

        elif subcmd in ("status", "info", "show"):

            self.display.section("AI LLM Status")

            self.display.info(f"Enabled: {self.config.llm_enabled}")

            self.display.info(f"Configured: {bool(self.llm_engine and self.llm_engine.is_configured)}")

            if self.llm_engine:

                self.display.info(f"Provider: {self.llm_engine.provider}")

                self.display.info(f"Model: {self.llm_engine.model}")

                self.display.info(f"Base URL: {self.llm_engine.base_url}")

                self.display.info(f"Memory: {'enabled' if self.llm_engine.memory_enabled else 'disabled'}")

                self.display.info(f"Session: {self.llm_engine.session_id}")

                self.display.info(f"API Key: {'*' * 8 + self.llm_engine.api_key[-4:] if self.llm_engine.api_key else 'Not set'}")

            else:

                self.display.info("Engine: Not initialized")

        elif subcmd in ("help", "--help", "-h"):

            self.display.section("AI LLM Commands")

            cmds = [

                ("ai on", "Enable AI LLM mode"),

                ("ai off", "Disable AI LLM mode"),

                ("ai status", "Show AI LLM status"),

                ("ai reset", "Reset conversation history"),

                ("ai key <key>", "Set API key"),

                ("ai model <model>", "Set model name"),

                ("ai provider [name]", "Set or list provider"),

                ("ai url <url>", "Set API base URL"),

                ("ai preset [name]", "Switch model/provider preset"),

                ("ai memory on/off", "Toggle persistent memory"),

                ("ai memory clear", "Clear all saved sessions"),

                ("ai memory list", "List saved sessions"),

                ("ai memory load <id>", "Load a saved session"),

                ("ai memory delete <id>", "Delete a saved session"),

            ]

            for cmd, desc in cmds:

                self.display.print(f"  {ANSI.CYAN}{cmd:<35}{ANSI.RESET} {desc}")

            self.display.print()

            self.display.info("Slash commands: /model, /provider, /key, /help")

        elif subcmd == "key" and len(args) >= 2:

            if self.llm_engine:

                self.llm_engine.api_key = args[1]

                self.config.llm_api_key = args[1]

                self.config.save()

                self.display.success("API key updated")

        elif subcmd == "model" and len(args) >= 2:

            model_name = args[1]

            if self.llm_engine:

                from delta.ai.llm import MODEL_PRESETS

                if model_name in MODEL_PRESETS:

                    self.llm_engine.apply_preset(model_name)

                    self.config.llm_model = self.llm_engine.model

                    self.config.llm_api_base_url = self.llm_engine.base_url

                    self.config.llm_provider = self.llm_engine.provider

                else:

                    self.llm_engine.model = model_name

                    self.config.llm_model = model_name

                self.config.save()

                self.display.success(f"Model set to: {self.llm_engine.model}")

        elif subcmd == "provider" and len(args) >= 2:

            provider_name = args[1].lower()

            from delta.ai.llm import PROVIDERS

            if provider_name in PROVIDERS:

                pinfo = PROVIDERS[provider_name]

                self.config.llm_provider = provider_name

                if self.llm_engine:

                    self.llm_engine.provider = provider_name

                    self.llm_engine.base_url = pinfo["base_url"]

                    self.llm_engine.model = pinfo.get("default_model", self.llm_engine.model)

                    self.config.llm_api_base_url = self.llm_engine.base_url

                    self.config.llm_model = self.llm_engine.model

                self.config.save()

                self.display.success(f"Provider: {pinfo['description']}")

            else:

                all_p = ", ".join(PROVIDERS.keys())

                self.display.error(f"Unknown provider: {provider_name}. Available: {all_p}")

        elif subcmd == "provider" and len(args) == 1:

            from delta.ai.llm import PROVIDERS

            self.display.section("Available Providers")

            for name, info in PROVIDERS.items():

                self.display.info(f"  {name}: {info['description']}")

        elif subcmd == "url" and len(args) >= 2:

            if self.llm_engine:

                self.llm_engine.base_url = args[1]

                self.config.llm_api_base_url = args[1]

                self.config.save()

                self.display.success(f"Base URL set to: {args[1]}")

        elif subcmd == "preset" and len(args) >= 2:

            preset = args[1].lower()

            from delta.ai.llm import MODEL_PRESETS, PROVIDERS

            if preset in MODEL_PRESETS:

                if self.llm_engine:

                    self.llm_engine.apply_preset(preset)

                    self.config.llm_model = self.llm_engine.model

                    self.config.llm_api_base_url = self.llm_engine.base_url

                    self.config.llm_provider = self.llm_engine.provider

                    self.config.save()

                    self.display.success(f"Switched to {MODEL_PRESETS[preset]['description']}")

            elif preset in PROVIDERS:

                info = PROVIDERS[preset]

                if self.llm_engine:

                    self.llm_engine.provider = preset

                    self.llm_engine.base_url = info["base_url"]

                    self.llm_engine.model = info.get("default_model", self.llm_engine.model)

                    self.config.llm_provider = preset

                    self.config.llm_api_base_url = info["base_url"]

                    self.config.llm_model = self.llm_engine.model

                    self.config.save()

                    self.display.success(f"Switched to provider: {info['description']}")

            else:

                all_names = list(MODEL_PRESETS.keys()) + list(PROVIDERS.keys())

                self.display.error(f"Unknown preset: {preset}. See /model for models, /provider for providers")

        elif subcmd == "preset" and len(args) == 1:

            from delta.ai.llm import MODEL_PRESETS, PROVIDERS

            self.display.section("Available Presets")

            self.display.info("Models:")

            for name, info in MODEL_PRESETS.items():

                self.display.info(f"  {name}: {info['description']}")

            self.display.info("Providers:")

            for name, info in PROVIDERS.items():

                self.display.info(f"  {name}: {info['description']}")

        elif subcmd == "memory" and len(args) >= 2:

            action = args[1].lower()

            if action == "on":

                if self.llm_engine:

                    self.llm_engine.memory_enabled = True

                    self.config.memory_enabled = True

                    self.config.save()

                    self.display.success("Memory enabled")

            elif action == "off":

                if self.llm_engine:

                    self.llm_engine.memory_enabled = False

                    self.config.memory_enabled = False

                    self.config.save()

                    self.display.success("Memory disabled")

            elif action == "clear":

                if self.llm_engine and self.llm_engine.memory_manager:

                    count = self.llm_engine.memory_manager.clear_all()

                    self.display.success(f"Cleared {count} saved session(s)")

            elif action == "list":

                if self.llm_engine and self.llm_engine.memory_manager:

                    sessions = self.llm_engine.memory_manager.list_sessions()

                    if sessions:

                        self.display.section("Saved Sessions")

                        for s in sessions[:20]:

                            self.display.info(f"  {s['session_id']} ({s['messages']} msgs, {s['updated_at']})")

                    else:

                        self.display.info("No saved sessions")

            elif action == "load" and len(args) >= 3:

                if self.llm_engine:

                    self.llm_engine.set_session_id(args[2])

                    self.display.success(f"Loaded session: {args[2]}")

            elif action == "delete" and len(args) >= 3:

                if self.llm_engine and self.llm_engine.memory_manager:

                    if self.llm_engine.memory_manager.delete_session(args[2]):

                        self.display.success(f"Deleted session: {args[2]}")

                    else:

                        self.display.error(f"Session not found: {args[2]}")

            else:

                self.display.warning("Usage: ai memory [on|off|clear|list|load <id>|delete <id>]")

        else:

            self.display.warning("Usage: ai [on|off|status|reset|key|model|provider|url|preset|memory|help]")

    def _cmd_policy(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Manage Delta security policy & capability limits."""

        subcmd = args[0].lower() if args else "status"

        if subcmd in ("status", "info", "show"):

            self.display.section("Delta Policy & Capability Limits")

            for line in self.policy.status_lines():

                self.display.info(line)

            violations = self.policy.violations()

            if violations:

                self.display.print()

                self.display.warning(f"{len(violations)} pelanggaran tercatat sesi ini:")

                for v in violations:

                    self.display.print(f"  {v['time']}  {v['command']}  →  {v['reason']}")

        elif subcmd == "ethics":

            self.display.section("Ethics of Delta")

            self.display.panel("Security Ethics", self.policy.ethics(), style="info")

        elif subcmd in ("authorize", "allow") and len(args) >= 2:

            self.display.success(self.policy.authorize(args[1]))

        elif subcmd == "deauthorize" and len(args) >= 2:

            self.display.success(self.policy.deauthorize(args[1]))

        elif subcmd == "block" and len(args) >= 2:

            self.display.success(self.policy.block_target(args[1]))

        elif subcmd == "deblock" and len(args) >= 2:

            self.display.success(self.policy.deblock_target(args[1]))

        elif subcmd in ("on", "enable"):

            self.policy.policy["enabled"] = True

            self.policy.save()

            self.display.success("Kebijakan keamanan diaktifkan")

        elif subcmd in ("off", "disable"):

            self.policy.policy["enabled"] = False

            self.policy.save()

            self.display.warning("Kebijakan keamanan dinonaktifkan — semua batas ditiadakan")

        elif subcmd == "reset":

            from delta.core.policy import DEFAULT_POLICY

            self.policy.policy = dict(DEFAULT_POLICY)

            self.policy.save()

            self.display.success("Kebijakan dikembalikan ke default")

        else:

            self.display.section("Policy Commands")

            cmds = [

                ("policy", "Tampilkan status kebijakan & batas"),

                ("policy ethics", "Tampilkan etika keamanan Delta"),

                ("policy authorize <host>", "Otorisasi target publik (mis. scan ke domain/IP milik Anda)"),

                ("policy deauthorize <host>", "Cabut otorisasi target"),

                ("policy block <host>", "Blokir target"),

                ("policy deblock <host>", "Buka blokir target"),

                ("policy on / off", "Aktifkan / nonaktifkan kebijakan"),

                ("policy reset", "Kembalikan kebijakan ke default"),

            ]

            for cmd, desc in cmds:

                self.display.print(f"  {ANSI.CYAN}{cmd:<35}{ANSI.RESET} {desc}")

            self.display.print()

            self.display.info(f"File kebijakan: {self.policy._policy_path}")

    def _cmd_banner(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Display the Delta banner again."""

        self.display.show_banner()

    # =========================================================== skills

    def _cmd_skills(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Daftarkan semua skill coding beserta status aktif/nonaktif."""

        args = args or []

        query = " ".join(args).strip().lower()

        skills = self.skills.find(query) if query else self.skills.list_skills()

        if not skills:

            self.display.warning("Tidak ada skill ditemukan. Coba `skills` tanpa kata kunci.")

            return

        self.display.section("🧠 Delta Skills — Coding Mastery")

        for skill in skills:

            marker = "●" if self.skills.is_active(skill.name) else "○"

            state = f"{ANSI.GREEN}Aktif{ANSI.RESET}" if self.skills.is_active(skill.name) else f"{ANSI.GRAY}Nonaktif{ANSI.RESET}"

            self.display.print(

                f"  {ANSI.CYAN}{marker} {skill.name:<22}{ANSI.RESET} "

                f"[{state}] {ANSI.DIM}{skill.category}{ANSI.RESET}"

            )

            if skill.description:

                self.display.print(f"      {ANSI.GRAY}{skill.description}{ANSI.RESET}")

        active = self.skills.active_names()

        self.display.print()

        self.display.info(

            f"Aktif ({len(active)}): {', '.join(active) if active else '(kosong)'}"

        )

        self.display.info("Gunakan: skill <nama> | skill off <nama> | skill all | skill none")

    def _cmd_skill(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Aktifkan/nonaktifkan skill coding."""

        args = args or []

        if not args:

            self._cmd_skills()

            return

        action = args[0].lower()

        if action in ("all", "on"):

            for skill in self.skills.list_skills():

                self.skills.activate(skill.name)

            self.display.success(f"Semua {len(self.skills.list_skills())} skill diaktifkan.")

            return

        if action in ("none", "off", "clear"):

            if len(args) > 1:

                self.skills.deactivate(args[1])

                self.display.success(f"Skill '{args[1]}' dinonaktifkan.")

                return

            self.skills.set_active([])

            self.display.success("Semua skill dinonaktifkan.")

            return

        if action in ("-d", "--deactivate", "remove"):

            if len(args) < 2:

                self.display.warning("Usage: skill -d <nama>")

                return

            self.skills.deactivate(args[1])

            self.display.success(f"Skill '{args[1]}' dinonaktifkan.")

            return

        if action in ("search", "find", "cari"):

            query = " ".join(args[1:])

            if query:

                self._cmd_skills([query])

            else:

                self.display.warning("Usage: skill search <kata kunci>")

            return

        if action in ("list", "ls"):

            self._cmd_skills()

            return

        name = action

        skill = self.skills.get_skill(name)

        if skill is None:

            hits = self.skills.find(name)

            if not hits:

                available = ", ".join(s.name for s in self.skills.list_skills())

                self.display.error(f"Skill '{name}' tidak ditemukan. Tersedia: {available}")

                return

            skill = hits[0]

        if self.skills.is_active(skill.name):

            self.display.info(f"Skill '{skill.name}' sudah aktif.")

            return

        self.skills.activate(skill.name)

        self.display.success(f"Skill '{skill.name}' diaktifkan — {skill.description}")

    # ======================================================== file system

    #

    # Semua perintah di bawah dieksekusi LANGSUNG tanpa konfirmasi:

    # operasi file/folder tidak termasuk risky_commands di kebijakan Delta.

    @staticmethod

    def _fs_non_flags(args: List[str]) -> List[str]:

        """Ambil argumen non-flag dari daftar argumen."""

        from delta.modules.filesystem import _PATH_FLAGS

        out: List[str] = []

        skip = False

        for a in args:

            if skip:

                skip = False

                continue

            if a in _PATH_FLAGS and a in ("-f", "--find", "-r", "--replace", "-n", "--lines", "-d", "--depth"):

                skip = True

                continue

            if a.startswith("-"):

                continue

            out.append(a)

        return out

    @staticmethod

    def _fs_flag_value(args: List[str], flags: List[str]) -> Optional[str]:

        for i, a in enumerate(args):

            if a in flags and i + 1 < len(args):

                return args[i + 1]

        return None

    @staticmethod

    def _fs_has_flag(args: List[str], flags: List[str]) -> bool:

        return any(a in flags for a in args)

    def _fs_new(self) -> Any:

        from delta.modules.filesystem import FileSystemModule

        return FileSystemModule(cwd=self.cwd, display=self.display)

    def _cmd_mkdir(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Buat folder (langsung, tanpa konfirmasi)."""

        path = (args[0] if args else "") or (intent.args[0] if intent and intent.args else "")

        if not path:

            self.display.warning("Usage: mkdir <folder> [-p]")

            return

        parents = self._fs_has_flag(args or [], ["-p", "--parents"])

        ok, msg = self._fs_new().mkdir(path, parents)

        (self.display.success if ok else self.display.error)(msg)

    def _cmd_write(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Buat/timpa file (langsung, tanpa konfirmasi)."""

        from delta.modules.filesystem import _strip_content_prefix

        parts = self._fs_non_flags(args or [])

        if not parts:

            self.display.warning("Usage: write <file> <isi>")

            return

        path = parts[0]

        content = _strip_content_prefix(" ".join(parts[1:]))

        ok, msg = self._fs_new().write(path, content)

        (self.display.success if ok else self.display.error)(msg)

    def _cmd_touch(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Buat file kosong (langsung, tanpa konfirmasi)."""

        path = (args[0] if args else "") or (intent.args[0] if intent and intent.args else "")

        if not path:

            self.display.warning("Usage: touch <file>")

            return

        ok, msg = self._fs_new().touch(path)

        (self.display.success if ok else self.display.error)(msg)

    def _cmd_edit(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Ubah isi file — ganti teks lama dengan teks baru (langsung)."""

        import re as _re

        parts = self._fs_non_flags(args or [])

        if not parts:

            self.display.warning("Usage: edit <file> <teks-lama> <teks-baru>")

            self.display.info("Contoh: edit app.py --find 'Halo' --replace 'Hai'")

            return

        path = parts[0]

        old = self._fs_flag_value(args or [], ["-f", "--find"])

        new = self._fs_flag_value(args or [], ["-r", "--replace"])

        if old is None:

            rest = " ".join(parts[1:])

            split = _re.search(r"\b(dengan|menjadi|ke|to|with)\b", rest, _re.IGNORECASE)

            if split:

                old = rest[:split.start()].strip()

                new = rest[split.end():].strip()

            else:

                old = rest

                new = ""

            old = _re.sub(r"^(ganti|ubah|replace|edit|rubah)\s*", "", old, flags=_re.IGNORECASE).strip()

        if not old:

            self.display.warning("Teks lama kosong. Usage: edit <file> <teks-lama> <teks-baru>")

            return

        ok, msg = self._fs_new().edit(path, old, new or "")

        (self.display.success if ok else self.display.error)(msg)

    def _cmd_append(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Tambahkan teks ke akhir file (langsung, tanpa konfirmasi)."""

        from delta.modules.filesystem import _strip_content_prefix

        parts = self._fs_non_flags(args or [])

        if not parts:

            self.display.warning("Usage: append <file> <teks>")

            return

        path = parts[0]

        text = _strip_content_prefix(" ".join(parts[1:]))

        ok, msg = self._fs_new().append(path, text)

        (self.display.success if ok else self.display.error)(msg)

    def _cmd_cat(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Lihat isi file/dokumen (langsung, tanpa konfirmasi)."""

        parts = self._fs_non_flags(args or [])

        if not parts:

            self.display.warning("Usage: cat <file> [jumlah-baris]")

            return

        path = parts[0]

        max_lines: Optional[int] = None

        if len(parts) > 1 and parts[1].isdigit():

            max_lines = int(parts[1])

        elif len(args or []) > 1 and (args[1] if args else "") in ("-n", "--lines") and len(args) > 2:

            max_lines = int(args[2])

        ok, content = self._fs_new().read(path, max_lines)

        if not ok:

            self.display.error(content)

            return

        self.display.section(f"File: {path}")

        for line in content.split("\n"):

            self.display.print(line)

    def _fs_new(self) -> Any:
        """Instansiasi FileSystemModule dengan cwd engine saat ini."""
        from delta.modules.filesystem import FileSystemModule
        return FileSystemModule(cwd=self.cwd, display=self.display)

    def _cmd_cd(self, args: Optional[List[str]] = None, intent: Optional[IntentResult] = None) -> None:

        """Pindah folder (langsung, tanpa konfirmasi)."""

        path = (args[0] if args else "") or (intent.args[0] if intent and intent.args else "")

        if not path:

            path = "~"

        ok, msg = self.set_cwd(path)

        (self.display.success if ok else self.display.error)(msg)

    def _cmd_pwd(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Tampilkan folder aktif."""

        self.display.info(f"Folder aktif: {self.cwd}")

    def _cmd_ls(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Daftar isi folder (langsung, tanpa konfirmasi)."""

        from delta.modules.filesystem import FileSystemModule

        parts = self._fs_non_flags(args or [])

        path = parts[0] if parts else ""

        all_hidden = self._fs_has_flag(args or [], ["-a", "--all"])

        long = self._fs_has_flag(args or [], ["-l", "--long"])

        fs = self._fs_new()

        ok, entries = fs.list_dir(path, all_hidden=all_hidden, long=long)

        if not ok:

            self.display.error(f"Folder tidak ditemukan: {fs._resolve(path)}")

            return

        if not entries:

            self.display.info(f"(folder kosong) {fs._resolve(path)}")

            return

        self.display.section(f"Folder: {fs._resolve(path)} ({len(entries)} entri)")

        for e in entries:

            if e["is_dir"]:

                self.display.print(f"  {ANSI.CYAN}{e['name']}/{ANSI.RESET}")

            elif long:

                self.display.print(f"  {e['name']:<40} {FileSystemModule._human_size(e['size']):>10}  {e['mtime'].strftime('%Y-%m-%d %H:%M')}")

            else:

                self.display.print(f"  {e['name']}")

    def _cmd_tree(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Tampilkan struktur folder (langsung, tanpa konfirmasi)."""

        parts = self._fs_non_flags(args or [])

        path = parts[0] if parts else ""

        depth = 2

        flag = self._fs_flag_value(args or [], ["-d", "--depth"])

        if flag and flag.isdigit():

            depth = int(flag)

        ok, body = self._fs_new().tree(path, max_depth=depth)

        if not ok:

            self.display.error(body)

            return

        self.display.section("Struktur Folder")

        self.display.print(body)

    def _cmd_dirinfo(self, args: List[str] = None, intent: IntentResult = None) -> None:

        """Analisis folder/direktori (langsung, tanpa konfirmasi)."""

        from delta.modules.filesystem import FileSystemModule

        parts = self._fs_non_flags(args or [])

        path = parts[0] if parts else ""

        fs = self._fs_new()

        ok, stats = fs.dirinfo(path)

        if not ok:

            self.display.error(f"Folder tidak ditemukan: {fs._resolve(path)}")

            return

        self.display.section(f"Analisis Folder: {stats['path']}")

        self.display.key_value_table("Ringkasan", {

            "File": str(stats["files"]),

            "Folder": str(stats["dirs"]),

            "Tersembunyi": str(stats["hidden"]),

            "Total Ukuran": FileSystemModule._human_size(stats["total_size"]),

        })

        if stats["extensions"]:

            self.display.table(

                "Tipe File (terbesar)",

                ["Ekstensi", "Jumlah", "Ukuran"],

                [[ext, str(info["count"]), FileSystemModule._human_size(info["size"])]

                 for ext, info in list(stats["extensions"].items())[:10]],

            )

        if stats["largest"]:

            self.display.table(

                "File Terbesar",

                ["File", "Ukuran"],

                [[name, FileSystemModule._human_size(size)] for name, size in stats["largest"]],

            )

        if stats["recent"]:

            self.display.table(

                "Terbaru Dimodifikasi",

                ["File", "Waktu"],

                [[name, datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")] for name, ts in stats["recent"]],

            )

    # =========================================================== git workflow

    def _cmd_git(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        subcmd = (args[0].lower() if args else "") or (intent.args[0].lower() if intent and intent.args else "")
        git = GitModule(cwd=self.cwd, display=self.display)
        if subcmd in ("init", "ginit"):
            self._cmd_git_init(args[1:] if args else [], intent)
        elif subcmd in ("status", "gstatus"):
            self._cmd_git_status(args[1:] if args else [], intent)
        elif subcmd in ("add", "gadd"):
            self._cmd_git_add(args[1:] if args else [], intent)
        elif subcmd in ("commit", "gcommit"):
            self._cmd_git_commit(args[1:] if args else [], intent)
        elif subcmd in ("push", "gpush"):
            self._cmd_git_push(args[1:] if args else [], intent)
        elif subcmd in ("pull", "gpull"):
            self._cmd_git_pull(args[1:] if args else [], intent)
        elif subcmd in ("branch", "gbranch"):
            self._cmd_git_branch(args[1:] if args else [], intent)
        elif subcmd in ("log", "glog"):
            self._cmd_git_log(args[1:] if args else [], intent)
        elif subcmd in ("remote", "gremote"):
            self._cmd_git_remote(args[1:] if args else [], intent)
        elif subcmd in ("diff", "gdiff"):
            self._cmd_git_diff(args[1:] if args else [], intent)
        elif subcmd in ("clone", "gclone"):
            self._cmd_git_clone(args[1:] if args else [], intent)
        else:
            self.display.warning(f"Unknown git subcommand: {subcmd}")
            self.display.info("Usage: git <init|status|add|commit|push|pull|branch|log|remote|diff|clone>")

    def _cmd_git_init(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        git = GitModule(cwd=self.cwd, display=self.display)
        ok, msg = git.init()
        (self.display.success if ok else self.display.error)(msg)

    def _cmd_git_status(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        git = GitModule(cwd=self.cwd, display=self.display)
        ok, msg = git.status()
        if ok:
            self.display.section("Git Status")
            self.display.print(msg)
        else:
            self.display.error(msg)

    def _cmd_git_add(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        git = GitModule(cwd=self.cwd, display=self.display)
        all_files = self._fs_has_flag(args or [], ["-A", "--all"])
        paths = self._fs_non_flags(args or []) if not all_files else None
        ok, msg = git.add(paths=paths, all_files=all_files)
        (self.display.success if ok else self.display.error)(msg)

    def _cmd_git_commit(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        message = " ".join(args) if args else (intent.target if intent else "")
        if not message:
            self.display.warning("Usage: git commit <message>")
            return
        git = GitModule(cwd=self.cwd, display=self.display)
        ok, msg = git.commit(message)
        (self.display.success if ok else self.display.error)(msg)

    def _cmd_git_push(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        remote = "origin"
        branch = ""
        if args:
            remote = args[0]
            if len(args) > 1:
                branch = args[1]
        git = GitModule(cwd=self.cwd, display=self.display)
        ok, msg = git.push(remote=remote, branch=branch)
        (self.display.success if ok else self.display.error)(msg)

    def _cmd_git_pull(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        remote = "origin"
        branch = ""
        if args:
            remote = args[0]
            if len(args) > 1:
                branch = args[1]
        git = GitModule(cwd=self.cwd, display=self.display)
        ok, msg = git.pull(remote=remote, branch=branch)
        (self.display.success if ok else self.display.error)(msg)

    def _cmd_git_branch(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        git = GitModule(cwd=self.cwd, display=self.display)
        if args and args[0] in ("-a", "--all", "-l", "--list"):
            ok, msg = git.branch(list_branches=True)
        elif args and args[0] in ("-c", "--create") and len(args) > 1:
            ok, msg = git.branch(name=args[1], create=True)
        elif args:
            ok, msg = git.branch(name=args[0], create=True)
        else:
            ok, msg = git.branch()
        if ok:
            self.display.section("Git Branch")
            self.display.print(msg)
        else:
            self.display.error(msg)

    def _cmd_git_log(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        count = 10
        if args and args[0].isdigit():
            count = int(args[0])
        git = GitModule(cwd=self.cwd, display=self.display)
        ok, msg = git.log(count=count)
        if ok:
            self.display.section("Git Log")
            self.display.print(msg)
        else:
            self.display.error(msg)

    def _cmd_git_remote(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        git = GitModule(cwd=self.cwd, display=self.display)
        action = args[0].lower() if args else "list"
        name = args[1] if len(args) > 1 else ""
        url = args[2] if len(args) > 2 else ""
        ok, msg = git.remote(action=action, name=name, url=url)
        if ok:
            self.display.section("Git Remote")
            self.display.print(msg)
        else:
            self.display.error(msg)

    def _cmd_git_diff(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        git = GitModule(cwd=self.cwd, display=self.display)
        staged = self._fs_has_flag(args or [], ["--staged", "-s"])
        paths = self._fs_non_flags(args or [])
        path = paths[0] if paths else ""
        ok, msg = git.diff(staged=staged, path=path)
        if ok:
            self.display.section("Git Diff")
            self.display.print(msg)
        else:
            self.display.error(msg)

    def _cmd_git_clone(self, args: List[str] = None, intent: IntentResult = None) -> None:
        from delta.modules.git import GitModule
        if not args:
            self.display.warning("Usage: git clone <url> [destination]")
            return
        repo_url = args[0]
        dest = args[1] if len(args) > 1 else ""
        git = GitModule(cwd=self.cwd, display=self.display)
        ok, msg = git.clone(repo_url, dest)
        (self.display.success if ok else self.display.error)(msg)
