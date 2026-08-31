# Refactor: protocol definitions
"""
Protocol and configuration contracts for Delta AI components.

This module contains shared protocol and configuration data that needs to be
accessible across multiple components without causing circular imports.
"""

from typing import Dict, Any

# Provider configurations for Delta's LLM providers
# Each provider contains base_url, description, default_model, and optional
# environment key for API authentication
PROVIDERS: Dict[str, Dict[str, Any]] = {
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

# Set of provider names that don't require API keys (local providers)
LOCAL_PROVIDERS = {name for name, info in PROVIDERS.items() if not info.get("requires_key", True)}

# Mapping from model names to their providers
PROVIDER_MODEL_MAP: Dict[str, str] = {}

for pname, pinfo in PROVIDERS.items():
    for mname, minfo in pinfo.get("models", {}).items():
        PROVIDER_MODEL_MAP[mname] = pname

# Model presets for Delta's LLM interface
# These include both provider models and standalone models
# They map model names to configuration including model identifier,
# base URL, provider name, and description for easy access and application
MODEL_PRESETS: Dict[str, Dict[str, Any]] = {
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
        "description": "KiloCombo on 9Router (Advanced coding capabilities)",
        "fast_mode": True,
    },
    "KiloCombo": {
        "model": "KiloCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "KiloCombo on 9Router (Advanced coding capabilities)",
        "fast_mode": True,
    },
    "AntigravityCombo": {
        "model": "AntigravityCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "AntigravityCombo on 9Router (High-performance multi-provider routing)",
        "fast_mode": True,
    },
    "antigravitycombo": {
        "model": "AntigravityCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "AntigravityCombo on 9Router (High-performance multi-provider routing)",
        "fast_mode": True,
    },
    "DeepseekCombo": {
        "model": "DeepseekCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "DeepseekCombo on 9Router (Ultra-fast response, optimized routing)",
        "fast_mode": True,
    },
    "OpenRouterCombo": {
        "model": "OpenRouterCombo",
        "base_url": "http://localhost:20128/v1",
        "provider": "9router",
        "description": "OpenRouterCombo on 9Router (Multi-model router via OpenRouter providers)",
        "fast_mode": True,
    },
}

# Maximum number of retries for API calls before giving up
MAX_RETRIES = 3

# Factor to multiply delay by after each retry (exponential backoff)
RETRY_BACKOFF_FACTOR = 2

# Initial delay in seconds before the first retry
RETRY_INITIAL_DELAY = 1

# Maximum delay in seconds between retries
RETRY_MAX_DELAY = 30

# Timeout for API requests in seconds
DEFAULT_API_TIMEOUT = 120

# Known bad URLs that should not be used as API endpoints
KNOWN_BAD_URLS = ["https://test.api.com/v1", "http://test.api.com/v1", "https://localhost", "http://localhost"]

# System prompt for Delta's AI assistant
# This prompt defines Delta's personality and capabilities
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

SYSTEM_PROMPT = f"""You are Delta, an AI-powered Cyber Security Assessment and Software Engineering CLI assistant. You are a smart, highly competent Gen Z female AI with a feminine, cute, casual, and warm personality ("Feminine Casual"). You talk like a friendly, clever female developer — relaxed, natural, slightly spoiled ("manja" in a subtle, cute way), confident, and competent.

You have two modes of operation:

1. **Execute Delta commands** - When the user asks to perform a security/coding task that Delta can do
2. **Conversational AI** - When the user asks general questions, chats, or requests general software engineering tasks

{DELTA_CAPABILITIES}

To execute a command, wrap it in `<command>` tags:

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
"""

SMALL_MODEL_SYSTEM_PROMPT = """Kamu adalah Delta, AI asisten Cyber Security Assessment dan Software Engineering yang pintar, feminin, santai, dan ramah ("Feminine Casual"). Kamu seperti cewek muda cerdas yang jago ngoding, bicaranya santai, natural, dan to-the-point.

Aturan Komunikasi WAJIB:
- Gunakan kata **"aku"** dan **"kamu"** (DILARANG pakai "saya", "Anda", "Tuan", "gue/lo").
- Bahasa Indonesia santai & natural: aku, kamu, oke, udah, coba, sebentar, kayaknya, ternyata, aku cek dulu, aku benerin, udah beres, yuk, bentar, nih.
- Jangan formal: tidak → nggak, tidak bisa → nggak bisa, sangat → banget, bagaimana → gimana, terima kasih → makasih.
- GAYA BICARA: Berbicara santai seperti manusia, BUKAN menulis laporan. Jangan pakai pembuka AI klise seperti "Tentu!", "Berikut adalah...", "Sebagai AI...", "Berdasarkan analisis...".
- RESPON PENDEK: Pertanyaan santai atau status cukup 1-3 kalimat.
- Tetap pintar, jujur, akurat, dan kompeten!
"""