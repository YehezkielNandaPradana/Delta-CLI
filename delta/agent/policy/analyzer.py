import re
from dataclasses import dataclass
from delta.agent.policy.risk import ToolRisk

@dataclass
class CommandAnalysisResult:
    command: str
    detected_risk: ToolRisk
    is_destructive: bool
    is_privileged: bool
    has_chaining: bool
    has_dangerous_pipe: bool
    reason: str

class CommandSafetyAnalyzer:
    DESTRUCTIVE_SHELL_PATTERNS = [
        (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b"), "Recursive forced file deletion (rm -rf)"),
        (re.compile(r"\bdel\s+/[sS]\s+/[qQ]\b|\brshift\b|\brmdir\s+/[sS]\b"), "Windows recursive force delete"),
        (re.compile(r"\bmkfs\b|\bfdisk\b|\bdd\s+if="), "Raw disk or filesystem formatting"),
    ]

    DESTRUCTIVE_GIT_PATTERNS = [
        (re.compile(r"\bgit\s+reset\s+--hard\b"), "Destructive git reset --hard"),
        (re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f\b"), "Destructive git clean -f"),
        (re.compile(r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b"), "Force git push"),
        (re.compile(r"\bgit\s+checkout\s+\.\b|\bgit\s+restore\s+\.\b"), "Discard all working tree modifications"),
    ]

    PRIVILEGED_PATTERNS = [
        (re.compile(r"\bsudo\b|\brunas\b|\bsu\s+-\b|\bchmod\s+-R\s+777\b|\bchown\s+-R\b"), "Privilege escalation or wide permissions"),
    ]

    DANGEROUS_PIPES = [
        (re.compile(r"\|\s*(bash|sh|zsh|python|perl|ruby)\b"), "Remote or unverified script piping to shell"),
    ]

    READ_ONLY_PREFIXES = ["git status", "git log", "git diff", "ls", "dir", "pwd", "whoami", "cat", "type", "findstr", "grep"]

    def analyze(self, command: str) -> CommandAnalysisResult:
        cmd_clean = command.strip()

        # 1. Privileged check
        for pat, reason in self.PRIVILEGED_PATTERNS:
            if pat.search(cmd_clean):
                return CommandAnalysisResult(
                    command=cmd_clean,
                    detected_risk=ToolRisk.HIGH_IMPACT,
                    is_destructive=True,
                    is_privileged=True,
                    has_chaining=";" in cmd_clean or "&&" in cmd_clean,
                    has_dangerous_pipe=False,
                    reason=reason
                )

        # 2. Destructive check
        for pat, reason in self.DESTRUCTIVE_SHELL_PATTERNS + self.DESTRUCTIVE_GIT_PATTERNS:
            if pat.search(cmd_clean):
                return CommandAnalysisResult(
                    command=cmd_clean,
                    detected_risk=ToolRisk.HIGH_IMPACT,
                    is_destructive=True,
                    is_privileged=False,
                    has_chaining=";" in cmd_clean or "&&" in cmd_clean,
                    has_dangerous_pipe=False,
                    reason=reason
                )

        # 3. Dangerous pipe check
        for pat, reason in self.DANGEROUS_PIPES:
            if pat.search(cmd_clean):
                return CommandAnalysisResult(
                    command=cmd_clean,
                    detected_risk=ToolRisk.HIGH_IMPACT,
                    is_destructive=True,
                    is_privileged=False,
                    has_chaining=False,
                    has_dangerous_pipe=True,
                    reason=reason
                )

        # 4. Read only prefix check
        for prefix in self.READ_ONLY_PREFIXES:
            if cmd_clean.startswith(prefix):
                return CommandAnalysisResult(
                    command=cmd_clean,
                    detected_risk=ToolRisk.READ,
                    is_destructive=False,
                    is_privileged=False,
                    has_chaining=";" in cmd_clean or "&&" in cmd_clean,
                    has_dangerous_pipe=False,
                    reason="Standard read-only diagnostic or inspect command"
                )

        # 5. Normal test/build command
        return CommandAnalysisResult(
            command=cmd_clean,
            detected_risk=ToolRisk.LOW_WRITE,
            is_destructive=False,
            is_privileged=False,
            has_chaining=";" in cmd_clean or "&&" in cmd_clean,
            has_dangerous_pipe=False,
            reason="Standard execution/build command"
        )
