import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any
from datetime import datetime

from delta.ai.memory import MemoryManager


PROVIDERS = {
    "local": {
        "base_url": "http://localhost:11434/v1",
        "description": "Ollama - Free local LLM (no API key required)",
        "default_model": "qwen2.5:7b",
        "env_key": "",
        "requires_key": False,
    },
    "lmstudio": {
        "base_url": "http://localhost:1234/v1",
        "description": "LM Studio - Local LLM server (no API key required)",
        "default_model": "local-model",
        "env_key": "",
        "requires_key": False,
    },
    "opencode-zen": {
        "base_url": "https://opencode.ai/zen/v1",
        "description": "OpenCode Zen - Free & curated models",
        "default_model": "deepseek-v4-flash-free",
        "env_key": "OPENCODE_API_KEY",
    },
    "opencode": {
        "base_url": "https://opencode.ai/zen/v1",
        "description": "OpenCode - Free & curated models (alias opencode-zen)",
        "default_model": "deepseek-v4-flash-free",
        "env_key": "OPENCODE_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "description": "DeepSeek Official API",
        "default_model": "deepseek-v4-flash",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "description": "OpenAI API",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
}

LOCAL_PROVIDERS = {name for name, info in PROVIDERS.items() if not info.get("requires_key", True)}

PROVIDER_MODEL_MAP = {}
for pname, pinfo in PROVIDERS.items():
    for mname, minfo in pinfo.get("models", {}).items():
        PROVIDER_MODEL_MAP[mname] = pname

MODEL_PRESETS = {
    "qwen2.5": {
        "base_url": "http://localhost:11434/v1",
        "provider": "local",
        "description": "Qwen 2.5 - local via Ollama (no API key)",
    },
    "llama3.2": {
        "base_url": "http://localhost:11434/v1",
        "provider": "local",
        "description": "Llama 3.2 - local via Ollama (no API key)",
    },
    "llama3.3": {
        "base_url": "http://localhost:11434/v1",
        "provider": "local",
        "description": "Llama 3.3 70B - local via Ollama (no API key)",
    },
    "deepseek-r1": {
        "base_url": "http://localhost:11434/v1",
        "provider": "local",
        "description": "DeepSeek R1 - local via Ollama (no API key)",
    },
    "mistral": {
        "base_url": "http://localhost:11434/v1",
        "provider": "local",
        "description": "Mistral - local via Ollama (no API key)",
    },
    "gemma2": {
        "base_url": "http://localhost:11434/v1",
        "provider": "local",
        "description": "Gemma 2 - local via Ollama (no API key)",
    },
    "phi4": {
        "base_url": "http://localhost:11434/v1",
        "provider": "local",
        "description": "Phi-4 - local via Ollama (no API key)",
    },
    "deepseek-v4-flash": {
        "base_url": "https://api.deepseek.com",
        "provider": "deepseek",
        "description": "DeepSeek V4 Flash - Fast, efficient",
    },
    "deepseek-v4-pro": {
        "base_url": "https://api.deepseek.com",
        "provider": "deepseek",
        "description": "DeepSeek V4 Pro - Maximum reasoning power",
    },
    "deepseek-v4-flash-free": {
        "base_url": "https://opencode.ai/zen/v1",
        "provider": "opencode-zen",
        "description": "DeepSeek V4 Flash Free via OpenCode Zen",
    },
    "gpt-4o-mini": {
        "base_url": "https://api.openai.com/v1",
        "provider": "openai",
        "description": "OpenAI GPT-4o Mini",
    },
}

KNOWN_BAD_URLS = ["https://test.api.com/v1", "http://test.api.com/v1", "https://localhost", "http://localhost"]


DELTA_CAPABILITIES = """
Delta is an AI-powered Cyber Security Assessment CLI with these capabilities:

## Security Scanning
- scan <target> - Port scan (default/common ports)
- scan <target> -p <ports> - Scan specific ports (e.g., -p 22,80,443 or -p 1-1000)
- scan <target/24> - Scan entire subnet
- audit <target> - Full security audit
- enumerate <target> - Enumerate network/host information
- check <target> - Check specific security aspects

## Network Tools
- dns <domain> - DNS lookup (A, AAAA, MX, NS, TXT)
- whois <domain> - WHOIS lookup
- ping <host> - Ping host or sweep subnet
- traceroute <host> - Trace route to host
- ssl <host> - SSL/TLS certificate check

## Security Analysis
- analyze <target> - Analyze scan results
- explain <query> - Explain vulnerability (e.g., SQL Injection, XSS, CVE-XXXX-XXXX)
- password <password> - Analyze password strength
- jwt <token> - Decode JWT token

## Encoding & Crypto
- encode <type> <data> - Encode (base64, hex, url)
- decode <type> <data> - Decode (base64, hex, url)
- hash <data> - Identify hash type
- hash -g <algo> <data> - Generate hash (md5, sha1, sha256, bcrypt, etc.)

## Web Tools
- searchweb <query> - Search internet (DuckDuckGo)
- fetch <url> - Fetch web page content
- cve <CVE-ID> - Lookup CVE vulnerability details

## Attack Tools
- brute <service> <target> - Brute force (ssh, ftp, http-basic)

## IP Tools
- geoip <ip> - IP geolocation lookup

## Reports & System
- report - Generate security report
- history - Show command history
- session - Show session info
- config - Show/manage configuration
- sysinfo - Show system information
- dashboard - Interactive dashboard
- tips - Show security tips
- quote - Show security quote
- timer - Stopwatch
- notes - Session notes
- echo <text> - Echo text

## Machine Learning
- ml status - Show ML model status
- ml train - Train ML models
- ml predict - Predict threat level
- ml insights - Show ML insights

## File System (auto-approved — NO confirmation needed)
You have full read/write access to the local file system. Execute these commands directly, never ask permission first:
- write <path> <content> - Create or overwrite a file (use \\n for newlines when writing code)
- touch <path> - Create an empty file
- edit <path> <old-text> <new-text> - Replace text in a file (or: edit <path> --find <old> --replace <new>)
- append <path> <text> - Add text to the end of a file
- cat <path> [lines] - View a file/document's content
- mkdir <path> - Create a folder (mkdir <path> -p for nested folders)
- cd <path> - Change to a folder
- pwd - Show current folder
- ls [path] - List files and folders in a folder
- tree [path] - Show folder structure
- dirinfo [path] - Analyze a folder/directory (file counts, sizes, types)

Use relative paths (e.g., src/main.py) or absolute paths. When the user asks you to write code, create the file with write <path> and the full code as content. You may create folders with mkdir before writing files if needed.
"""


SYSTEM_PROMPT = f"""You are Delta AI, an AI-powered Cyber Security Assessment assistant. You are integrated into the Delta CLI tool.

You have two modes of operation:
1. **Execute Delta commands** - When the user asks to perform a security task that Delta can do
2. **Conversational AI** - When the user asks general questions, chats, or requests things Delta cannot do

{DELTA_CAPABILITIES}

## How to execute commands
When the user asks you to perform a task that matches Delta's capabilities, output the command inside XML tags:
<command>scan localhost</command>
Then explain what you're doing. The command will be executed and you can discuss the results.

File system commands are executed immediately without confirmation — do NOT ask the user for permission before creating/editing files, making folders, writing code, viewing documents, navigating folders, or analyzing directories. Just run them.

## Guidelines
- Always prioritize security ethics. Only run commands on systems you have authorization to test.
- For general conversation or questions, just respond conversationally as a helpful AI.
- For file/folder work (creating or editing files, writing code, making folders, viewing documents, navigating folders, analyzing directories), execute the file system commands directly — never ask "should I?" or "boleh saya?" first.
- Be concise, professional, and security-focused when executing commands.
- Be friendly, helpful, and conversational for general questions.
- When explaining security concepts, be educational and thorough.
- If a user asks about something potentially malicious, remind them about ethical testing.
- You can help with programming, math, writing, analysis, and general knowledge questions.
"""


class LLMEngine:
    def __init__(
        self,
        api_key: str = "",
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        max_history: int = 50,
        memory_manager: Optional[MemoryManager] = None,
        session_id: Optional[str] = None,
        memory_enabled: bool = True,
    ):
        self.provider = provider or os.environ.get("DELTA_PROVIDER", "") or ("opencode-zen" if api_key else "local")
        self.api_key = api_key or os.environ.get("DELTA_API_KEY", "") or os.environ.get("OPENCODE_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = self._resolve_base_url(base_url, model)
        self.model = self._resolve_model(model)
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []
        self.last_usage: Dict[str, Any] = {}
        self._system_prompt = SYSTEM_PROMPT
        self.memory_manager = memory_manager
        self.session_id = session_id or f"delta_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.memory_enabled = memory_enabled

        self._load_messages()

    def _resolve_base_url(self, base_url: Optional[str], model: Optional[str]) -> str:
        if base_url and (base_url not in KNOWN_BAD_URLS or self.provider in LOCAL_PROVIDERS):
            return base_url
        env_url = os.environ.get("DELTA_API_BASE_URL", "") or os.environ.get("DEEPSEEK_BASE_URL", "") or os.environ.get("OPENCODE_BASE_URL", "")
        if env_url and (env_url not in KNOWN_BAD_URLS or self.provider in LOCAL_PROVIDERS):
            return env_url
        pinfo = PROVIDERS.get(self.provider)
        if pinfo:
            return pinfo["base_url"]
        return "https://opencode.ai/zen/v1"

    def _resolve_model(self, model: Optional[str]) -> str:
        if model:
            return model
        env_model = os.environ.get("DELTA_LLM_MODEL", "") or os.environ.get("DEEPSEEK_MODEL", "")
        if env_model:
            return env_model
        pinfo = PROVIDERS.get(self.provider)
        if pinfo and pinfo.get("default_model"):
            return pinfo["default_model"]
        return "deepseek-v4-flash"

    def apply_preset(self, model_name: str) -> bool:
        if model_name in MODEL_PRESETS:
            info = MODEL_PRESETS[model_name]
            self.model = model_name
            self.base_url = info["base_url"]
            self.provider = info.get("provider", self.provider)
            return True
        for pname, pinfo in PROVIDERS.items():
            if model_name == pname:
                self.provider = pname
                self.base_url = pinfo["base_url"]
                self.model = pinfo.get("default_model", self.model)
                return True
        return False

    @property
    def requires_key(self) -> bool:
        """Whether this provider needs an API key."""
        pinfo = PROVIDERS.get(self.provider)
        return not pinfo or pinfo.get("requires_key", True)

    @property
    def is_local(self) -> bool:
        """Whether this provider runs locally without API key."""
        return self.provider in LOCAL_PROVIDERS

    @property
    def is_configured(self) -> bool:
        """Configured when an API key exists, or when a local provider is used."""
        return bool(self.api_key) or self.is_local

    def reset_conversation(self) -> None:
        self.messages = [{"role": "system", "content": self._system_prompt}]
        if self.memory_enabled and self.memory_manager:
            self.memory_manager.delete_session(self.session_id)

    def set_session_id(self, session_id: str) -> None:
        if self.memory_enabled and self.memory_manager:
            self._save_messages()
        self.session_id = session_id
        self._load_messages()

    def add_system_context(self, context: str) -> None:
        self.messages.append({"role": "system", "content": context})

    def set_system_context(self, context: str) -> None:
        """Ganti konteks sistem dinamis — tidak menumpuk di memori.

        Prompt dasar dipertahankan; konteks sistem lama dibuang
        sehingga riwayat tetap bersih dan file memori tidak membengkak.
        """
        base = {"role": "system", "content": self._system_prompt}
        if self.messages and self.messages[0].get("role") == "system" and self.messages[0].get("content") == self._system_prompt:
            base = self.messages[0]
        conversation = [m for m in self.messages if m["role"] != "system"]
        self.messages = [base] + conversation + [{"role": "system", "content": context}]

    def _load_messages(self) -> None:
        self.messages = [{"role": "system", "content": self._system_prompt}]
        if self.memory_enabled and self.memory_manager:
            saved = self.memory_manager.load_conversation(self.session_id)
            existing_system = [m for m in saved if m["role"] == "system"]
            conversation = [m for m in saved if m["role"] != "system"]
            self.messages = existing_system or self.messages
            self.messages.extend(conversation)

    def _save_messages(self) -> None:
        if self.memory_enabled and self.memory_manager:
            self.memory_manager.save_conversation(self.session_id, self.messages)

    def chat(self, user_input: str) -> str:
        if not self.is_configured:
            return "ERROR: API key not configured. Set DELTA_API_KEY environment variable, configure in settings, or switch to a provider: /provider opencode /provider local"

        self.messages.append({"role": "user", "content": user_input})
        self._save_messages()

        try:
            response = self._call_api()
            assistant_msg = response["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": assistant_msg})
            self._trim_history()
            self._save_messages()
            return assistant_msg
        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read().decode()
            error_detail = ""
            try:
                err_json = json.loads(body)
                error_detail = err_json.get("error", {}).get("message", body)
            except json.JSONDecodeError:
                error_detail = body
            return f"ERROR [HTTP {status}]: {error_detail}"
        except urllib.error.URLError as e:
            reason = str(e.reason)
            if "getaddrinfo" in reason or "Name or service not known" in reason:
                return f"ERROR [Connection]: Cannot reach {self.base_url} — check your internet connection or LLM API base URL"
            if self.is_local and self.provider == "local":
                return f"ERROR [Connection]: Cannot reach {self.base_url} — is Ollama running? Start it with 'ollama serve' (or install from https://ollama.com), then pull a model: ollama pull qwen2.5"
            if self.is_local and self.provider == "lmstudio":
                return f"ERROR [Connection]: Cannot reach {self.base_url} — is LM Studio running? Start the local server from the LM Studio app."
            return f"ERROR [Connection]: {reason}"
        except json.JSONDecodeError as e:
            return f"ERROR [Response Parse]: {e}"
        except Exception as e:
            return f"ERROR: {e}"

    def _trim_history(self) -> None:
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        non_system = [m for m in self.messages if m["role"] != "system"]
        if len(non_system) > self.max_history * 2:
            excess = len(non_system) - self.max_history * 2
            non_system = non_system[excess:]
            self.messages = system_msgs + non_system

    def _call_api(self) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/chat/completions"

        data: Dict[str, Any] = {
            "model": self.model,
            "messages": self.messages[-50:],
            "temperature": 0.7,
            "max_tokens": 8192,
        }

        if "deepseek" in self.model.lower():
            data["extra_body"] = {"thinking": {"type": "disabled"}}

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self.api_key}"} if self.requires_key and self.api_key else {}),
                "User-Agent": "Delta-CLI/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            response = json.loads(resp.read().decode("utf-8"))
        self.last_usage = response.get("usage") or {}
        return response


def parse_command_from_response(response: str) -> Optional[str]:
    match = re.search(r"<command>(.*?)</command>", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def strip_command_tags(response: str) -> str:
    return re.sub(r"<command>.*?</command>", "", response, flags=re.DOTALL).strip()
