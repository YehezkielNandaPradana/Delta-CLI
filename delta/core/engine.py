# delta/core/engine.py
"""
Main Delta engine - REPL loop, command dispatch, and AI integration.
"""

import sys
import os
import shlex
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from delta.core.config import DeltaConfig
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.core.display import DisplayManager, ANSI
from delta.core.plugin import PluginManager, PluginBase
from delta.ai.intent import IntentEngine, IntentResult


# Try to import prompt_toolkit for enhanced input
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.styles import Style
    HAS_PROMPT_TOOLKIT = True
except ImportError:
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
        """
        self.config = config
        self.database = database
        self.session = session
        self.intent_engine = intent_engine
        self.plugin_manager = plugin_manager
        self.display = display
        self.running = False

        # Command handlers registration
        self._builtin_commands: Dict[str, callable] = {}
        self._register_builtin_commands()

        # Load plugins
        if self.plugin_manager:
            loaded = self.plugin_manager.load_all()
            if loaded:
                self.display.debug(f"Loaded {len(loaded)} plugin(s)")

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
        }
        self._builtin_commands.update(commands)

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

                prompt_session = PromptSession(
                    history=FileHistory(history_path),
                    auto_suggest=AutoSuggestFromHistory(),
                    style=prompt_style,
                    enable_history_search=True,
                )
            except Exception:
                prompt_session = None

        self.display.success("Delta AI Engine initialized successfully")
        self.display.info("Type 'help' for available commands, 'exit' to quit")
        self.display.info(f"Session: {self.session.session_id}")
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

    def _process_input(self, user_input: str) -> None:
        """
        Process user input through AI engine and dispatch to appropriate handler.

        Args:
            user_input: Raw user input string
        """
        # Add to conversation
        self.session.add_conversation("user", user_input)

        # Process through AI intent engine
        intent = self.intent_engine.process(user_input, self.session.context)

        if intent:
            # Handle with AI guidance
            self._execute_with_ai(intent, user_input)
        else:
            # Try direct command dispatch
            self._dispatch_command(user_input)

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

    def _dispatch_command(self, raw: str) -> None:
        """Direct command dispatch without AI processing."""
        parts = shlex.split(raw)
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

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
            # Try AI to interpret
            intent = self.intent_engine.process(raw, self.session.context)
            if intent and intent.confidence > 0.5:
                self._execute_with_ai(intent, raw)
            else:
                self.display.warning(f"Unknown command: {cmd}")
                self.display.info("Type 'help' for available commands")

    def _cmd_help(self, args: List[str] = None, intent: IntentResult = None) -> None:
        """Display help information."""
        self.display.section("Delta Commands")

        categories = {
            "🔍 Scanning": [
                ("scan <target>", "Scan target (host, ports, services)"),
                ("audit <target>", "Full security audit of target"),
                ("enumerate <target>", "Enumerate network/host information"),
                ("check <target>", "Check specific security aspects"),
            ],
            "🌐 Network": [
                ("dns <domain>", "DNS lookup (A, AAAA, MX, NS, TXT)"),
                ("whois <domain>", "WHOIS lookup"),
                ("ping <host>", "Ping sweep"),
                ("traceroute <host>", "Trace route to host"),
                ("ssl <host>", "SSL/TLS certificate check"),
            ],
            "🛡 Security": [
                ("analyze <target>", "Analyze scan results"),
                ("explain <vulnerability>", "Explain a vulnerability"),
                ("password <password>", "Analyze password strength"),
                ("jwt <token>", "Decode JWT token"),
            ],
            "🔧 Utilities": [
                ("decode <type> <data>", "Decode base64/hex/url"),
                ("encode <type> <data>", "Encode base64/hex/url"),
                ("hash <data>", "Identify/generate hashes"),
            ],
            "📊 Reports": [
                ("report", "Generate security report"),
                ("history", "Show command history"),
                ("session", "Show current session info"),
            ],
            "⚙ System": [
                ("config", "Show/manage configuration"),
                ("plugins", "List loaded plugins"),
                ("clear", "Clear screen"),
                ("version", "Show version info"),
                ("exit/quit", "Exit Delta"),
            ],
        }

        for category, cmds in categories.items():
            self.display.print(f"\n  {ANSI.BOLD}{category}{ANSI.RESET}")
            for cmd, desc in cmds:
                self.display.print(f"    {ANSI.CYAN}{cmd:<30}{ANSI.RESET} {desc}")

        self.display.print()
        self.display.info("💡 Delta understands natural language. Try:")
        self.display.print('    "scan localhost"')
        self.display.print('    "check security server 192.168.1.1"')
        self.display.print('    "audit website on port 8080"')

    def _cmd_scan(self, args: List[str], intent: IntentResult = None) -> None:
        """Execute scanning module."""
        from delta.modules.scanner import ScannerModule
        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:
            self.display.warning("No target specified. Usage: scan <target>")
            return

        self.session.set_host(target)
        scanner = ScannerModule(self.config, self.database, self.session, self.display)
        result = scanner.scan(target, intent)
        
        if result:
            self.session.set_scan_result(target, result)
            self.session.add_to_history(f"scan {target}", host=target, result_summary=f"Scan completed for {target}")
        
        self.session.save()

    def _cmd_audit(self, args: List[str], intent: IntentResult = None) -> None:
        """Execute full audit module."""
        from delta.modules.scanner import ScannerModule
        target = intent.target if intent else (args[0] if args else self.session.get_host())

        if not target:
            self.display.warning("No target specified. Usage: audit <target>")
            return

        self.session.set_host(target)
        scanner = ScannerModule(self.config, self.database, self.session, self.display)
        result = scanner.full_audit(target, intent)
        
        if result:
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

    def _cmd_clear(self, args: List[str] = None, intent: IntentResult = None) -> None:
        """Clear the screen."""
        os.system("clear" if os.name != "nt" else "cls")
        self.display.print("Screen cleared")
    def _cmd_dns(self, args: List[str], intent: IntentResult = None) -> None:
        """DNS lookup command."""
        from delta.modules.dns import DNSModule
        target = intent.target if intent else (args[0] if args else self.session.get_host())
        
        if not target:
            self.display.warning("No target specified. Usage: dns <domain>")
            return
        
        dns = DNSModule()
        result = dns.get_all_dns(target)
        
        if result.ip:
            self.display.info(f"IP: {result.ip}")
        if result.a_records:
            self.display.info(f"A Records: {', '.join(result.a_records)}")
        if result.mx_records:
            self.display.info(f"MX Records: {', '.join(result.mx_records)}")
        if result.ns_records:
            self.display.info(f"NS Records: {', '.join(result.ns_records)}")

    def _cmd_ssl(self, args: List[str], intent: IntentResult = None) -> None:
        """SSL certificate check command."""
        from delta.modules.ssl import SSLModule
        target = intent.target if intent else (args[0] if args else self.session.get_host())
        
        if not target:
            self.display.warning("No target specified. Usage: ssl <host>")
            return
        
        ssl_mod = SSLModule()
        info = ssl_mod.check(target)
        
        if info.valid:
            self.display.info(f"Subject: {info.subject}")
            self.display.info(f"Issuer: {info.issuer}")
            self.display.info(f"Valid: {info.not_before} to {info.not_after}")
            self.display.info(f"Expired: {info.expired}")
            self.display.info(f"Protocol: {info.protocol}")
        else:
            self.display.warning(f"SSL check failed: {info.errors}")

    def _cmd_ping(self, args: List[str], intent: IntentResult = None) -> None:
        """Ping command."""
        from delta.modules.network import NetworkModule
        target = intent.target if intent else (args[0] if args else self.session.get_host())
        
        if not target:
            self.display.warning("No target specified. Usage: ping <host>")
            return
        
        net = NetworkModule()
        result = net.ping(target)
        
        if result.alive:
            self.display.success(f"Host {target} is alive (RTT: {result.rtt_ms}ms)")
        else:
            self.display.warning(f"Host {target} is not responding")

    def _cmd_encode(self, args: List[str], intent: IntentResult = None) -> None:
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
        else:
            self.display.warning(f"Unknown encode type: {enc_type}")
            return
        
        if result.success:
            self.display.success(f"Encoded: {result.result}")
        else:
            self.display.error(result.error)

    def _cmd_decode(self, args: List[str], intent: IntentResult = None) -> None:
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
        else:
            self.display.warning(f"Unknown decode type: {dec_type}")
            return
        
        if result.success:
            self.display.success(f"Decoded: {result.result}")
        else:
            self.display.error(result.error)

    def _cmd_hash(self, args: List[str], intent: IntentResult = None) -> None:
        """Hash operations command."""
        from delta.modules.crypto import CryptoModule
        
        if not args:
            self.display.warning("Usage: hash <type> <data>")
            return
        
        crypto = CryptoModule()
        
        if len(args) == 1:
            result = crypto.identify_hash(args[0])
            if result.matches:
                self.display.info(f"Possible types: {', '.join(result.possible_types)}")
            else:
                self.display.warning("Could not identify hash type")
        elif len(args) >= 2:
            algo = args[0].lower()
            data = " ".join(args[1:])
            result = crypto.generate_hash(data, algo)
            if result.success:
                self.display.success(f"{result.hash_type}: {result.generated}")
            else:
                self.display.error(result.generated)

    def _cmd_password(self, args: List[str], intent: IntentResult = None) -> None:
        """Password analysis command."""
        from delta.modules.crypto import CryptoModule
        
        if not args:
            self.display.warning("Usage: password <password>")
            return
        
        password = " ".join(args)
        crypto = CryptoModule()
        result = crypto.analyze_password(password)
        
        self.display.info(f"Password length: {result.length}")
        self.display.info(f"Entropy: {result.entropy:.1f} bits")
        self.display.info(f"Strength: {result.strength}")
        self.display.info(f"Score: {result.score}/5")
        self.display.info(f"Crack time estimate: {result.crack_time}")

    def _cmd_jwt(self, args: List[str], intent: IntentResult = None) -> None:
        """JWT decode command."""
        from delta.modules.encode import EncodeModule
        
        if not args:
            self.display.warning("Usage: jwt <token>")
            return
        
        token = " ".join(args)
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
