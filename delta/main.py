# delta/main.py
"""
Main entry point for Delta CLI application.
Supports direct command execution and interactive REPL mode.
"""

import sys
import os
import argparse
from typing import Optional

from delta import __version__
from delta.core.config import DeltaConfig
from delta.core.engine import DeltaEngine
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.core.display import DisplayManager
from delta.ai.intent import IntentEngine
from delta.core.plugin import PluginManager


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

    engine = DeltaEngine(
        config=config,
        database=database,
        session=session,
        intent_engine=intent_engine,
        plugin_manager=plugin_manager,
        display=display,
    )

    return engine


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
        # If no command provided, start interactive REPL
        if not args.command:
            engine = create_engine()
            engine.display.show_banner()
            engine.display.success("Delta AI Engine initialized successfully")
            engine.display.info("Type 'help' for available commands, 'exit' to quit")
            engine.run()
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
        print("\n\n[!] Delta shutdown requested. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()