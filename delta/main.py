# delta/main.py
"""
Main entry point for Delta CLI application.
Handles initialization, banner display, and the main REPL loop.
"""

import sys
import os
from typing import Optional

from delta.core.config import DeltaConfig
from delta.core.engine import DeltaEngine
from delta.core.database import Database
from delta.core.session import SessionManager
from delta.core.display import DisplayManager
from delta.ai.intent import IntentEngine
from delta.core.plugin import PluginManager


def main() -> None:
    """Main entry point for Delta CLI."""
    try:
        # Initialize configuration
        config = DeltaConfig()
        config.load()

        # Initialize display
        display = DisplayManager()
        display.show_banner()

        # Initialize database
        db_path = os.path.join(config.data_dir, "delta.db")
        database = Database(db_path)
        database.initialize()

        # Initialize session
        session = SessionManager(database)

        # Initialize AI engine
        intent_engine = IntentEngine(config, database)

        # Initialize plugin manager
        plugin_manager = PluginManager(config.plugin_dir)

        # Initialize main engine
        engine = DeltaEngine(
            config=config,
            database=database,
            session=session,
            intent_engine=intent_engine,
            plugin_manager=plugin_manager,
            display=display,
        )

        # Start REPL
        engine.run()

    except KeyboardInterrupt:
        print("\n\n[!] Delta shutdown requested. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()