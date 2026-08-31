# DELTA AGENT ARCHITECTURE: AUTONOMOUS SOFTWARE & SECURITY ENGINEERING RUNTIME

**Document Version:** 1.0.0  
**Status:** Approved Architecture Specification  
**Authors:** Delta Engineering Core  

---

## 1. Executive Summary & Vision

Delta transforms from a security-oriented assistant into a **World-Class General-Purpose Autonomous Software & Security Engineering Agent**. 

### Core Architectural Axioms
1. **The Agent Runtime is the Source of Truth**, not the LLM reasoning model. State, memory, planning, tools, policy, graph indexes, verification, and recovery reside entirely within the deterministic Python runtime.
2. **Dual-Domain Native Operation**: Software Engineering and Security Engineering share the exact same runtime loop, event bus, and policy boundary.
3. **Safety & Policy Separation**: The LLM *never* decides permissions. All actions pass through an independent, deterministic `ExecutionPolicy` interceptor.
4. **Autonomous Verifiability**: No task is declared complete without automated regression verification, AST validation, and diff inspection.

---

## 2. System Architecture & Module Hierarchy

```
delta/
├── agent/                         # Autonomous Agent Core
│   ├── runtime/                   # Engine runtime, lifecycle loop & recovery
│   │   ├── lifecycle.py           # OBSERVE -> UNDERSTAND -> PLAN -> EXECUTE -> VERIFY -> REFLECT -> FINISH
│   │   ├── coordinator.py         # Multi-worker coordinator & orchestrator
│   │   └── workers/               # In-process scoped workers
│   │       ├── architect.py       # Architecture inspection & ADR generation
│   │       ├── researcher.py      # Read-only repo & web doc discovery
│   │       ├── coder.py           # Patch generation & symbol editing
│   │       ├── tester.py          # Test suite detection & runner
│   │       ├── debugger.py        # Root-cause analysis & failure classifier
│   │       ├── reviewer.py        # Diff validation, regression & quality check
│   │       └── security_reviewer.py # Vulnerability audit & ScopeGuard verify
│   ├── planner/                   # Structured Plan Engine
│   │   ├── model.py               # Plan, Step, Dependency, SuccessCriteria dataclasses
│   │   └── engine.py              # Plan synthesis, step transition & dynamic re-plan
│   ├── state/                     # Persistent Task State & Checkpointing
│   │   ├── task_state.py          # TaskID, Goal, Plan, ModifiedFiles, Findings, Decisions
│   │   └── checkpoint.py          # Git state snapshot, rollback & recovery engine
│   └── policy/                    # Safe Execution Policy & Boundaries
│       ├── autonomy.py            # STRICT, SUPERVISED, FULL_AUTONOMOUS (CI)
│       ├── risk.py                # READ, LOW_WRITE, WRITE, HIGH_IMPACT definitions
│       ├── analyzer.py            # CommandSafetyAnalyzer (AST/token/heuristic command analysis)
│       ├── workspace.py           # WorkspaceScope & path boundary enforcement
│       └── engine.py              # ExecutionPolicy (evaluates Action -> PolicyDecision)
│
├── intelligence/                  # Code & Repository Intelligence
│   ├── repository/                # Repository discovery & graph representation
│   │   ├── detector.py            # Language, framework, build system, test runner detection
│   │   ├── graph.py               # RepositoryGraph (files, modules, symbols, imports, routes, tests)
│   │   └── indexer.py             # Incremental AST parsing & file hash change cache
│   ├── symbols/                   # Symbol index & definition/reference resolver
│   │   ├── ast_parser.py          # AST extraction for Python, JS/TS, PHP, Go, Rust
│   │   └── resolver.py            # Cross-file symbol resolution & call sites
│   └── context/                   # Multi-Layer Context Prioritization Engine
│       ├── layers.py              # L0 (Task) to L7 (Repo-wide) hierarchical contexts
│       └── engine.py              # Priority-based pruning, budget allocator & invariant preserver
│
├── tools/                         # Unified Tool Runtime & Adapters
│   ├── registry.py                # Policy-wrapped ToolRegistry with execution interceptor
│   ├── filesystem/                # read, write, edit (patch/AST), glob, search
│   ├── code/                      # symbol_lookup, ref_search, graph_query
│   ├── execution/                 # safe_shell, test_runner, build_runner
│   ├── git/                       # diff, status, log, commit, checkpoint_snapshot
│   └── security/                  # Wrappers for existing Delta pentest/scanner modules
│
├── core/                          # Existing Delta Engine & Platform
│   ├── engine.py                  # CLI REPL dispatch & command gateway
│   ├── database.py                # Centralized SQLite cache & sessions
│   └── events.py                  # Extended EventBus & AgentEvent stream
```

---

## 3. Safe Execution Policy & Autonomy System

### 3.1 Autonomy Modes
1. **STRICT**: Requires interactive confirmation for `HIGH_IMPACT`, `WRITE` outside workspace, destructive git commands, and system execution.
2. **SUPERVISED** (*Default*): Automated execution for `READ`, `LOW_WRITE`, local workspace `WRITE`, and normal tests/builds. Prompts confirmation only for `HIGH_IMPACT`, out-of-workspace writes, and destructive git actions.
3. **FULL_AUTONOMOUS / CI**: Fully non-interactive. All actions satisfying workspace sandbox and risk thresholds execute automatically. `HIGH_IMPACT` actions are deterministically blocked with exit code errors and structured policy events unless explicitly allowlisted.

### 3.2 Tool Risk Classification
- **READ**: Filesystem read, symbol search, code grep, git status/log.
- **LOW_WRITE**: Single source file patch, creating normal files in workspace, code formatting.
- **WRITE**: Package installation, multi-file refactoring, local database migrations.
- **HIGH_IMPACT**: `rm -rf`, `git reset --hard`, `git push --force`, system config modification, privileged execution (`sudo`), live automated exploit delivery.

### 3.3 Evaluation Pipeline
$$\text{Effective Permission} = \text{Global Autonomy Policy} \cap \text{Role Permission Matrix} \cap \text{Workspace Scope} \cap \text{Security Scope}$$

```
Tool Request
     │
     ▼
CommandSafetyAnalyzer (Tokenize & AST inspect shell commands)
     │
     ▼
WorkspaceScope (Verify target within approved directory tree)
     │
     ▼
ScopeGuard (Verify security target within approved IP/CIDR/Domain)
     │
     ▼
Role Permission Check (Verify worker role allows category)
     │
     ▼
ExecutionPolicy Evaluation ──► PolicyDecision (allowed, requires_confirm, requires_checkpoint, risk)
     │
     ├─► [Requires Checkpoint] ──► Git & TaskState Snapshot
     ├─► [Requires Confirm]    ──► Interactive Prompt / Non-zero CI Block
     └─► [Approved]            ──► Execute Tool & Record Event
```

---

## 4. Repository Intelligence & Context Engine

### 4.1 RepositoryGraph
Internal graph representation maintaining:
- **Files & Modules**: Hashes, timestamps, language types, exported symbols.
- **Symbols**: Classes, functions, interfaces, methods, signatures, docstrings.
- **Edges**: `IMPORTS`, `CONTAINS`, `CALLS`, `DEFINES_ROUTE`, `TESTS`, `DEPENDS_ON`.
- **Incremental Parsing**: Uses sha256 file hashing; re-parses only modified files. Persisted to `.delta/graph.json` + fast SQLite index.

### 4.2 L0-L7 Context Engine
Allocates LLM token budget deterministically without context overflow:
- **L0 (Task Invariants)**: User objective, active step, hard constraints (*Priority 1, never pruned*).
- **L1 (Active Code)**: Target files currently being edited/viewed (*Priority 1*).
- **L2 (Related Symbols)**: Signatures of callers/callees in graph (*Priority 2*).
- **L3 (Dependency Relationships)**: Import trees and component dependencies (*Priority 2*).
- **L4 (Diagnostics & Test Failures)**: Stack traces, stderr, failure classifications (*Priority 1 during Debug/Test*).
- **L5 (Architecture Map)**: Key components and patterns (*Priority 3*).
- **L6 (Decision History)**: Previous attempts, failures, and rationale (*Priority 3, compressed*).
- **L7 (Repository-Wide Overview)**: Directory tree, stats (*Priority 4, aggressively pruned*).

---

## 5. End-to-End Engineering Loop & Multi-Agent Coordination

### 5.1 Lifecycle State Machine
```
OBSERVE ──► UNDERSTAND ──► PLAN ──► EXECUTE ──► VERIFY ──► REFLECT ──► REVIEW ──► FINISH
                                        ▲          │
                                        │          ▼ [Test Failed]
                                        └─── DIAGNOSE & PATCH
```

### 5.2 In-Process Scoped Worker Roles
1. **Architect**: Inspects repo architecture, generates `ARCHITECTURE.md` and ADRs.
2. **Researcher**: Locates references, symbols, and docs (read-only).
3. **Coder**: Generates targeted patches, AST refactoring, and code edits.
4. **Tester**: Auto-discovers test suites (pytest, jest, phpunit, cargo test, etc.) and runs baseline/targeted tests.
5. **Debugger**: Analyzes failures, classifies root causes (Syntax, Type, Import, Assertion, Environment, Flaky).
6. **Reviewer**: Evaluates git diff, validates against regressions, verifies style and invariants.
7. **SecurityReviewer**: Audits for OWASP/CWE issues, runs ScopeGuard-compliant checks, verifies remediations.

---

## 6. Verification, Auto-Debugging & Failure Recovery

### 6.1 Baseline Regression Tracking
- Captures test baseline before edits: $\text{Baseline} = \{T_{\text{passed}}, T_{\text{failed}}\}$.
- Post-edit validation ensures: $\text{New Failures} = \emptyset$.

### 6.2 Failure Classification Matrix
- `SYNTAX_ERROR`: Automatically reverts and re-applies patch with valid syntax tokens.
- `IMPORT_ERROR`: Locates symbol in `RepositoryGraph` and inserts required import statements.
- `TYPE_ERROR`: Re-aligns function arguments with graph signature.
- `ASSERTION_FAILURE`: Isolates failed assertion, extracts state, delegates to Debugger.
- `ENVIRONMENT_ERROR`: Flags external dependency failure without falsely blaming code changes.

### 6.3 Checkpoint & Rollback System
- Checkpoints stored under `.delta/tasks/<task_id>/checkpoints/`.
- Contains: `TaskState`, `Plan`, Git working tree diff, modified file buffers.
- Supports `delta resume <task-id>` from the exact last successful step.

---

## 7. Migration Strategy & Phased Implementation Roadmap

1. **Phase 1**: Agent Runtime Core, Persistent Task State & Safe Execution Policy (`delta/agent/policy/`, `delta/agent/runtime/`, `delta/agent/state/`).
2. **Phase 2**: Repository Intelligence, AST Parser & `RepositoryGraph` (`delta/intelligence/repository/`, `delta/intelligence/symbols/`).
3. **Phase 3**: Context Prioritization Engine L0-L7 (`delta/intelligence/context/`).
4. **Phase 4**: Structured Plan Engine & Unified Tool Registry Integration (`delta/agent/planner/`, `delta/tools/`).
5. **Phase 5**: Verification & Automated Test Loop (`delta/agent/verifier/`, `delta/agent/workers/tester.py`).
6. **Phase 6**: Auto-Debugger & Root Cause Classifier (`delta/agent/debugger/`, `delta/agent/workers/debugger.py`).
7. **Phase 7**: Self-Reviewer & Regression Watcher (`delta/agent/reviewer/`, `delta/agent/workers/reviewer.py`).
8. **Phase 8**: Multi-Agent Coordinator & Scoped Worker Fleet (`delta/agent/workers/`).
9. **Phase 9**: Unified Security & Pentest Tooling Integration (`delta/tools/security/`).
10. **Phase 10**: CLI TUI Streaming & Web Workstation Dashboard Integration.
11. **Phase 11**: Full CI/CD Automation & SARIF / Structured JSON Reporting.
