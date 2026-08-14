# delta/core/config.py

"""

Configuration management for Delta.

Handles YAML/JSON config loading with sensible defaults.

"""

import json

import os

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any, Dict, List, Optional

from functools import lru_cache

from delta.ai.protocols import MODEL_PRESETS

@dataclass

class DeltaConfig:

    """Application configuration with type-safe access."""

    # Paths

    data_dir: str = field(default_factory=lambda: os.path.join(os.path.expanduser("~"), ".delta"))

    config_dir: str = ""

    plugin_dir: str = ""

    log_dir: str = ""

    cache_dir: str = ""

    template_dir: str = ""

    # General settings

    debug: bool = False

    verbose: bool = False

    timeout: int = 30

    max_threads: int = 50

    default_ports: str = "21,22,23,25,53,80,110,143,443,445,993,995,1433,1521,2049,3306,3389,5432,5900,8080,8443,9090,27017"

    # AI settings

    ai_enabled: bool = True

    context_memory_size: int = 100

    auto_suggest: bool = True

    # LLM settings

    llm_api_key: str = ""

    llm_api_base_url: str = "http://localhost:11434/v1"

    llm_model: str = "gemma4:12b"

    llm_provider: str = "local"  # local ollama is default

    llm_enabled: bool = True

    llm_max_retries: int = 3

    llm_retry_backoff_factor: float = 2.0

    llm_retry_initial_delay: float = 1.0

    llm_retry_max_delay: float = 30.0

    # Memory settings

    memory_enabled: bool = True

    max_sessions: int = 50

    # Skill settings

    active_skills: List[str] = field(default_factory=list)

    # First run tracking

    first_run: bool = True

    # Auth settings

    auth_enabled: bool = True

    auth_username: str = ""

    auth_password_salt: str = ""

    auth_password_hash: str = ""

    # Display settings

    color_enabled: bool = True

    animation_enabled: bool = True

    typing_speed: float = 0.02

    prompt_symbol: str = "D"

    # Report settings

    report_company: str = "Delta Security"

    report_author: str = "Delta Analyst"

    # Internal state (not from config file)

    _loaded: bool = False

    _raw_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:

        """Set derived paths after initialization."""

        if not self.config_dir:

            self.config_dir = os.path.join(self.data_dir, "config")

        if not self.plugin_dir:

            self.plugin_dir = os.path.join(self.data_dir, "plugins")

        if not self.log_dir:

            self.log_dir = os.path.join(self.data_dir, "logs")

        if not self.cache_dir:

            self.cache_dir = os.path.join(self.data_dir, "cache")

        if not self.template_dir:

            self.template_dir = os.path.join(self.data_dir, "templates")

    def load(self, config_path: Optional[str] = None) -> "DeltaConfig":

        """

        Load configuration from file, merging with defaults.

        Args:

            config_path: Optional path to config file. If None,

                        searches default locations.

        Returns:

            Self for method chaining.

        """

        # Create data directory if it doesn't exist

        os.makedirs(self.data_dir, exist_ok=True)

        # Try loading .env file first (always)

        self._load_dotenv()

        # Search for config file

        if config_path is None:

            config_path = os.path.join(self.config_dir, "config.json")

        # Create default config if not exists

        if not os.path.exists(config_path):

            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            self._save_default(config_path)

        # Load config from file

        try:

            if os.path.exists(config_path):

                with open(config_path, "r") as f:

                    raw = json.load(f)

                    self._raw_config = raw

                    for key, value in raw.items():

                        if hasattr(self, key):

                            setattr(self, key, value)

        except (json.JSONDecodeError, IOError) as e:

            print(f"[!] Warning: Could not load config: {e}")

        # Override with environment variables if set

        env_map = {

            "DELTA_API_KEY": "llm_api_key",

            "OPENCODE_API_KEY": "llm_api_key",

            "DEEPSEEK_API_KEY": "llm_api_key",

            "OPENAI_API_KEY": "llm_api_key",

            "DELTA_API_BASE_URL": "llm_api_base_url",

            "OPENCODE_BASE_URL": "llm_api_base_url",

            "DEEPSEEK_BASE_URL": "llm_api_base_url",

            "DELTA_LLM_MODEL": "llm_model",

            "DEEPSEEK_MODEL": "llm_model",

            "DELTA_PROVIDER": "llm_provider",

        }

        for env_key, config_key in env_map.items():

            env_val = os.environ.get(env_key)

            if env_val and hasattr(self, config_key):

                setattr(self, config_key, env_val)

        # Clean bad URLs from config

        self._clean_bad_urls()

        # Migrate to 9Router as the default provider

        self._migrate_to_9router()

    def _migrate_to_9router(self) -> None:

        """Ensure Delta always uses 9Router as its LLM provider."""

        self.llm_provider = "9router"

        self.llm_api_base_url = "http://localhost:20128/v1"

        self.llm_enabled = True

        if not self.llm_model or self.llm_model not in [k for k in MODEL_PRESETS if "/" in k] + ["KiloCombo"]:

            self.llm_model = "DeepseekCombo"

        self._loaded = True

    def _clean_bad_urls(self) -> None:

        bad_urls = ["https://test.api.com/v1", "http://test.api.com/v1", "https://localhost:8080"]

        if self.llm_api_base_url in bad_urls:

            self.llm_api_base_url = ""

        if "localhost:20128" in self.llm_api_base_url:

            return

        local_provider = self.llm_provider in ("local", "lmstudio", "9router")

        if self.llm_api_base_url and ("test." in self.llm_api_base_url or "localhost" in self.llm_api_base_url):

            if not local_provider and "opencode" not in self.llm_api_base_url and "deepseek" not in self.llm_api_base_url and "openai" not in self.llm_api_base_url:

                self.llm_api_base_url = ""

    def _load_dotenv(self) -> None:

        for path in [".env", os.path.join(self.data_dir, ".env")]:

            env_path = os.path.abspath(path)

            if os.path.isfile(env_path):

                try:

                    with open(env_path, "r") as f:

                        for line in f:

                            line = line.strip()

                            if not line or line.startswith("#") or "=" not in line:

                                continue

                            key, _, val = line.partition("=")

                            key = key.strip()

                            val = val.strip().strip("\"'")

                            if key not in os.environ:

                                os.environ[key] = val

                except IOError:

                    pass

        # Ensure all directories exist

        for d in [self.data_dir, self.config_dir, self.plugin_dir,

                  self.log_dir, self.cache_dir, self.template_dir]:

            os.makedirs(d, exist_ok=True)

        self._loaded = True

        return self

    def save(self, config_path: Optional[str] = None) -> None:

        """Save current configuration to file."""

        if config_path is None:

            config_path = os.path.join(self.config_dir, "config.json")

        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        config_dict = {

            k: v for k, v in self.__dict__.items()

            if not k.startswith("_")

        }

        with open(config_path, "w") as f:

            json.dump(config_dict, f, indent=2)

    def _save_default(self, path: str) -> None:

        """Save default configuration."""

        config_dict = {

            k: v for k, v in self.__dict__.items()

            if not k.startswith("_")

        }

        with open(path, "w") as f:

            json.dump(config_dict, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:

        """Get config value by key with optional default."""

        return getattr(self, key, default)

    def set(self, key: str, value: Any) -> None:

        """Set config value."""

        if hasattr(self, key):

            setattr(self, key, value)

    @property

    def is_loaded(self) -> bool:

        """Check if configuration has been loaded."""

        return self._loaded