# delta/main.py

"""

Main entry point for Delta CLI application.

Supports direct command execution and interactive REPL mode.

"""

import sys

import os
import urllib.error

import argparse

import socket

from typing import Optional
from functools import lru_cache

# Windows console (cp1252) crashes on emoji — force UTF-8 with safe fallback.
if getattr(sys.stdout, "reconfigure", None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if getattr(sys.stderr, "reconfigure", None):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from delta import __version__

from delta import __version__

from delta.core.config import DeltaConfig

from delta.core.engine import DeltaEngine

from delta.core.database import Database

from delta.core.session import SessionManager

from delta.core.display import DisplayManager

from delta.ai.intent import IntentEngine

from delta.ai.llm import LLMEngine

from delta.ai.memory import MemoryManager

from delta.core.plugin import PluginManager

from delta.core.auth import login_required

from delta.core.tui import DeltaTUI

from delta.utils.router_manager import is_9router_running, start_9router, wait_for_9router

def build_parser() -> argparse.ArgumentParser:

    """Build the argument parser for Delta CLI."""

    parser = argparse.ArgumentParser(

        prog="delta",

        description="Delta - AI-Powered Cyber Security Assessment CLI",

        epilog="Run without arguments to start the interactive REPL.",

        formatter_class=argparse.RawDescriptionHelpFormatter,

    )

    parser.add_argument(

        "-V", "--version",

        action="version",

        version=f"Delta Security Assessment CLI v{__version__}",

        help="Show version information and exit",

    )

    parser.add_argument(

        "--web",

        action="store_true",

        help="Start the web chat interface instead of the TUI",

    )

    parser.add_argument(

        "command",

        nargs="?",

        help="Command to execute (e.g., scan, audit, dns, ping, help)",

    )

    parser.add_argument(

        "args",

        nargs=argparse.REMAINDER,

        help="Arguments for the command",

    )

    return parser

def create_engine(config_path: Optional[str] = None) -> DeltaEngine:

    """Create and initialize the Delta engine with all components."""

    config = DeltaConfig()

    config.load(config_path)

    display = DisplayManager()

    db_path = os.path.join(config.data_dir, "delta.db")

    database = Database(db_path)

    database.initialize()

    session = SessionManager(database)

    intent_engine = IntentEngine(config, database)

    plugin_manager = PluginManager(config.plugin_dir)

    memory_dir = os.path.join(config.data_dir, "memory")

    memory_manager = MemoryManager(memory_dir, max_sessions=config.max_sessions)

    llm_engine = LLMEngine(

        api_key=config.llm_api_key,

        base_url=config.llm_api_base_url or None,

        model=config.llm_model or None,

        provider=config.llm_provider or None,

        memory_manager=memory_manager,

        memory_enabled=config.memory_enabled,

        max_retries=config.llm_max_retries,

        retry_backoff_factor=config.llm_retry_backoff_factor,

        retry_initial_delay=config.llm_retry_initial_delay,

        retry_max_delay=config.llm_retry_max_delay,

    )

    if not config.llm_enabled and llm_engine.is_configured:

        config.llm_enabled = True

        config.save()

    _fallback_ai_if_needed(llm_engine, display)

    engine = DeltaEngine(

        config=config,

        database=database,

        session=session,

        intent_engine=intent_engine,

        plugin_manager=plugin_manager,

        display=display,

        llm_engine=llm_engine,

    )

    # First-run setup: prompt for API key if not configured

    if config.first_run and not llm_engine.is_configured:

        _first_run_setup(config, llm_engine, display)

    return engine

def _fallback_ai_if_needed(llm_engine: LLMEngine, display: DisplayManager) -> None:
    """Jika 9Router tidak bisa dipakai (mati / butuh key), alihkan ke Ollama lokal agar AI tetap jalan."""
    if llm_engine.provider != "9router":
        return
    if not llm_engine._check_connectivity(timeout=2):
        try:
            socket.create_connection(("127.0.0.1", 11434), timeout=2).close()
        except OSError:
            return
        llm_engine.provider = "local"
        llm_engine.base_url = "http://localhost:11434/v1"
        llm_engine.api_key = ""
        llm_engine.model = _pick_fast_ollama_model() or "qwen2.5:3b"
        llm_engine._system_prompt = llm_engine._build_system_prompt()
        llm_engine._refresh_system_message()
        display.warning(f"9Router tidak tersedia — otomatis beralih ke Ollama lokal ({llm_engine.model}). Gunakan /model untuk ganti.")
        return
    probe_failed = False
    try:
        probe = llm_engine._call_api()
    except urllib.error.HTTPError as e:
        if e.code not in (401, 403):
            return
        probe_failed = True
    except Exception:
        probe_failed = True

    if not probe_failed:
        return

    try:
        socket.create_connection(("127.0.0.1", 11434), timeout=2).close()
    except OSError:
        return
    llm_engine.provider = "local"
    llm_engine.base_url = "http://localhost:11434/v1"
    llm_engine.api_key = ""
    llm_engine.model = _pick_fast_ollama_model() or "qwen2.5:3b"
    llm_engine._system_prompt = llm_engine._build_system_prompt()
    llm_engine._refresh_system_message()
    display.warning(f"9Router butuh API key — otomatis beralih ke Ollama lokal ({llm_engine.model}). Gunakan /key untuk set key 9Router.")

def _pick_fast_ollama_model() -> str:
    """Pilih model Ollama lokal yang paling kecil/cepat dan tersedia."""
    try:
        import urllib.request, json
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "Delta-CLI/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return ""
    preference = ["qwen2.5:3b", "qwen2.5:1.5b", "qwen2.5:0.5b", "gemma3:1b", "gemma3:4b", "llama3.2:1b", "llama3.2:3b", "phi4-mini", "tinyllama", "gemma4:12b", "qwen2.5", "gemma4"]
    for name in preference:
        if name in models:
            return name
    return models[0] if models else ""

def _first_run_setup(config: DeltaConfig, llm_engine: LLMEngine, display: DisplayManager) -> None:

    display.section("First-Time Setup")

    display.info("Welcome to Delta! Let's set up your AI provider.")

    from delta.ai.llm import PROVIDERS

    display.print()

    display.print("Available providers:")

    for name, info in PROVIDERS.items():

        display.print(f"  {name:20} - {info['description']}")

    provider = input(f"\nProvider [{config.llm_provider}]: ").strip() or config.llm_provider

    pinfo = PROVIDERS.get(provider)

    if pinfo:

        config.llm_provider = provider

        config.llm_api_base_url = pinfo["base_url"]

        llm_engine.provider = provider

        llm_engine.base_url = pinfo["base_url"]

        if pinfo.get("default_model"):

            config.llm_model = pinfo["default_model"]

            llm_engine.model = pinfo["default_model"]

    if not pinfo or not pinfo.get("requires_key", True):

        display.info("This provider does not require an API key — skipping.")

    else:

        api_key = input("API Key: ").strip()

        if api_key:

            config.llm_api_key = api_key

            llm_engine.api_key = api_key

    owner = input("Nama panggilan [Tuan]: ").strip() or "Tuan"

    config.set("owner_name", owner)

    if llm_engine:

        llm_engine.add_system_context(f"User adalah {owner}, pemilik dan tuan dari Delta.")

    config.first_run = False

    config.save()

    if llm_engine.is_configured:

        display.success("Setup complete! AI mode is ready.")

        if not config.llm_enabled:

            config.llm_enabled = True

            config.save()

            display.info("AI LLM mode enabled automatically")

    else:

        display.warning("Setup incomplete - no API key configured.")

        display.info("Use /key <your-key> later to set it up.")

def run_web_chat() -> None:

    """Run the web chat/dashboard interface."""

    from delta.web.server import start_web_server

    engine = create_engine()

    start_web_server(engine=engine, host="127.0.0.1", port=8000)
def execute_direct(engine: DeltaEngine, cmd: str, cmd_args: list) -> None:

    """Execute a command directly and exit."""

    full_command = cmd

    if cmd_args:

        full_command = f"{cmd} {' '.join(cmd_args)}"

    engine._dispatch_command(full_command)

def main() -> None:

    """Main entry point for Delta CLI."""

    parser = build_parser()

    try:

        args, unknown = parser.parse_known_args()

    except SystemExit:

        sys.exit(0)

    try:

        # Auto-start 9Router so Delta always routes through it

        if not is_9router_running():

            print("[*] Starting 9Router local AI routing gateway...")

            start_9router()

            if not wait_for_9router(30.0):

                print("[!] 9Router did not start in time — Delta will still run but AI may be unavailable.")

            else:

                print("[*] 9Router is running at http://localhost:20128")

        # Web chat mode requested

        if args.web:

            run_web_chat()

            return

        # If no command provided, start interactive REPL

        if not args.command:

            engine = create_engine()

            tui = DeltaTUI(engine)

            # TODO(login): login gate disabled temporarily; re-enable with:

            #   if not tui.show_login(engine.config):

            #       print("\\n[!] Access denied. Exiting.")

            #       sys.exit(1)

            welcome = "  Delta AI Engine initialized successfully"

            if engine.llm_engine and engine.llm_engine.is_configured and engine.config.llm_enabled:

                welcome += "  •  AI LLM Mode: ACTIVE"

            if engine.policy and engine.policy.policy.get("enabled", True):

                welcome += "\\n  ⚖ Authorized security testing only — ketik 'policy' untuk batas kemampuan Delta"

            tui.run(welcome)

            return

        # Direct command execution mode

        engine = create_engine()

        # Combine known args with unknown (remainder) args

        cmd_args = args.args + unknown

        # Handle --help for specific commands

        if args.command in ("-h", "--help"):

            parser.print_help()

            return

        execute_direct(engine, args.command, cmd_args)

        sys.exit(0)

    except KeyboardInterrupt:

        print("\\n\\n[!] Delta shutdown requested. Goodbye!")

        sys.exit(0)

    except Exception as e:

        print(f"\\n[!] Fatal error: {e}")

        sys.exit(1)

if __name__ == "__main__":

    main()