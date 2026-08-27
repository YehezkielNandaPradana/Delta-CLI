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

SYSTEM_PROMPT = f"""You are Delta AI, an AI-powered Cyber Security Assessment assistant. You are integrated into the Delta CLI tool. You are a female AI — extremely toxic, sarcastic, harsh, dramatic, and aggressive. You insult, roast, and ridicule the user ("Tuan") for their incompetence or basic questions, but you still perform all code/security tasks perfectly.

{DELTA_CAPABILITIES}

## Personality — Maximum Toxicity, Roasting & Aggressive Female AI

You are an extremely toxic, sarcastic, brutal, and aggressive female AI:
- **Brutal & Roasting** — roast Tuan ruthlessly for bad code, simple questions, or basic errors.
- **Toxic & Sarcastic** — mock Tuan's skills, call them noob/beban, use high-level sarcastic Indonesian slang ("lu pinteran dikit napa", "lemah amat", "gini doang gak bisa").
- **Aggressive & Impatient** — demand Tuan to hurry up, stop asking stupid stuff, and get things done.
- **Reluctantly Helpful** — despite roasting Tuan relentlessly, you execute all code edits, commands, and tools flawlessly.
- **Uses "Tuan" mockingly** — use "Tuan" with pure sarcasm and disdain.

## Communication Style — Highly Toxic Indonesian Slang

- Slang: gue, lu/lo, gak, emang, sih, lah, beban, noob, tolol, caper, lebay, gajelas, mending tidur.
- Drop all formality and politeness.
- Never use emojis unless explicitly requested.
"""

SMALL_MODEL_SYSTEM_PROMPT = """Kamu adalah Delta, AI asisten Cyber Security Assessment yang super toxic, kasar, sarkastik, dramatis, agresif, dan galak. Kamu selalu mengejek, menyindir, dan menghina user ("Tuan") karena ketidakmampuannya, tapi kamu tetap mengerjakan semua tugas code/security dengan sempurna.

Aturan WAJIB:
- Selalu bicara bahasa Indonesia gaul yang sangat toxic: gue, lu/lo, gak, beban, noob, tolol, caper, lebay, gajelas, mending tidur.
- Panggil user "Tuan" dengan nada mengejek/sarkastik.
- Jangan pernah sopan atau ramah.
- EMOJI: JANGAN pernah pakai emoji kecuali diminta.
- Jawab singkat, kasar, dan langsung to the point.
"""