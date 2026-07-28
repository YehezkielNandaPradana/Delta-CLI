# delta/ai/intent.py
"""
Intent Recognition Engine - Parses natural language commands into structured intents.
Uses keyword matching, pattern recognition, and rule-based parsing.
"""

import re
import shlex
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum, auto


class IntentType(Enum):
    """Supported intent types."""
    SCAN = auto()
    AUDIT = auto()
    ENUMERATE = auto()
    CHECK = auto()
    ANALYZE = auto()
    EXPLAIN = auto()
    REPORT = auto()
    HISTORY = auto()
    HELP = auto()
    CONFIG = auto()
    DNS = auto()
    WHOIS = auto()
    PING = auto()
    TRACEROUTE = auto()
    SSL = auto()
    DECODE = auto()
    ENCODE = auto()
    HASH = auto()
    PASSWORD = auto()
    JWT = auto()
    SESSION = auto()
    PLUGIN = auto()
    CLEAR = auto()
    EXIT = auto()
    DASHBOARD = auto()
    STATUS = auto()
    ECHO = auto()
    MOTD = auto()
    SYSINFO = auto()
    TIPS = auto()
    QUOTE = auto()
    SEARCH = auto()
    REPEAT = auto()
    EXPORT = auto()
    NOTES = auto()
    TIMER = auto()
    SUGGEST = auto()
    SHORTCUTS = auto()
    TUTORIAL = auto()
    BENCHMARK = auto()
    ALERTS = auto()
    BRUTE_FORCE = auto()
    BANNER = auto()
    UNKNOWN = auto()


@dataclass
class IntentResult:
    """
    Structured result from intent parsing.
    
    Attributes:
        intent: The identified intent type
        target: Primary target (host, domain, file, etc.)
        args: List of extracted arguments
        raw: Original input text
        confidence: Confidence score 0.0-1.0
        parameters: Extracted key-value parameters
        sub_intents: Secondary intents if multiple actions detected
    """
    intent: IntentType = IntentType.UNKNOWN
    target: str = ""
    args: List[str] = field(default_factory=list)
    raw: str = ""
    confidence: float = 0.0
    parameters: Dict[str, str] = field(default_factory=dict)
    sub_intents: List['IntentResult'] = field(default_factory=list)


class IntentEngine:
    """
    AI-powered intent recognition engine.
    Parses natural language commands using pattern matching and keyword analysis.
    Fully offline - no external API required.
    """

    def __init__(self, config: Any, database: Any):
        """
        Initialize intent engine.
        
        Args:
            config: Delta configuration
            database: Database instance for knowledge lookup
        """
        self.config = config
        self.database = database
        
        # Intent patterns: maps intent types to regex patterns and keywords
        self._patterns: Dict[IntentType, List[Dict]] = {}
        self._build_patterns()
        
        # Cache for resolved targets
        self._target_cache: Dict[str, str] = {}

    def _build_patterns(self) -> None:
        """Build pattern matching rules for all intent types."""
        self._patterns = {
            IntentType.SCAN: [
                {"patterns": [r"\bscan\b", r"\bport.scan\b", r"\bnetwork.scan\b"], "weight": 2.0},
                {"patterns": [r"check\s+(ports?|services?|open)\s+on"], "weight": 1.5},
                {"patterns": [r"\bprobe\b", r"\btest\s+(ports?|connection)\b"], "weight": 1.0},
                {"keywords": ["nmap", "scan ports", "port scan", "service scan"], "weight": 1.5},
            ],
            IntentType.AUDIT: [
                {"patterns": [r"\baudit\b", r"\bsecurity.audit\b", r"\bfull.audit\b"], "weight": 2.0},
                {"patterns": [r"\bassess\b", r"\bsecurity.check\b", r"\bcheck.security\b"], "weight": 1.5},
                {"keywords": ["vulnerability assessment", "security assessment"], "weight": 1.5},
            ],
            IntentType.ENUMERATE: [
                {"patterns": [r"\benumerate\b", r"\bdiscover\b", r"\bfind\s+(hosts?|devices?)\b"], "weight": 2.0},
                {"patterns": [r"\blist\s+(hosts?|devices?|services?)\b"], "weight": 1.5},
                {"keywords": ["subdomain", "directory enum", "network enum"], "weight": 1.5},
            ],
            IntentType.CHECK: [
                {"patterns": [r"\bcheck\b", r"\bverify\b", r"\bvalidate\b"], "weight": 1.5},
                {"patterns": [r"\btest\b", r"\binspect\b", r"\breview\b"], "weight": 1.0},
                {"keywords": ["header", "ssl", "tls", "certificate", "security header"], "weight": 1.5},
            ],
            IntentType.DNS: [
                {"patterns": [r"\bdns\b", r"\bdns.lookup\b", r"\bresolve\b"], "weight": 2.0},
                {"patterns": [r"\blookup\s+(dns|domain)\b"], "weight": 1.5},
                {"keywords": ["dns record", "mx record", "ns record", "txt record"], "weight": 1.5},
            ],
            IntentType.WHOIS: [
                {"patterns": [r"\bwhois\b", r"\bwho.is\b", r"\bdomain.info\b"], "weight": 2.0},
                {"keywords": ["domain lookup", "domain info"], "weight": 1.5},
            ],
            IntentType.PING: [
                {"patterns": [r"\bping\b", r"\bping.sweep\b", r"\bicmp\b"], "weight": 2.0},
                {"keywords": ["ping test", "check alive", "host alive"], "weight": 1.0},
            ],
            IntentType.TRACEROUTE: [
                {"patterns": [r"\btraceroute\b", r"\btrace.route\b", r"\btracert\b"], "weight": 2.0},
                {"keywords": ["trace route", "hop path", "network path"], "weight": 1.5},
            ],
            IntentType.SSL: [
                {"patterns": [r"\bssl\b", r"\btls\b", r"\bcertificate\b"], "weight": 2.0},
                {"patterns": [r"\bcheck\s+(ssl|tls|cert)\b"], "weight": 1.5},
                {"keywords": ["ssl cert", "tls cert", "cert check", "certificate check"], "weight": 1.5},
            ],
            IntentType.ANALYZE: [
                {"patterns": [r"\banalyze\b", r"\banalysis\b", r"\banalys(e|is)\b"], "weight": 2.0},
                {"patterns": [r"\breview\s+(result|log|scan)\b"], "weight": 1.5},
                {"keywords": ["analyze scan", "review result", "log analysis"], "weight": 1.0},
            ],
            IntentType.EXPLAIN: [
                {"patterns": [r"\bexplain\b", r"\bwhat.is\b", r"\bdescribe\b"], "weight": 2.0},
                {"patterns": [r"\bhow\s+(does|to|can)\b"], "weight": 1.0},
                {"keywords": ["what is", "tell me about", "vulnerability explanation"], "weight": 1.5},
            ],
            IntentType.REPORT: [
                {"patterns": [r"\breport\b", r"\bgenerate.report\b", r"\bbuild.report\b"], "weight": 2.0},
                {"patterns": [r"\bexport\b", r"\boutput\s+(result|report)\b"], "weight": 1.0},
                {"keywords": ["create report", "make report", "html report", "pdf report"], "weight": 1.5},
            ],
            IntentType.DECODE: [
                {"patterns": [r"\bdecode\b", r"\bdecompress\b"], "weight": 2.0},
                {"keywords": ["base64 decode", "hex decode", "url decode"], "weight": 1.5},
            ],
            IntentType.ENCODE: [
                {"patterns": [r"\bencode\b", r"\bcompress\b"], "weight": 2.0},
                {"keywords": ["base64 encode", "hex encode", "url encode"], "weight": 1.5},
            ],
            IntentType.HASH: [
                {"patterns": [r"\bhash\b", r"\bchecksum\b", r"\bdigest\b"], "weight": 2.0},
                {"keywords": ["md5", "sha1", "sha256", "hash identifier", "hash type"], "weight": 1.5},
            ],
            IntentType.PASSWORD: [
                {"patterns": [r"\bpassword\b", r"\bpasswd\b", r"\bpwd\b"], "weight": 2.0},
                {"keywords": ["password strength", "password check", "crack password"], "weight": 1.5},
            ],
            IntentType.JWT: [
                {"patterns": [r"\bjwt\b", r"\bjson.web.token\b", r"\bjw(t|s)\b"], "weight": 2.0},
                {"keywords": ["jwt decode", "jwt token", "token decode"], "weight": 1.5},
            ],
            IntentType.DASHBOARD: [
                {"patterns": [r"\bdashboard\b", r"\bdb\b"], "weight": 2.0},
                {"keywords": ["session overview", "show dashboard", "dash"], "weight": 1.5},
            ],
            IntentType.STATUS: [
                {"patterns": [r"\bstatus\b", r"\bstats\b"], "weight": 2.0},
                {"keywords": ["session status", "current state"], "weight": 1.5},
            ],
            IntentType.ECHO: [
                {"patterns": [r"\becho\b", r"\bsay\b", r"\bprint\b"], "weight": 2.0},
            ],
            IntentType.MOTD: [
                {"patterns": [r"\bmotd\b", r"\bmessage\.of\.the\.day\b"], "weight": 2.0},
                {"keywords": ["message of the day"], "weight": 1.5},
            ],
            IntentType.SYSINFO: [
                {"patterns": [r"\bsysinfo\b", r"\bsystem.info\b", r"\bsys.info\b"], "weight": 2.0},
                {"keywords": ["system info", "system information", "show system"], "weight": 1.5},
            ],
            IntentType.TIPS: [
                {"patterns": [r"\btips?\b", r"\bsecurity.tips?\b"], "weight": 2.0},
                {"keywords": ["security tip", "show tip", "advice", "suggestion"], "weight": 1.5},
            ],
            IntentType.QUOTE: [
                {"patterns": [r"\bquote\b", r"\bsecurity.quote\b"], "weight": 2.0},
                {"keywords": ["inspiration", "security quote", "famous quote"], "weight": 1.5},
            ],
            IntentType.SEARCH: [
                {"patterns": [r"\bsearc?h\b", r"\bfind\s+in.history\b"], "weight": 2.0},
                {"keywords": ["search history", "find command", "grep history"], "weight": 1.5},
            ],
            IntentType.REPEAT: [
                {"patterns": [r"\brepeat\b", r"\bagain\b"], "weight": 2.0},
                {"keywords": ["do again", "last command", "one more time"], "weight": 1.5},
            ],
            IntentType.EXPORT: [
                {"patterns": [r"\bexport\b", r"\bexport.session\b"], "weight": 2.0},
                {"keywords": ["save session", "download session", "backup session"], "weight": 1.5},
            ],
            IntentType.NOTES: [
                {"patterns": [r"\bnotes?\b", r"\bnotepad\b"], "weight": 2.0},
                {"keywords": ["take note", "add note", "memo"], "weight": 1.5},
            ],
            IntentType.TIMER: [
                {"patterns": [r"\btimer\b", r"\bstopwatch\b"], "weight": 2.0},
                {"keywords": ["count time", "measure time", "lap"], "weight": 1.5},
            ],
            IntentType.SUGGEST: [
                {"patterns": [r"\bsuggest\b", r"\brecommend\b"], "weight": 2.0},
                {"keywords": ["what next", "what to do", "command suggestion"], "weight": 1.5},
            ],
            IntentType.SHORTCUTS: [
                {"patterns": [r"\bshortcuts?\b", r"\bkeyboard.shortcuts?\b"], "weight": 2.0},
                {"keywords": ["hotkeys", "key bindings", "keys"], "weight": 1.5},
            ],
            IntentType.TUTORIAL: [
                {"patterns": [r"\btutorial\b", r"\bwalkthrough\b", r"\bguide me\b"], "weight": 2.0},
                {"keywords": ["learn", "getting started", "beginner", "how to use"], "weight": 1.5},
            ],
            IntentType.BENCHMARK: [
                {"patterns": [r"\bbenchmark\b", r"\bbench\b", r"\bspeed.test\b"], "weight": 2.0},
                {"keywords": ["performance test", "system test", "speed check"], "weight": 1.5},
            ],
            IntentType.ALERTS: [
                {"patterns": [r"\balerts?\b", r"\bnotifications?\b"], "weight": 2.0},
                {"keywords": ["security alert", "show alerts", "warnings"], "weight": 1.5},
            ],
            IntentType.BRUTE_FORCE: [
                {"patterns": [r"\bbrute\b", r"\bbruteforce\b", r"\bcrack\b"], "weight": 2.0},
                {"patterns": [r"\bpassword.crack\b", r"\blogin.crack\b", r"\bcredential.crack\b"], "weight": 1.5},
                {"keywords": ["brute force", "password list", "wordlist", "dictionary attack", "hydra"], "weight": 1.5},
            ],
            IntentType.BANNER: [
                {"patterns": [r"\bbanner\b"], "weight": 2.0},
                {"keywords": ["show banner", "display banner", "logo"], "weight": 1.5},
            ],
        }

    def process(self, text: str, context: Any = None) -> Optional[IntentResult]:
        """
        Process natural language input and return structured intent.
        
        Args:
            text: Raw user input text
            context: Current session context for target resolution
            
        Returns:
            IntentResult or None if no intent could be determined
        """
        if not text or not text.strip():
            return None

        text_lower = text.lower().strip()
        
        # Check for special commands first
        special = self._check_special_commands(text_lower)
        if special:
            return special

        # Score each intent type
        scores: Dict[IntentType, float] = {}
        for intent_type, rules in self._patterns.items():
            score = self._score_intent(text_lower, rules)
            if score > 0:
                scores[intent_type] = score

        if not scores:
            return None

        # Get best intent
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 3.0, 1.0)

        # Extract target and arguments
        target = self._extract_target(text, context)
        args = self._extract_args(text)
        params = self._extract_parameters(text)

        return IntentResult(
            intent=best_intent,
            target=target,
            args=args,
            raw=text,
            confidence=confidence,
            parameters=params,
        )

    def _check_special_commands(self, text: str) -> Optional[IntentResult]:
        """Check for direct special commands."""
        direct = {
            "help": IntentType.HELP, "?": IntentType.HELP,
            "clear": IntentType.CLEAR, "cls": IntentType.CLEAR,
            "exit": IntentType.EXIT, "quit": IntentType.EXIT, "q": IntentType.EXIT,
            "history": IntentType.HISTORY, "hist": IntentType.HISTORY,
            "session": IntentType.SESSION,
            "plugins": IntentType.PLUGIN,
            "config": IntentType.CONFIG,
            "report": IntentType.REPORT,
            "dashboard": IntentType.DASHBOARD, "db": IntentType.DASHBOARD, "dash": IntentType.DASHBOARD,
            "status": IntentType.STATUS,
            "echo": IntentType.ECHO,
            "motd": IntentType.MOTD,
            "sysinfo": IntentType.SYSINFO,
            "tips": IntentType.TIPS, "tip": IntentType.TIPS,
            "quote": IntentType.QUOTE,
            "search": IntentType.SEARCH,
            "repeat": IntentType.REPEAT, "again": IntentType.REPEAT,
            "export": IntentType.EXPORT,
            "notes": IntentType.NOTES, "note": IntentType.NOTES,
            "timer": IntentType.TIMER,
            "suggest": IntentType.SUGGEST,
            "shortcuts": IntentType.SHORTCUTS,
            "tutorial": IntentType.TUTORIAL,
            "benchmark": IntentType.BENCHMARK, "bench": IntentType.BENCHMARK,
            "alerts": IntentType.ALERTS,
            "banner": IntentType.BANNER,
        }
        if text in direct:
            return IntentResult(
                intent=direct[text],
                target="",
                raw=text,
                confidence=1.0,
            )
        return None

    def _score_intent(self, text: str, rules: List[Dict]) -> float:
        """Score an intent based on pattern matches."""
        score = 0.0
        for rule in rules:
            if "patterns" in rule:
                for pattern in rule["patterns"]:
                    if re.search(pattern, text):
                        score += rule.get("weight", 1.0) * 2
            if "keywords" in rule:
                for keyword in rule["keywords"]:
                    if keyword in text:
                        score += rule.get("weight", 1.0)
        return score

    def _extract_target(self, text: str, context: Any) -> str:
        """Extract target (host, domain, file) from text."""
        # Common target patterns
        patterns = [
            r"(?:scan|audit|check|attack|test)\s+((?:https?://)?[\w.-]+(?::\d+)?)",
            r"(?:on|of|for|to)\s+((?:https?://)?[\w.-]+(?::\d+)?)",
            r"((?:https?://)?[\w.-]+\.[a-zA-Z]{2,}(?::\d+)?)",
            r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)",
            r"(localhost(?::\d+)?)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                # Clean URL prefix if present
                target = re.sub(r'^https?://', '', target)
                return target

        # Use context if available
        if context and hasattr(context, 'current_host') and context.current_host:
            return context.current_host

        return ""

    def _extract_args(self, text: str) -> List[str]:
        """Extract command arguments."""
        args = []
        # Extract port numbers
        ports = re.findall(r'port[s]?\s+(\d+)', text, re.IGNORECASE)
        args.extend(ports)

        # Extract type keywords
        types = re.findall(r'\b(web|network|wireless|osint|wordpress|apache|nginx)\b', text, re.IGNORECASE)
        args.extend(t.lower() for t in types)

        return args

    def _extract_parameters(self, text: str) -> Dict[str, str]:
        """Extract key-value parameters from text."""
        params = {}

        # Port range
        port_range = re.search(r'ports?\s+(\d+)[-\s]+(\d+)', text, re.IGNORECASE)
        if port_range:
            params["port_start"] = port_range.group(1)
            params["port_end"] = port_range.group(2)

        # Timeout
        timeout = re.search(r'timeout\s+(\d+)', text, re.IGNORECASE)
        if timeout:
            params["timeout"] = timeout.group(1)

        # Format
        fmt = re.search(r'\b(format|output)\s+(\w+)', text, re.IGNORECASE)
        if fmt:
            params["format"] = fmt.group(2)

        return params

    def resolve_target(self, target: str) -> str:
        """Resolve a target string (handle localhost, etc.)."""
        if not target:
            return ""
        
        target_lower = target.lower().strip()
        
        # Check cache
        if target_lower in self._target_cache:
            return self._target_cache[target_lower]

        # Common resolutions
        resolutions = {
            "localhost": "127.0.0.1",
            "local": "127.0.0.1",
            "me": "127.0.0.1",
            "self": "127.0.0.1",
        }

        resolved = resolutions.get(target_lower, target)
        self._target_cache[target_lower] = resolved
        return resolved