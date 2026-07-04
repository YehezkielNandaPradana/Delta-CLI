# delta/core/plugin.py
"""
Plugin management system for Delta.
Discovers and loads plugins from the plugin directory using importlib.
"""

import os
import sys
import importlib
import importlib.util
import inspect
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from pathlib import Path


class PluginBase:
    """
    Base class for all Delta plugins.
    All plugins must inherit from this class and implement the required methods.
    """

    @property
    def name(self) -> str:
        """Plugin name - override in subclass."""
        return self.__class__.__name__

    @property
    def version(self) -> str:
        """Plugin version - override in subclass."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Plugin description - override in subclass."""
        return ""

    @property
    def author(self) -> str:
        """Plugin author - override in subclass."""
        return "Unknown"

    @property
    def commands(self) -> List[str]:
        """List of commands this plugin handles."""
        return []

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass

    def execute(self, command: str, args: List[str], context: Dict[str, Any]) -> str:
        """
        Execute plugin functionality.

        Args:
            command: The command to execute
            args: Command arguments
            context: Current session context

        Returns:
            Result string
        """
        raise NotImplementedError("Plugin must implement execute()")


@dataclass
class PluginInfo:
    """Information about a loaded plugin."""
    name: str
    version: str
    description: str
    author: str
    commands: List[str]
    module_path: str
    instance: Any


class PluginManager:
    """
    Discovers, loads, and manages Delta plugins.
    Uses importlib for dynamic loading from the plugin directory.
    """

    def __init__(self, plugin_dir: str):
        """
        Initialize plugin manager.

        Args:
            plugin_dir: Path to plugin directory
        """
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, PluginInfo] = {}
        self._command_map: Dict[str, str] = {}

        # Ensure plugin directory exists
        os.makedirs(self.plugin_dir, exist_ok=True)

        # Create __init__.py if it doesn't exist
        init_file = os.path.join(self.plugin_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# Delta plugins package\n")

    def discover(self) -> List[str]:
        """
        Discover plugins in the plugin directory.

        Returns:
            List of discovered plugin names
        """
        discovered = []
        plugin_dir_path = Path(self.plugin_dir)

        for item in plugin_dir_path.iterdir():
            if item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                discovered.append(item.stem)
            elif item.is_dir() and not item.name.startswith("_"):
                init_file = item / "__init__.py"
                if init_file.exists():
                    discovered.append(item.name)

        return discovered

    def load_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        Load a specific plugin by name.

        Args:
            plugin_name: Name of the plugin module

        Returns:
            PluginInfo if loaded successfully, None otherwise
        """
        try:
            # Add plugin directory to path if not already
            if self.plugin_dir not in sys.path:
                sys.path.insert(0, self.plugin_dir)

            # Import the plugin module
            module = importlib.import_module(plugin_name)

            # Find PluginBase subclasses
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and issubclass(obj, PluginBase)
                        and obj is not PluginBase):
                    plugin_classes.append(obj)

            if not plugin_classes:
                return None

            # Instantiate and register each plugin class
            for plugin_class in plugin_classes:
                instance = plugin_class()
                instance.on_load()

                info = PluginInfo(
                    name=instance.name,
                    version=instance.version,
                    description=instance.description,
                    author=instance.author,
                    commands=instance.commands,
                    module_path=os.path.join(self.plugin_dir, f"{plugin_name}.py"),
                    instance=instance,
                )

                self.plugins[instance.name] = info

                # Register commands
                for cmd in instance.commands:
                    self._command_map[cmd.lower()] = instance.name

            return self.plugins.get(plugin_classes[0].__name__)

        except Exception as e:
            print(f"[!] Failed to load plugin '{plugin_name}': {e}")
            return None

    def load_all(self) -> List[PluginInfo]:
        """
        Discover and load all plugins.

        Returns:
            List of loaded plugin information
        """
        discovered = self.discover()
        loaded = []

        for plugin_name in discovered:
            info = self.load_plugin(plugin_name)
            if info:
                loaded.append(info)

        return loaded

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if unloaded successfully
        """
        if plugin_name in self.plugins:
            info = self.plugins[plugin_name]
            try:
                info.instance.on_unload()
            except Exception:
                pass

            # Remove command mappings
            for cmd in info.commands:
                if cmd.lower() in self._command_map:
                    del self._command_map[cmd.lower()]

            del self.plugins[plugin_name]
            return True
        return False

    def get_plugin_for_command(self, command: str) -> Optional[Any]:
        """
        Get plugin instance that handles a command.

        Args:
            command: Command to look up

        Returns:
            Plugin instance or None
        """
        cmd_lower = command.lower()
        if cmd_lower in self._command_map:
            plugin_name = self._command_map[cmd_lower]
            if plugin_name in self.plugins:
                return self.plugins[plugin_name].instance
        return None

    def list_plugins(self) -> List[PluginInfo]:
        """Get list of all loaded plugins."""
        return list(self.plugins.values())

    def is_command_handled(self, command: str) -> bool:
        """Check if a command is handled by any plugin."""
        return command.lower() in self._command_map