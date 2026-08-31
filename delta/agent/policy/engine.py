from typing import Any, Dict, Optional
from delta.agent.policy.autonomy import AutonomyMode
from delta.agent.policy.risk import ToolRisk, PolicyDecision
from delta.agent.policy.analyzer import CommandSafetyAnalyzer
from delta.agent.policy.workspace import WorkspaceScope, RolePermissionMatrix


class ExecutionPolicy:
    def __init__(
        self,
        autonomy: AutonomyMode = AutonomyMode.SUPERVISED,
        workspace_root: str = ".",
        max_autonomous_risk: ToolRisk = ToolRisk.WRITE,
    ):
        self.autonomy = autonomy
        self.workspace = WorkspaceScope(workspace_root)
        self.role_matrix = RolePermissionMatrix()
        self.analyzer = CommandSafetyAnalyzer()
        self.max_autonomous_risk = max_autonomous_risk

    def evaluate_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        worker_role: str = "main",
        tool_category: str = "general",
    ) -> PolicyDecision:
        # 1. Determine base risk from tool & arguments
        risk = ToolRisk.LOW_WRITE
        reason = f"Execution of {tool_name}"
        rollback_strat = None

        if tool_name in [
            "read_file",
            "glob",
            "search",
            "grep",
            "git_status",
            "git_log",
        ]:
            risk = ToolRisk.READ
        elif tool_name in ["write_file", "edit_file", "patch_file"]:
            risk = ToolRisk.WRITE if "refactor" in str(tool_args) else ToolRisk.LOW_WRITE
            rollback_strat = "git_diff_revert"
        elif tool_name in ["shell", "execute_command"]:
            cmd = tool_args.get("command", "")
            cmd_res = self.analyzer.analyze(cmd)
            risk = cmd_res.detected_risk
            reason = cmd_res.reason
            if cmd_res.is_destructive:
                rollback_strat = "task_checkpoint_restore"

        # 2. Check path boundaries if file path present
        target_path = tool_args.get("file_path") or tool_args.get("path")
        if target_path and not self.workspace.contains_path(target_path):
            if risk.level < ToolRisk.WRITE.level:
                risk = ToolRisk.WRITE
            reason = f"Target path {target_path} is outside workspace root"

        # 3. Check Autonomy Mode first for HIGH_IMPACT or blocked autonomous risk
        if self.autonomy == AutonomyMode.FULL_AUTONOMOUS:
            if (
                risk.level > self.max_autonomous_risk.level
                or risk == ToolRisk.HIGH_IMPACT
            ):
                return PolicyDecision(
                    allowed=False,
                    requires_confirmation=False,
                    requires_checkpoint=False,
                    risk_level=risk,
                    reason=f"Action with risk {risk.value} is blocked in autonomous/CI mode",
                )

        # 4. Check Role Permission Matrix
        if not self.role_matrix.is_allowed(worker_role, risk, tool_category):
            return PolicyDecision(
                allowed=False,
                requires_confirmation=False,
                requires_checkpoint=False,
                risk_level=risk,
                reason=f"Worker role '{worker_role}' is not authorized for {risk.value} in {tool_category}",
            )

        # 5. Evaluate Autonomy Mode for allowed actions
        if self.autonomy == AutonomyMode.FULL_AUTONOMOUS:
            return PolicyDecision(
                allowed=True,
                requires_confirmation=False,
                requires_checkpoint=(risk.level >= ToolRisk.LOW_WRITE.level),
                risk_level=risk,
                reason=reason,
                rollback_strategy=rollback_strat,
            )

        if self.autonomy == AutonomyMode.STRICT:
            requires_confirm = risk.level >= ToolRisk.LOW_WRITE.level
            return PolicyDecision(
                allowed=True,
                requires_confirmation=requires_confirm,
                requires_checkpoint=(risk.level >= ToolRisk.LOW_WRITE.level),
                risk_level=risk,
                reason=reason,
                rollback_strategy=rollback_strat,
            )

        # SUPERVISED Mode (Default)
        requires_confirm = (risk == ToolRisk.HIGH_IMPACT) or bool(
            target_path and not self.workspace.contains_path(target_path)
        )
        return PolicyDecision(
            allowed=True,
            requires_confirmation=requires_confirm,
            requires_checkpoint=(risk.level >= ToolRisk.LOW_WRITE.level),
            risk_level=risk,
            reason=reason,
            rollback_strategy=rollback_strat,
        )
