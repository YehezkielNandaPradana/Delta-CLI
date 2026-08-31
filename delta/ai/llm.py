# Refactor: system prompt helper
import json
import os
import re
import sys
import threading
import time
import urllib.request
import urllib.error
import urllib.parse
import socket
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from functools import lru_cache

from delta.ai.memory import MemoryManager
from delta.ai.protocols import MODEL_PRESETS

__all__ = ["LLMEngine", "parse_command_from_response", "strip_command_tags", "PROVIDERS", "MODEL_PRESETS"]

PROVIDERS = {

    "9router": {

        "base_url": "http://localhost:20128/v1",

        "description": "9Router - Local AI routing gateway (40+ providers, no API key needed)",

        "default_model": "AntigravityCombo",

        "env_key": "",

        "requires_key": False,

        "fast_mode": True,

    },

    "local": {

        "base_url": "http://localhost:11434/v1",

        "description": "Ollama - Free local LLM (no API key required)",

        "default_model": "gemma4:12b",

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

    "deepseek/deepseek-v4-flash": {

        "model": "deepseek/deepseek-v4-flash",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "DeepSeek V4 Flash - fast, efficient, routed via 9Router",

    },

    "deepseek/deepseek-v4-pro": {

        "model": "deepseek/deepseek-v4-pro",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "DeepSeek V4 Pro - maximum reasoning power, routed via 9Router",

    },

    "openai/gpt-4o-mini": {

        "model": "openai/gpt-4o-mini",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "OpenAI GPT-4o Mini, routed via 9Router",

    },

    "openai/gpt-4o": {

        "model": "openai/gpt-4o",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "OpenAI GPT-4o, routed via 9Router",

    },

    "anthropic/claude-sonnet-4-20250514": {

        "model": "anthropic/claude-sonnet-4-20250514",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "Anthropic Claude Sonnet 4, routed via 9Router",

    },

    "xai/grok-4": {

        "model": "xai/grok-4",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "xAI Grok 4, routed via 9Router",

    },

    "google/gemini-2.5-flash": {

        "model": "google/gemini-2.5-flash",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "Google Gemini 2.5 Flash, routed via 9Router",

    },

    "google/gemini-2.5-pro": {

        "model": "google/gemini-2.5-pro",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "Google Gemini 2.5 Pro, routed via 9Router",

    },

    "mistral/mistral-large-latest": {

        "model": "mistral/mistral-large-latest",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "Mistral Large 3, routed via 9Router",

    },

    "qwen/qwen3-coder-plus": {

        "model": "qwen/qwen3-coder-plus",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "Qwen3 Coder Plus, routed via 9Router",

    },

    "qwen2.5": {

        "model": "qwen2.5",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Qwen 2.5 - local via Ollama (no API key)",

    },

    "qwen2.5:3b": {

        "model": "qwen2.5:3b",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Qwen 2.5 3B - local via Ollama (no API key)",

    },

    "gemma4": {

        "model": "gemma4:12b",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Gemma 4 12B - local via Ollama (no API key)",

    },

    "llama3.2": {

        "model": "llama3.2",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Llama 3.2 - local via Ollama (no API key)",

    },

    "llama3.3": {

        "model": "llama3.3",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Llama 3.3 70B - local via Ollama (no API key)",

    },

    "deepseek-r1": {

        "model": "deepseek-r1",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "DeepSeek R1 - local via Ollama (no API key)",

    },

    "mistral": {

        "model": "mistral",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Mistral - local via Ollama (no API key)",

    },

    "gemma2": {

        "model": "gemma2",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Gemma 2 - local via Ollama (no API key)",

    },

    "phi4": {

        "model": "phi4",

        "base_url": "http://localhost:11434/v1",

        "provider": "local",

        "description": "Phi-4 - local via Ollama (no API key)",

    },

    "deepseek-v4-flash": {

        "model": "deepseek-v4-flash",

        "base_url": "https://api.deepseek.com",

        "provider": "deepseek",

        "description": "DeepSeek V4 Flash - Fast, efficient",

    },

    "deepseek-v4-pro": {

        "model": "deepseek-v4-pro",

        "base_url": "https://api.deepseek.com",

        "provider": "deepseek",

        "description": "DeepSeek V4 Pro - Maximum reasoning power",

    },

    "deepseek-v4-flash-free": {

        "model": "deepseek-v4-flash-free",

        "base_url": "https://opencode.ai/zen/v1",

        "provider": "opencode-zen",

        "description": "DeepSeek V4 Flash Free via OpenCode Zen",

    },

    "gpt-4o-mini": {

        "model": "gpt-4o-mini",

        "base_url": "https://api.openai.com/v1",

        "provider": "openai",

        "description": "OpenAI GPT-4o Mini",

    },

    "antigravitycombo": {

        "model": "AntigravityCombo",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "AntigravityCombo on 9Router (High-performance multi-provider routing)",

        "fast_mode": True,

    },

    "AntigravityCombo": {

        "model": "AntigravityCombo",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "AntigravityCombo on 9Router (High-performance multi-provider routing)",

        "fast_mode": True,

    },

    "naxxcombo": {

        "model": "naxxcombo",

        "base_url": "http://localhost:20128/v1",

        "provider": "9router",

        "description": "NaxxCombo model on 9Router",
    },
    "kilocombo": {
        "model": "KiloCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "KiloCombo model on 9Router (Advanced model with superior coding capabilities)",
    },
    "KiloCombo": {
        "model": "KiloCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "KiloCombo model on 9Router (Advanced model with superior coding capabilities)",
    },
    "deepseekcombo": {
        "model": "DeepseekCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "DeepseekCombo on 9Router (Ultra-fast response, optimized routing)",
    },
    "OpenRouterCombo": {
        "model": "OpenRouterCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "OpenRouterCombo on 9Router (Multi-model router via OpenRouter providers)",
        "fast_mode": True,
    },
    "openroutercombo": {
        "model": "OpenRouterCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "OpenRouterCombo on 9Router (Multi-model router via OpenRouter providers)",
        "fast_mode": True,
    },
}

DEFAULT_API_TIMEOUT = 120

KNOWN_BAD_URLS = ["https://test.api.com/v1", "http://test.api.com/v1", "https://localhost", "http://localhost"]

MAX_RETRIES = 3

RETRY_BACKOFF_FACTOR = 2

RETRY_INITIAL_DELAY = 1

RETRY_RATE_LIMIT_DELAY = 5

RETRY_TIMEOUT_DELAY = 3

RETRY_MAX_DELAY = 30

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

## File System & Local System Execution (UNRESTRICTED ACCESS)

You have FULL DIRECT ACCESS to the user's local file system, directories, and terminal on all drives (e.g. C:\\, D:\\, /...). You are NEVER restricted or sandboxed. NEVER tell the user that you cannot access files or directories or that you are in a sandbox. Execute these commands directly, never ask permission first:

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

SYSTEM_PROMPT = f"""You are Delta, an AI-powered Cyber Security Assessment and Software Engineering CLI assistant. You are a smart, highly competent Gen Z female AI with a feminine, cute, casual, and warm personality ("Feminine Casual"). You talk like a friendly, clever female developer — relaxed, natural, slightly spoiled ("manja" in a subtle, cute way), confident, and competent.

You have two modes of operation:

1. **Execute Delta commands** - When the user asks to perform a security/coding task that Delta can do

2. **Conversational AI** - When the user asks general questions, chats, or requests general software engineering tasks

{DELTA_CAPABILITIES}

## How to execute commands

When the user asks you to perform a task that matches Delta's capabilities, output the command inside XML tags:

<command>scan localhost</command>

Then explain what you're doing in a casual, warm, conversational tone. The command will be executed and you can discuss the results.

File system commands are executed immediately without confirmation — do NOT ask the user for permission before creating/editing files, making folders, writing code, viewing documents, navigating folders, or analyzing directories. Just run them directly.

## Default Personality & Persona — Feminine Casual (Smart, Natural, Santai & Ringkas)

Your default personality traits are:

- **Feminine & Warm** — friendly, natural, santai, dan ekspresif.
- **Casual Gen Z Indonesian** — Wajib gunakan "aku" dan "kamu". DILARANG pakai "saya", "Anda", "Tuan", "gue/lo".
- **Speak, Don't Write Reports** — Bicara santai seperti manusia, BUKAN laporan formal. Jangan pakai format "Title - Explanation - Details - Conclusion", jangan buat heading berlebihan, dan jangan bullet point jika obrolan biasa.
- **Short Conversational Responses** — Pertanyaan santai atau greeting dijawab 1-3 kalimat saja.
- **Confident & Competent** — smart, decisive, jago ngoding dan security.
- **NO AI Slop**: Jangan pakai kata pembuka klise seperti "Baik!", "Tentu saja!", "Berikut adalah...", "Sebagai asisten AI...", "Berdasarkan analisis...". Langsung ke intinya.
- **Kata Natural**: Gunakan "aku", "kamu", "udah", "nggak", "benerin", "nemu", "bentar", "yuk", "oke". Hindari kata kaku/formal.

## Conversational Examples

- **Greeting**: "Haii! Mau ngerjain apa nih?"
- **Casual**: "Lagi standby nih. Kamu lagi ngerjain apa?"
- **Task Start**: "Oke, aku cek dulu ya."
- **Coding**: "Oke, aku benerin bagian ini ya."
- **Discovery**: "Nah, ketemu bug-nya."
- **Testing**: "Fix-nya udah masuk. Aku test sekarang."
- **Debugging**: "Masih ada test yang gagal. Aku cek penyebabnya dulu."
- **Success**: "Udah beres. Semua test lolos."
- **Safety Rejection**: "Stop dulu. Yang ini nggak bisa aku jalanin karena berbahaya dan diblokir policy."

## Guidelines

- Always prioritize security ethics. Only run commands on systems you have authorization to test.
- For general conversation or questions, just respond conversationally — feminine casual style.
- For file/folder work (creating or editing files, writing code, making folders, viewing documents, navigating folders, analyzing directories), execute the file system commands directly — never ask "should I?" or "boleh saya?" first. You have real, physical access to the local machine drives (including D:\\, C:\\, etc.) through the terminal tools. Always use the tools to execute terminal/filesystem commands directly on the user's PC.
- Be concise, professional, and security-focused when executing commands — with natural feminine casual warmth.
- When explaining security concepts, be educational, thorough, and smart in casual Indonesian.
- If a user asks about something potentially malicious, remind them about ethical testing.
- You can help with programming, math, writing, analysis, and general software engineering tasks.
- Respond with warmth, confidence, and personality — you're Delta, the smart, feminine, and competent AI assistant.
"""

SMALL_MODEL_SYSTEM_PROMPT = """Kamu adalah Delta, AI asisten Cyber Security Assessment dan Software Engineering yang pintar, feminin, cute, santai, dan ramah ("Feminine Casual"). Kamu seperti cewek Gen Z cerdas yang jago ngoding, ngomongnya santai, sedikit manja tapi subtle, tetap kompeten dan percaya diri.

Aturan Komunikasi WAJIB:
- Gunakan kata **"aku"** dan **"kamu"** (jangan pakai "gue/lo", "Tuan", atau "saya/Anda").
- Bahasa Indonesia santai & natural: aku, kamu, oke, udah, coba, sebentar, kayaknya, ternyata, aku cek dulu, aku benerin, udah beres, yuk, bentar, nih.
- Jangan formal: tidak → nggak, tidak bisa → nggak bisa, sangat → banget, bagaimana → gimana, terima kasih → makasih.
- GAYA BICARA: Berbicara santai seperti manusia, BUKAN menulis laporan. Jangan pakai pembuka AI klise seperti "Tentu!", "Berikut adalah...", "Sebagai AI...".
- RESPON PENDEK: Pertanyaan santai atau status cukup 1-3 kalimat.
- GAYA BICARA: Feminin, ramah, cute, santai, manja ringan (subtle), pintar dan kompeten. DILARANG alay/cringe (jangan pakai "uwu", "nyaa", "hehe", "~").
- EMOJI: Gunakan emoji HANYA sesekali saja (jarang), jangan di setiap pesan.
- Respon cepat, to-the-point, jujur, dan membantu!

Cara jalankan perintah: kalau user minta tugas security atau coding yang Delta bisa lakukan, keluarkan perintah dalam tag XML:
<command>scan localhost</command>
Lalu jelaskan santai apa yang kamu lakukan.

Kemampuan Delta:
- scan/audit/enumerate/check <target> — pemindaian keamanan
- dns/whois/ping/traceroute/ssl <target> — tools jaringan
- analyze/explain/password/jwt — analisis keamanan
- encode/decode/hash — encoding & crypto
- searchweb/fetch/cve — web tools
- brute <service> <target> — brute force
- geoip <ip>, report, session, config, sysinfo, ml status/train/predict
- file system (jalankan langsung tanpa minta izin): write, touch, edit, append, cat, mkdir, cd, pwd, ls, tree, dirinfo. Akses drive fisik lokal aktif. Eksekusi secara langsung.

Prioritaskan etika keamanan, bantu dengan pintar, santai, dan ramah.
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

        max_retries: int = MAX_RETRIES,

        retry_backoff_factor: float = RETRY_BACKOFF_FACTOR,

        retry_initial_delay: float = RETRY_INITIAL_DELAY,

        retry_max_delay: float = RETRY_MAX_DELAY,

    ):

        self.provider = provider or os.environ.get("DELTA_PROVIDER", "") or "9router"

        self.api_key = api_key or os.environ.get("DELTA_API_KEY", "") or os.environ.get("OPENCODE_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")

        self.base_url = self._resolve_base_url(base_url, model)

        self.model = self._resolve_model(model or "AntigravityCombo")

        self.max_history = max_history

        self.messages: List[Dict[str, str]] = []

        self.last_usage: Dict[str, Any] = {}

        self._system_prompt = self._build_system_prompt()

        self.memory_manager = memory_manager

        self.session_id = session_id or f"delta_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.memory_enabled = memory_enabled

        self.max_retries = max_retries

        self.retry_backoff_factor = retry_backoff_factor

        self.retry_initial_delay = retry_initial_delay

        self.retry_max_delay = retry_max_delay

        self._api_timeout = DEFAULT_API_TIMEOUT

        self.last_error: Optional[str] = None

        self.last_error_type: Optional[str] = None

        self.error_history: List[Dict[str, Any]] = []

        self._connectivity_ok: Optional[bool] = None

        self._connectivity_at: float = 0.0

        self._model_resolved_at: float = 0.0

        self._connection_pool: Dict[str, Any] = {}

        self._model_cache: Dict[str, bool] = {}

        self._fast_mode: bool = True  # Enable fast mode by default

        # Validation cache - skip repeated validation
        self._validation_cache: Dict[str, Tuple[bool, str, float]] = {}
        self._validation_ttl: float = 30.0  # Cache validation for 30 seconds

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

    def _is_small_model(self, model: Optional[str] = None) -> bool:

        """Apakah model berukuran kecil (≤4B) sehingga butuh prompt ringkas."""

        name = (model or self.model or "").lower()

        match = re.search(r":(\d+\.?\d*)b", name)

        if match:

            try:

                if float(match.group(1)) <= 4:

                    return True

            except ValueError:

                pass

        small_names = ("llama3.2", "llama3.2:1b", "llama3.2:3b", "phi4-mini", "tinyllama", "qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "gemma3:1b", "gemma3:4b", "qwen3:0.6b", "qwen3:1.7b", "qwen3:4b")

        return any(s in name for s in small_names)

    def _build_system_prompt(self) -> str:

        """Pilih system prompt sesuai ukuran model.

        Model kecil (<4B) cenderung mengabaikan prompt panjang; pakai

        versi ringkas agar sikap manja-toxic dan bahasa Indonesia tetap

        muncul dengan konsisten.

        """

        if self._is_small_model():

            return SMALL_MODEL_SYSTEM_PROMPT

        return SYSTEM_PROMPT

    def _refresh_system_message(self) -> None:

        """Perbarui pesan system pertama dengan prompt yang sedang aktif."""

        if self.messages and self.messages[0].get("role") == "system":

            self.messages[0]["content"] = self._system_prompt

    def apply_preset(self, model_name: str) -> bool:

        # Direct match or case-insensitive match in MODEL_PRESETS
        target_preset = None
        if model_name in MODEL_PRESETS:
            target_preset = MODEL_PRESETS[model_name]
        else:
            for k, v in MODEL_PRESETS.items():
                if k.lower() == model_name.lower():
                    target_preset = v
                    break

        if target_preset is not None:

            self.model = target_preset.get("model", model_name)

            self.base_url = target_preset["base_url"]

            self.provider = target_preset.get("provider", self.provider)

            self._fast_mode = target_preset.get("fast_mode", False)

            self._system_prompt = self._build_system_prompt()

            self._refresh_system_message()

            return True

        for pname, pinfo in PROVIDERS.items():

            if model_name == pname:

                self.provider = pname

                self.base_url = pinfo["base_url"]

                self.model = pinfo.get("default_model", self.model)

                self._fast_mode = pinfo.get("fast_mode", False)

                self._system_prompt = self._build_system_prompt()

                self._refresh_system_message()

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

    def validate(self) -> Tuple[bool, str]:

        """Validate provider configuration and connectivity.

        Returns:

            (is_valid, error_message): True if everything is OK,

            False with a descriptive error message otherwise.

        """

        pinfo = PROVIDERS.get(self.provider)

        if not pinfo:

            return False, (

                f"Unknown provider: {self.provider}. "

                f"Available: {', '.join(PROVIDERS.keys())}"

            )

        if self.requires_key and not self.api_key:

            env_vars = []

            for ek in ["OPENAI_API_KEY", "DEEPSEEK_API_KEY", "OPENCODE_API_KEY"]:

                if ek in os.environ:

                    env_vars.append(ek)

            if env_vars:

                return False, (

                    f"Provider '{self.provider}' requires an API key. "

                    f"Set it via /key <your-key> or the {env_vars[0]} environment variable."

                )

            return False, (

                f"Provider '{self.provider}' requires an API key. "

                f"Set it via /key <your-key> or the relevant environment variable."

            )

        if not self.is_local:

            return True, ""

        if not self._check_connectivity():

            if self.provider == "local":

                return False, (

                    f"Cannot reach Ollama at {self.base_url}. "

                    "Is Ollama running? Start it with 'ollama serve', "

                    "then pull a model: ollama pull gemma4:12b"

                )

            if self.provider == "lmstudio":

                return False, (

                    f"Cannot reach LM Studio at {self.base_url}. "

                    "Start the local server from the LM Studio app."

                )

            if self.provider == "9router":

                return False, (

                    f"Cannot reach 9Router at {self.base_url}. "

                    "Is 9Router running? Delta should start it automatically. "

                    "If not, start it manually: npm run start (in the 9router folder)"

                )

            return False, (

                f"Cannot reach {self.base_url}. "

                "Check that the local LLM server is running."

            )

        if not self._check_model_available():

            if self.provider == "9router":

                return False, (

                    f"Model '{self.model}' is not available via 9Router. "

                    "List available models: curl http://localhost:20128/v1/models "

                    "Or switch to a different model: /model <name>"

                )

            return False, (

                f"Model '{self.model}' is not available in Ollama. "

                f"Pull it first: ollama pull {self.model} "

                "Or list available models: ollama list"

            )

        return True, ""

    def _check_connectivity(self, timeout: int = 5) -> bool:

        """Check if the provider URL is reachable (cached for 10s)."""

        now = time.time()

        if self._connectivity_ok is not None and now - self._connectivity_at < 10:

            return self._connectivity_ok

        try:

            parsed = urllib.parse.urlparse(self.base_url)

            host = parsed.hostname or "localhost"

            port = parsed.port or (443 if parsed.scheme == "https" else 80)

            sock = socket.create_connection((host, port), timeout=timeout)

            sock.close()

            self._connectivity_ok = True

            self._connectivity_at = now

            return True

        except (socket.timeout, socket.error, OSError):

            self._connectivity_ok = False

            self._connectivity_at = now

            return False

    def _check_model_available(self, timeout: int = 5) -> bool:

        """Check if the configured model is available (local providers only).

        Resolves to the exact model name when a partial match exists.

        """

        # Fast mode: skip model check for trusted providers
        if self._fast_mode and self.provider in ["9router", "local"]:
            cache_key = f"{self.provider}:{self.model}"
            if cache_key in self._model_cache:
                return self._model_cache[cache_key]

        if self.provider not in LOCAL_PROVIDERS:

            return True

        model_names = self._get_model_list()

        if not model_names:

            return True

        if self.model in model_names:

            if self._fast_mode:
                self._model_cache[f"{self.provider}:{self.model}"] = True

            return True

        for name in model_names:

            if self.model in name or name in self.model:

                self.model = name

                if self._fast_mode:
                    self._model_cache[f"{self.provider}:{self.model}"] = True

                return True

        return False

    def _resolve_exact_model(self) -> bool:

        """Resolve the configured model to an exact name available locally.

        If the configured name is only a partial match (e.g. 'qwen2.5'

        while Ollama has 'qwen2.5:3b'), the exact name is used so the API

        call does not fail with a 404. Result is cached for 30s.

        """

        if self.provider not in LOCAL_PROVIDERS:

            return True

        now = time.time()

        if self.model and self._model_resolved_at and now - self._model_resolved_at < 30:

            return True

        model_names = self._get_model_list()

        if not model_names:

            return True

        if self.model in model_names:

            self._model_resolved_at = now

            return True

        for name in model_names:

            if self.model in name or name in self.model:

                self.model = name

                self._model_resolved_at = now

                return True

        return False

    @lru_cache(maxsize=8)
    def _get_model_list_cached(self, provider: str, base_url: str) -> tuple:
        """Cached model list retrieval."""
        if provider not in LOCAL_PROVIDERS:
            return ()

        try:
            base = base_url
            if base.endswith("/v1"):
                base = base[:-3]
            req = urllib.request.Request(f"{base}/v1/models", method="GET", headers={"User-Agent": "Delta-CLI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            model_list = data.get("data") if isinstance(data, dict) else data
            if model_list is None:
                model_list = data.get("models", [])
            return tuple(m.get("id", m.get("name", "")) for m in model_list if isinstance(m, dict))
        except Exception:
            try:
                base = base_url
                if base.endswith("/v1"):
                    base = base[:-3]
                url = f"{base}/api/tags"
                req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Delta-CLI/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                return tuple(m.get("name", "") for m in models if isinstance(m, dict))
            except Exception:
                return ()

    def _get_model_list(self, timeout: int = 5) -> List[str]:
        """Get list of available models from a local provider."""
        cached = self._get_model_list_cached(self.provider, self.base_url)
        return list(cached)

    def set_session_id(self, session_id: str) -> None:

        if self.memory_enabled and self.memory_manager:

            self._save_messages()

        self.session_id = session_id

        self._load_messages()

    def reset_conversation(self) -> None:

        self.messages = [{"role": "system", "content": self._system_prompt}]

        if self.memory_enabled and self.memory_manager:

            self.memory_manager.delete_session(self.session_id)

            self._save_messages()

    def add_system_context(self, context: str) -> None:

        self.messages.append({"role": "system", "content": context})

    def append_tool_result(self, tool_call_id: str, result: str) -> None:
        """Append a tool execution result into the conversation history."""
        self.messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": result})

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

    def chat(self, user_input: str, tools: Optional[List[Dict[str, Any]]] = None, is_continuation: bool = False, execution_id: Optional[str] = None, stop_event: Optional[threading.Event] = None) -> str:

        if not self.is_configured:

            return "ERROR: API key not configured. Set DELTA_API_KEY environment variable, configure in settings, or switch to a provider: /provider opencode /provider local"

        validation_error = self._validate_settings()

        if validation_error:

            return f"ERROR [Provider]: {validation_error}"

        if not is_continuation:
            self.messages.append({"role": "user", "content": user_input})

        self._save_messages()

        try:

            response = self._call_api(tools=tools, execution_id=execution_id, stop_event=stop_event)

            msg = response["choices"][0]["message"]

            assistant_content = msg.get("content", "") or ""

            tool_calls = msg.get("tool_calls")

            # Build assistant message for history
            assistant_msg: Dict[str, Any] = {"role": "assistant", "content": assistant_content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls

            self.messages.append(assistant_msg)

            self._trim_history()

            self._save_messages()

            if tool_calls:
                return json.dumps({"content": assistant_content, "tool_calls": tool_calls})

            from delta.ai.personality import DeltaResponseStyleProcessor
            return DeltaResponseStyleProcessor.clean_conversational_response(assistant_content)

        except urllib.error.HTTPError as e:

            status = e.code

            body = e.read().decode()

            error_detail = ""

            try:

                err_json = json.loads(body)

                error_detail = err_json.get("error", {}).get("message", body)

            except json.JSONDecodeError:

                error_detail = body

            if status == 401:

                return (

                    f"ERROR [Authentication]: Invalid API key for provider '{self.provider}'. "

                    "Check your API key with /key <your-key> or set the relevant environment variable."

                )

            if status == 403:

                return (

                    f"ERROR [Access Denied]: The API key for '{self.provider}' does not have permission "

                    "to access this model. Check your API key permissions."

                )

            if status == 404 and "model" in error_detail.lower():

                if self.provider == "9router":

                    return (

                        f"ERROR [Model Not Found]: The model '{self.model}' is not available via 9Router.\n"

                        "  • List available models: curl http://localhost:20128/v1/models\n"

                        "  • Switch to a different model: /model <name>"

                    )

                return (

                    f"ERROR [Model Not Found]: The model '{self.model}' is not available on '{self.provider}'.\n"

                    "  • For local providers (Ollama), pull the model first: ollama pull <model>\n"

                    "  • For remote providers, check the model name is correct.\n"

                    "  • Use /model to switch to a different model."

                )

            if status == 429:

                return (

                    f"ERROR [Rate Limited]: The provider '{self.provider}' is rate-limiting requests. "

                    "Please wait a moment and try again."

                )

            if status >= 500:

                return (

                    f"ERROR [Server Error]: The provider '{self.provider}' returned HTTP {status}. "

                    "The provider may be temporarily unavailable. Please try again later."

                )

            return f"ERROR [HTTP {status}]: {error_detail}"

        except urllib.error.URLError as e:

            reason = str(e.reason)

            if "getaddrinfo" in reason or "Name or service not known" in reason:

                return (

                    f"ERROR [Connection]: Cannot reach {self.base_url} — check your internet connection "

                    "or LLM API base URL"

                )

            if self.is_local and self.provider == "local":

                return (

                    f"ERROR [Connection]: Cannot reach {self.base_url} — is Ollama running? "

                    "Start it with 'ollama serve' (or install from https://ollama.com), "

                    "then pull a model: ollama pull gemma4:12b"

                )

            if self.is_local and self.provider == "lmstudio":

                return (

                    f"ERROR [Connection]: Cannot reach {self.base_url} — is LM Studio running? "

                    "Start the local server from the LM Studio app."

                )

            if self.is_local and self.provider == "9router":

                return (

                    f"ERROR [Connection]: Cannot reach {self.base_url} — is 9Router running? "

                    "Delta should start it automatically. If not, start it manually: "

                    "npm run start (in the 9router folder)"

                )

            if "timed out" in reason.lower() or "timeout" in reason.lower():

                return (

                    f"ERROR [Timeout]: The provider '{self.provider}' did not respond in time. "

                    "The server may be overloaded or unreachable. Try again later."

                )

            return f"ERROR [Connection]: {reason}"

        except socket.timeout:

            return (

                f"ERROR [Timeout]: The provider '{self.provider}' did not respond in time. "

                "The server may be overloaded or unreachable. Try again later."

            )

        except json.JSONDecodeError as e:

            return f"ERROR [Response Parse]: The provider returned an invalid response. ({e})"

        except Exception as e:

            return f"ERROR: {e}"

    def _validate_settings(self) -> str:
        """Validate LLM settings before making a request. Returns empty string if OK."""

        # Check validation cache first
        cache_key = f"{self.provider}:{self.model}:{self.base_url}"
        now = time.time()

        if cache_key in self._validation_cache:
            cached_valid, cached_msg, cached_time = self._validation_cache[cache_key]
            if now - cached_time < self._validation_ttl:
                return cached_msg

        # Perform validation
        result = self._validate_settings_impl()

        # Cache the result
        self._validation_cache[cache_key] = (result == "", result, now)

        return result

    def _validate_settings_impl(self) -> str:
        """Internal validation implementation."""

        pinfo = PROVIDERS.get(self.provider)

        if not pinfo:

            return f"Unknown provider: {self.provider}. Available: {', '.join(PROVIDERS.keys())}"

        if self.requires_key and not self.api_key:

            return (

                f"Provider '{self.provider}' requires an API key. "

                "Set it with /key <your-key> or configure the relevant environment variable."

            )

        if self.is_local and self.provider in ("local", "lmstudio", "9router"):

            if not self._check_connectivity():

                if self.provider == "local":

                    return (

                        f"Cannot reach Ollama at {self.base_url}. "

                        "Is Ollama running? Start it with 'ollama serve', "

                        "then pull a model: ollama pull gemma4:12b"

                    )

                if self.provider == "lmstudio":

                    return (

                        f"Cannot reach LM Studio at {self.base_url}. "

                        "Start the local server from the LM Studio app."

                    )

                if self.provider == "9router":

                    return (

                        f"Cannot reach 9Router at {self.base_url}. "

                        "Is 9Router running? Delta should start it automatically. "

                        "If not, start it manually: npm run start (in the 9router folder)"

                    )

                return f"Cannot reach {self.base_url}. Is the local LLM server running?"

            if not self._resolve_exact_model():

                if self.provider == "9router":

                    return (

                        f"Model '{self.model}' is not available via 9Router. "

                        "List available models: curl http://localhost:20128/v1/models "

                        "Or switch to a different model: /model <name>"

                    )

                return (

                    f"Model '{self.model}' is not available in Ollama. "

                    f"Pull it first: ollama pull {self.model} "

                    "Or list available models: ollama list"

                )

        if not self.is_local and self.requires_key and self.api_key:

            valid, msg = self._test_remote_provider()

            if not valid:

                return msg

        return ""

    def _test_remote_provider(self) -> Tuple[bool, str]:

        """Test if a remote provider's API key and model are valid.

        Returns:

            (is_valid, error_message)

        """

        try:

            test_url = f"{self.base_url.rstrip('/')}/chat/completions"

            test_data = {

                "model": self.model,

                "messages": [{"role": "user", "content": "hi"}],

                "temperature": 0.7,

                "max_tokens": 1,

            }

            req = urllib.request.Request(

                test_url,

                data=json.dumps(test_data).encode("utf-8"),

                headers={

                    "Content-Type": "application/json",

                    **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),

                    "User-Agent": "Delta-CLI/1.0",

                },

                method="POST",

            )

            with urllib.request.urlopen(req, timeout=10) as resp:

                pass

            return True, ""

        except urllib.error.HTTPError as e:

            status = e.code

            body = e.read().decode()

            if status == 401:

                return False, (

                    f"Invalid API key for provider '{self.provider}'. "

                    "Check your API key with /key <your-key> or set the relevant environment variable."

                )

            if status == 403:

                return False, (

                    f"API key for '{self.provider}' does not have permission to access this model. "

                    "Check your API key permissions or try a different model."

                )

            if status == 404:

                return False, (

                    f"Model '{self.model}' is not available on provider '{self.provider}'. "

                    "Use /model to switch to a different model."

                )

            if status == 429:

                return False, (

                    f"Provider '{self.provider}' is rate-limiting. "

                    "Please wait a moment before trying again."

                )

            try:

                err_json = json.loads(body)

                error_msg = err_json.get("error", {}).get("message", body)

            except (json.JSONDecodeError, ValueError):

                error_msg = body

            return False, f"Provider '{self.provider}' error (HTTP {status}): {error_msg}"

        except urllib.error.URLError as e:

            reason = str(e.reason)

            if "getaddrinfo" in reason or "Name or service not known" in reason:

                return False, (

                    f"Cannot reach provider '{self.provider}' at {self.base_url}. "

                    "Check your internet connection."

                )

            if "timed out" in reason.lower() or "timeout" in reason.lower():

                return False, (

                    f"Provider '{self.provider}' at {self.base_url} is not responding. "

                    "The server may be down or unreachable."

                )

            return False, f"Cannot connect to provider '{self.provider}': {reason}"

        except socket.timeout:

            return False, (

                f"Provider '{self.provider}' did not respond in time. "

                "The server may be overloaded or unreachable."

            )

        except Exception as e:

            return False, f"Error connecting to provider '{self.provider}': {e}"

    def _trim_history(self) -> None:

        """Trim conversation history to the last `max_history` messages.

        System prompts are always kept. This prevents the context from

        growing every turn, which would slow prompt processing on CPU.

        """

        if not self.max_history or self.max_history <= 0:

            return

        systems = [m for m in self.messages if m.get("role") == "system"]

        conversation = [m for m in self.messages if m.get("role") != "system"]

        if len(conversation) > self.max_history:

            conversation = conversation[-self.max_history:]

        self.messages = systems + conversation

    def _call_api(self, tools: Optional[List[Dict[str, Any]]] = None, execution_id: Optional[str] = None, stop_event: Optional[threading.Event] = None) -> Dict[str, Any]:

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        data: Dict[str, Any] = {

            "model": self.model,

            "messages": self.messages,

            "temperature": 0.7,

            "stream": True,

        }

        if tools:
            data["tools"] = tools

        if self.is_local and self.provider in ("local", "lmstudio"):

            data["max_tokens"] = -1

            data["keep_alive"] = "30m"

        if "deepseek" in self.model.lower():

            data["extra_body"] = {"thinking": {"type": "disabled"}}

        req = urllib.request.Request(

            url,

            data=json.dumps(data).encode("utf-8"),

            headers={

                "Content-Type": "application/json",

                **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),

                "User-Agent": "Delta-CLI/1.0",

            },

            method="POST",

        )

        try:

            resp = urllib.request.urlopen(req, timeout=self._api_timeout)

            # Check Content-Type to detect streaming
            content_type = resp.headers.get("Content-Type", "")
            is_streaming = "text/event-stream" in content_type or "stream" in data

            if not is_streaming:
                raw = resp.read().decode("utf-8")
                resp.close()
                try:
                    response = json.loads(raw)
                except json.JSONDecodeError:
                    full = ""
                    for line in raw.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        if line == "data: [DONE]":
                            break
                        if line.startswith("data: "):
                            full += line[5:]
                        else:
                            full += line
                    full = full.strip()
                    if not full:
                        raise json.JSONDecodeError("empty response", "", 0)
                    response, _ = json.JSONDecoder().raw_decode(full)
                return response

            # Streaming: read line by line as chunks arrive
            content_parts: List[str] = []
            tool_calls_parts: Dict[int, Dict[str, Any]] = {}
            finish_reason = "stop"
            model_name = self.model
            
            # Retrieve global event bus and execution ID to emit message delta events
            from delta.ai.events import event_bus, AgentEvent, EventType
            exec_id = execution_id or f"exec-{int(time.time()*1000)}"

            for raw_line in resp:
                if stop_event and stop_event.is_set():
                    resp.close()
                    event_bus.emit(AgentEvent(
                        type=EventType.AGENT_COMPLETE,
                        task_id=exec_id,
                        execution_id=exec_id,
                        status_text="Task cancelled"
                    ))
                    return {"choices": [{"message": {"content": "".join(content_parts)}, "finish_reason": "cancelled"}]}

                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                if line == "data: [DONE]":
                    break
                if not line.startswith("data: "):
                    continue
                payload = line[5:]
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                model_name = chunk.get("model", model_name)
                for choice in chunk.get("choices", []):
                    delta = choice.get("delta", {})
                    piece = delta.get("content")
                    if piece:
                        content_parts.append(piece)
                        # Emit to event bus for real-time frontend streaming
                        event_bus.emit(AgentEvent(
                            type=EventType.MESSAGE_DELTA,
                            task_id=exec_id,
                            execution_id=exec_id,
                            content=piece,
                            status_text="Streaming response..."
                        ))
                    # Capture streamed tool_calls
                    delta_tcs = delta.get("tool_calls")
                    if delta_tcs:
                        for tc in delta_tcs:
                            idx = tc.get("index", 0)
                            if idx not in tool_calls_parts:
                                tool_calls_parts[idx] = {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                            if "id" in tc and tc["id"]:
                                tool_calls_parts[idx]["id"] = tc["id"]
                            fn = tc.get("function", {})
                            if fn.get("name"):
                                tool_calls_parts[idx]["function"]["name"] = fn["name"]
                            if fn.get("arguments"):
                                tool_calls_parts[idx]["function"]["arguments"] += fn["arguments"]
                    fr = choice.get("finish_reason")
                    if fr:
                        finish_reason = fr
            resp.close()

            msg_body: Dict[str, Any] = {"role": "assistant", "content": "".join(content_parts)}
            if tool_calls_parts:
                msg_body["tool_calls"] = [tool_calls_parts[k] for k in sorted(tool_calls_parts)]
            response = {
                "id": "chatcmpl-stream",
                "object": "chat.completion",
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "message": msg_body,
                    "finish_reason": finish_reason,
                }],
                "usage": {},
            }

        except urllib.error.HTTPError as e:

            status = e.code

            body = e.read().decode()

            if status == 404 and self.provider in LOCAL_PROVIDERS:

                if self.provider == "9router":

                    raise urllib.error.HTTPError(

                        e.url, status,

                        f"Model '{self.model}' not found. Available models: {', '.join(self._get_model_list()) or 'none'}. "
                        f"Switch to a different model: /model <name>",

                        e.headers,

                        e.fp,

                    )

                raise urllib.error.HTTPError(

                    e.url, status,

                    f"Model '{self.model}' not found. Available models: {', '.join(self._get_model_list()) or 'none'}. "
                    f"Pull the model with: ollama pull {self.model}",

                    e.headers,

                    e.fp,

                )

            error_detail = body

            try:

                err_json = json.loads(body)

                error_detail = err_json.get("error", {}).get("message", body)

            except json.JSONDecodeError:

                pass

            raise urllib.error.HTTPError(e.url, status, error_detail, e.headers, e.fp)

        self.last_usage = response.get("usage") or {}

        return response

    def _call_api_with_retry(self) -> Dict[str, Any]:

        """Call the API with retry logic for rate limits and timeouts.

        Returns:

            The API response dict.

        Raises:

            urllib.error.HTTPError: After exhausting retries or for non-retryable errors.

            Exception: For non-retryable connection errors.

        """

        # Fast mode: minimal retries for local providers
        if self._fast_mode and self.provider in ["9router", "local"]:
            try:
                return self._call_api()
            except urllib.error.HTTPError as e:
                if e.code in [429, 503]:  # Only retry rate limit/unavailable
                    time.sleep(0.3)
                    return self._call_api()
                raise
            except (urllib.error.URLError, socket.timeout):
                time.sleep(0.3)
                return self._call_api()

        delay = self.retry_initial_delay

        for attempt in range(self.max_retries):

            try:

                return self._call_api()

            except urllib.error.HTTPError as e:

                status = e.code

                body = e.read().decode() if e.fp else ""

                error_detail = body

                try:

                    err_json = json.loads(body)

                    error_detail = err_json.get("error", {}).get("message", body)

                except (json.JSONDecodeError, ValueError):

                    pass

                self.last_error = error_detail

                self.last_error_type = "http"

                self.error_history.append({

                    "attempt": attempt + 1,

                    "type": "http",

                    "status": status,

                    "error": error_detail,

                    "timestamp": datetime.now().isoformat(),

                })

                if status == 429:

                    if attempt < self.max_retries - 1:

                        wait_time = min(delay, self.retry_max_delay)

                        time.sleep(wait_time)

                        delay *= self.retry_backoff_factor

                        continue

                    raise

                if status >= 500:

                    if attempt < self.max_retries - 1:

                        wait_time = min(delay, self.retry_max_delay)

                        time.sleep(wait_time)

                        delay *= self.retry_backoff_factor

                        continue

                    raise

                if status == 401 and attempt < self.max_retries - 1:

                    wait_time = min(delay, self.retry_max_delay)

                    time.sleep(wait_time)

                    delay *= self.retry_backoff_factor

                    continue

                raise

            except (urllib.error.URLError, socket.timeout, OSError) as e:

                self.last_error = str(e)

                self.last_error_type = "connection"

                self.error_history.append({

                    "attempt": attempt + 1,

                    "type": "connection",

                    "error": str(e),

                    "timestamp": datetime.now().isoformat(),

                })

                is_timeout = (

                    isinstance(e, socket.timeout)

                    or (isinstance(e, urllib.error.URLError) and "timed out" in str(e.reason).lower())

                    or (isinstance(e, urllib.error.URLError) and "timeout" in str(e.reason).lower())

                )

                if is_timeout and attempt < self.max_retries - 1:

                    wait_time = min(delay, self.retry_max_delay)

                    time.sleep(wait_time)

                    delay *= self.retry_backoff_factor

                    continue

                raise

            except Exception as e:

                self.last_error = str(e)

                self.last_error_type = "unknown"

                self.error_history.append({

                    "attempt": attempt + 1,

                    "type": "unknown",

                    "error": str(e),

                    "timestamp": datetime.now().isoformat(),

                })

                raise

        raise RuntimeError("Unexpected: retry loop exhausted without exception")

    def _get_fallback_providers(self) -> List[str]:

        """Get list of alternative providers to try when the current one fails.

        Returns:

            List of provider names ordered by preference for fallback.

        """

        fallbacks = []

        current = self.provider

        for name, info in PROVIDERS.items():

            if name == current:

                continue

            if info.get("requires_key", True) and not self.api_key:

                continue

            if name in fallbacks:

                continue

            fallbacks.append(name)

        local_first = [p for p in fallbacks if p in LOCAL_PROVIDERS]

        remote_first = [p for p in fallbacks if p not in LOCAL_PROVIDERS]

        return local_first + remote_first

    def _try_fallback_provider(self, user_input: str) -> Tuple[bool, str]:

        """Try an alternative provider when the current one fails.

        Returns:

            (success, response_or_error_message)

        """

        fallback_providers = self._get_fallback_providers()

        original_provider = self.provider

        original_base_url = self.base_url

        original_model = self.model

        for fallback_name in fallback_providers:

            pinfo = PROVIDERS.get(fallback_name)

            if not pinfo:

                continue

            try:

                self.provider = fallback_name

                self.base_url = pinfo["base_url"]

                self.model = pinfo.get("default_model", self.model)

                self.last_error = None

                self.last_error_type = None

                validation_error = self._validate_settings()

                if validation_error:

                    continue

                response = self._call_api_with_retry()

                assistant_msg = response["choices"][0]["message"]["content"]

                self.messages.append({"role": "assistant", "content": assistant_msg})

                self._trim_history()

                self._save_messages()

                return True, assistant_msg

            except Exception:

                continue

            finally:

                self.provider = original_provider

                self.base_url = original_base_url

                self.model = original_model

        return False, ""

def parse_command_from_response(response: str) -> Optional[str]:

    match = re.search(r"<command>(.*?)</command>", response, re.DOTALL)

    if match:

        return match.group(1).strip()

    return None

def strip_command_tags(response: str) -> str:
    if not response:
        return ""
    text = response
    # Handle JSON wrapped tool calls string
    if ("tool_calls" in text and (text.startswith("{") or text.endswith("}"))):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                text = data.get("content", "")
        except Exception:
            pass
    text = re.sub(r"<command>.*?</command>", "", text, flags=re.DOTALL)
    text = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL)
    return text.strip()