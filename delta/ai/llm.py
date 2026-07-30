import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any


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

## Guidelines
- Always prioritize security ethics. Only run commands on systems you have authorization to test.
- For general conversation, questions, writing code, analysis, or tasks outside Delta's scope, just respond conversationally as a helpful AI.
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
        max_history: int = 50,
    ):
        self.api_key = api_key or os.environ.get("DELTA_API_KEY", "")
        self.base_url = (
            base_url
            or os.environ.get("DELTA_API_BASE_URL", "")
            or "https://api.openai.com/v1"
        )
        self.model = model or os.environ.get("DELTA_LLM_MODEL", "gpt-4o-mini")
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []
        self._system_prompt = SYSTEM_PROMPT
        self.messages.append({"role": "system", "content": self._system_prompt})

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def reset_conversation(self) -> None:
        self.messages = [{"role": "system", "content": self._system_prompt}]

    def add_system_context(self, context: str) -> None:
        self.messages.append({"role": "system", "content": context})

    def chat(self, user_input: str) -> str:
        if not self.is_configured:
            return "ERROR: API key not configured. Set DELTA_API_KEY environment variable or configure in settings."

        self.messages.append({"role": "user", "content": user_input})

        try:
            response = self._call_api()
            assistant_msg = response["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": assistant_msg})
            self._trim_history()
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

        data = {
            "model": self.model,
            "messages": self.messages[-50:],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Delta-CLI/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))


def parse_command_from_response(response: str) -> Optional[str]:
    match = re.search(r"<command>(.*?)</command>", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def strip_command_tags(response: str) -> str:
    return re.sub(r"<command>.*?</command>", "", response, flags=re.DOTALL).strip()
