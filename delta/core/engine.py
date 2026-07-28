# delta/core/engine.py
"""
Main Delta engine - REPL loop, command dispatch, and AI integration.
"""

import sys
import os
import shlex
import time
import random
import shutil
from datetime import datetime
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

        self.last_result: Any = None
        self.last_command: str = ""
        self.session_start = datetime.now()
        self._timer_start: Optional[float] = None

        # Command aliases
        self._aliases: Dict[str, str] = {
            "q": "quit", "x": "exit", "h": "help", "?": "help",
            "cls": "clear", "hist": "history", "ls": "history",
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

    def _process_input(self, user_input: str) -> None:
        """
        Process user input through AI engine and dispatch to appropriate handler.

        Args:
            user_input: Raw user input string
        """
        self.last_command = user_input

        # Check aliases
        first_word = user_input.split()[0].lower() if user_input.split() else ""
        if first_word in self._aliases:
            alias_target = self._aliases[first_word]
            user_input = alias_target + user_input[len(first_word):]

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

        if not result:
            self.display.warning(f"Scan failed for {target}")
            return

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

    def _cmd_traceroute(self, args: List[str], intent: IntentResult = None) -> None:
        """Trace route to host command."""
        from delta.modules.network import NetworkModule
        target = intent.target if intent else (args[0] if args else self.session.get_host())
        if not target:
            self.display.warning("No target specified. Usage: traceroute <host>")
            return
        self.display.info(f"Tracing route to {target}...")
        net = NetworkModule()
        result = net.traceroute(target)
        if result and result.hops:
            self.display.section(f"Traceroute to {target}")
            for hop in result.hops:
                self.display.print(f"  {hop['ttl']:<4} {hop['host']:<40} {hop['rtt']}ms")
        else:
            self.display.warning("Traceroute failed or no response")

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
            if result.matches:
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
        for fmt_name, path in generated.items():
            self.display.success(f"Report saved: {path}")

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
                self.display.warning("whois command not found on this system")
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
        self.display.info("Delta Security Assessment CLI v1.0.0")
        self.display.info("Author: HackerAI")
        self.display.info("License: MIT")

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
                self.display.print(f"  {key}: {value}")
        else:
            if len(args) >= 2:
                key = args[0]
                value = args[1]
                self.config.set(key, value)
                self.config.save()
                self.display.success(f"Config updated: {key} = {value}")

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
        self.display.panel("Message of the Day", "Stay secure, stay vigilant.\nDelta is your AI-powered security assessment tool.\nAlways ensure you have proper authorization before testing.", style="info")

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
        if not self.last_command:
            self.display.warning("No previous command to repeat")
            return
        cmd = self.last_command
        if self.last_command.lower().startswith(("repeat", "again")):
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
            ("Ctrl+C", "Cancel current input"),
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

    def _cmd_banner(self, args: List[str] = None, intent: IntentResult = None) -> None:
        """Display the Delta banner again."""
        self.display.show_banner()
