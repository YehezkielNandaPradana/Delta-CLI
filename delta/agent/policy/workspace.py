import os
from pathlib import Path
from typing import Dict, Set
from delta.agent.policy.risk import ToolRisk

class WorkspaceScope:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()

    def contains_path(self, target_path: str) -> bool:
        try:
            target = Path(target_path).resolve()
            return target == self.root_path or self.root_path in target.parents
        except Exception:
            return False

class RolePermissionMatrix:
    ROLE_MAX_RISK: Dict[str, ToolRisk] = {
        "architect": ToolRisk.READ,
        "researcher": ToolRisk.READ,
        "coder": ToolRisk.WRITE,
        "tester": ToolRisk.WRITE,
        "debugger": ToolRisk.LOW_WRITE,
        "reviewer": ToolRisk.READ,
        "security_reviewer": ToolRisk.LOW_WRITE,
        "main": ToolRisk.WRITE,
    }

    ROLE_ALLOWED_CATEGORIES: Dict[str, Set[str]] = {
        "architect": {"filesystem", "code", "architecture", "general"},
        "researcher": {"filesystem", "code", "search", "web", "general"},
        "coder": {"filesystem", "code", "execution", "general"},
        "tester": {"filesystem", "execution", "test", "general"},
        "debugger": {"filesystem", "code", "execution", "diagnostics", "general"},
        "reviewer": {"filesystem", "code", "git", "general"},
        "security_reviewer": {"filesystem", "security", "pentest", "code", "general"},
        "main": {"filesystem", "code", "execution", "git", "web", "security", "general"},
    }

    def is_allowed(self, role: str, risk: ToolRisk, category: str = "general") -> bool:
        role_key = role.lower()
        if role_key not in self.ROLE_MAX_RISK:
            return False
        max_risk = self.ROLE_MAX_RISK[role_key]
        if risk.level > max_risk.level:
            return False
        allowed_cats = self.ROLE_ALLOWED_CATEGORIES.get(role_key, set())
        return category.lower() in allowed_cats or "general" in allowed_cats
