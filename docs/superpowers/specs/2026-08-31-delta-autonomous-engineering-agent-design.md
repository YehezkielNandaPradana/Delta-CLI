# Spec: Delta Autonomous Software Engineering Agent Architecture

**Spec File:** `docs/superpowers/specs/2026-08-31-delta-autonomous-engineering-agent-design.md`  
**Date:** 2026-08-31  
**Status:** Approved Specification  

---

## 1. Overview
Delta expands into a general-purpose, persistent, autonomous software and security engineering agent runtime. Delta operates under a deterministic state machine with policy-driven safe execution, repository graph intelligence, and full regression verification.

## 2. Core Modules
- `delta/agent/policy/`: `ExecutionPolicy`, `CommandSafetyAnalyzer`, `AutonomyMode` (STRICT, SUPERVISED, AUTONOMOUS), `WorkspaceScope`, `RolePermission`.
- `delta/agent/state/`: `TaskState`, `CheckpointManager`, `.delta/` persistence.
- `delta/agent/runtime/`: `AgentLifecycle`, `AgentCoordinator`, `ScopedWorker` fleet.
- `delta/agent/planner/`: `Plan`, `PlanStep`, `PlanEngine` with dynamic replanning.
- `delta/intelligence/repository/`: `RepositoryGraph`, `LanguageDetector`, `IncrementalIndexer`.
- `delta/intelligence/context/`: Layered Context Engine (L0-L7) with token budget allocation.
- `delta/tools/`: Policy-wrapped `ToolRegistry` spanning filesystem, code, execution, git, and security.

## 3. Policy & Safety Engine
- Invariant: LLM is never the authority for permissions.
- Effective Permission = Global Policy ∩ Role Matrix ∩ Workspace Scope ∩ Security Scope.
- Autonomy modes: STRICT (prompt all mutations), SUPERVISED (prompt HIGH_IMPACT & out-of-workspace), FULL_AUTONOMOUS (non-interactive, deterministic block on violations).

## 4. Phased Execution Roadmap
1. Phase 1: Policy Engine, Task State & Checkpointing
2. Phase 2: Repository Graph & AST Intelligence
3. Phase 3: Context Engine L0-L7
4. Phase 4: Plan Engine & Tool Runtime Integration
5. Phase 5: Verification & Automated Test Loop
6. Phase 6: Auto-Debugger & Root Cause Classifier
7. Phase 7: Self-Reviewer & Regression Watcher
8. Phase 8: Multi-Worker Coordination
9. Phase 9: Unified Security Tooling Integration
10. Phase 10: CLI TUI & Web Workstation
11. Phase 11: CI/CD & SARIF Reporting
