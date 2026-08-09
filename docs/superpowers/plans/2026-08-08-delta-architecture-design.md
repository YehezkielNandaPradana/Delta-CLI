# Delta Architecture Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure Delta CLI into 9 namespace-owned areas with dependency direction enforcement, while preserving existing behavior (9Router + KiloCombo defaults) and keeping 127 tests green.

**Architecture:** Approach A — Namespace Ownership. Assign one owner per existing top-level namespace. Preserve runtime structure. Fix defects and add narrow contracts at boundaries. Work in 5 milestones: Stabilize → Contracts → Boundaries → Ownership → YAGNI trim.

**Tech Stack:** Python 3.11, stdlib only (no new dependencies), unittest, typing.Protocol, ast (for import audit).

## Global Constraints

- Preserve defaults: provider `9router`, base_url `http://localhost:20128/v1`, model `KiloCombo`.
- Zero new dependencies. Use stdlib only.
- No behavior change to runtime (REPL loop, intent parsing, module dispatch).
- All tests must remain passing at each step.
- YAGNI: no DI framework, no ABC hierarchy, no event system, no DeltaEngine refactor unless coverage >80% or contributor >3.
- Platform: Windows + Unix compatibility (encoding-safe output, lazy Flask).

---

## File Structure

```
delta/
├── __init__.py                 # minimal re-export (qa-team owns)
├── main.py                     # entry point (core-team)
├── ai/
│   ├── __init__.py             # ai-team
│   ├── llm.py                  # LLMEngine + MODEL_PRESETS (ai-team)
│   ├── intent.py               # IntentEngine (ai-team)
│   ├── memory.py               # MemoryManager (ai-team)
│   ├── context.py              # context management (ai-team)
│   ├── knowledge.py            # knowledge base (ai-team)
│   ├── reasoning.py            # reasoning engine (ai-team)
│   ├── recommendation.py       # recommendation engine (ai-team)
│   └── protocols.py            # shared protocol data (ai-team)
├── core/
│   ├── __init__.py             # core-team
│   ├── engine.py               # DeltaEngine monolith (core-team)
│   ├── config.py               # DeltaConfig (core-team)
│   ├── tui.py                  # TUI display (core-team)
│   ├── display.py              # display utilities (core-team)
│   ├── session.py              # session management (core-team)
│   ├── database.py             # SQLite persistence (core-team)
│   ├── auth.py                 # auth module (core-team)
│   ├── policy.py               # policy enforcement (core-team)
│   ├── plugin.py               # plugin system (core-team)
├── modules/
│   ├── __init__.py             # modules-team
│   ├── scanner.py, dns.py, encode.py, crypto.py, ssl.py,
│   │   web.py, network.py, report.py, bruteforce.py,
│   │   geoip.py, filesystem.py, git.py, websearch.py,
│   │   analysis.py, skills.py   # modules-team
├── web/
│   ├── __init__.py             # web-team (lazy Flask import)
│   └── chat.py                 # Flask chat UI (web-team)
├── ml/
│   ├── __init__.py             # ml-team
│   ├── engine.py, pipeline.py, classifier.py, anomaly.py
├── utils/
│   ├── __init__.py             # utils-team
│   ├── helpers.py, network.py, router_manager.py, text_utils.py, validators.py
├── skills/                     # skills-team (data-only folders)
├── plugins/                    # plugins-team (plugin registry)
└── config/                     # DELETE in M1 (empty namespace)

tests/                           # qa-team owns test harness
scripts/
│   └── import_audit.py          # M3: import direction scanner
docs/superpowers/specs/
│   └── 2026-08-08-delta-architecture-design.md
```

---

## Milestone 1 — Stabilize (minggu 1–2)

### Task 1: Flask lazy import — make web module optional

**Files:**
- Modify: `delta/web/__init__.py:1-13`
- Modify: `delta/web/chat.py:1-15`
- Test: `tests/test_ai.py` (ensure discovery passes without Flask)

**Interfaces:**
- Consumes: none
- Produces: `delta.web` importable without Flask installed

- [ ] **Step 1: Verify current failure**

```bash
python -m pytest tests/ -v 2>&1 | grep -A5 "ERROR: delta.web"
```
Expected: ImportError on `delta.web` due to missing Flask.

- [ ] **Step 2: Add lazy Flask import in `delta/web/__init__.py`**

Replace eager import with guarded import:

```python
"""Delta web interface module."""
try:
    from delta.web.chat import DeltaChatInterface
    _WEB_AVAILABLE = True
except ImportError:
    DeltaChatInterface = None
    _WEB_AVAILABLE = False

def is_available() -> bool:
    """Check if Flask web UI is available."""
    return _WEB_AVAILABLE
```

- [ ] **Step 3: Add Flask guard in `delta/web/chat.py`**

Wrap Flask imports in try/except at top of file:

```python
try:
    from flask import Flask, render_template_string, request, jsonify, session
    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False

if not _FLASK_AVAILABLE:
    raise ImportError("Flask is required for web UI. Install with: pip install flask")
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/ -v
```
Expected: 127 pass, no ERROR on `delta.web` discovery (import fails gracefully).

- [ ] **Step 5: Commit**

```bash
git add delta/web/__init__.py delta/web/chat.py
git commit -m "fix(web): lazy import Flask to prevent discovery crash"
```

---

### Task 2: Windows TUI cp1252 emoji fallback

**Files:**
- Modify: `delta/core/tui.py:1-50` (encoding detection)
- Modify: `delta/core/display.py` (emoji handling)
- Test: manual verification on Windows cp1252 console

**Interfaces:**
- Consumes: none
- Produces: TUI prints without crashing on cp1252

- [ ] **Step 1: Verify current failure**

```bash
python -c "from delta.core.tui import DeltaTUI; t = DeltaTUI(); t.show_help()" 2>&1
```
Expected: `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f50d'`

- [ ] **Step 2: Add encoding-safe output helper in `delta/core/tui.py`**

Add near top of file (after imports):

```python
import sys
import unicodedata

def _safe_print(text: str) -> None:
    """Print text, falling back to ASCII-safe version on encoding failure."""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_fallback = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        print(ascii_fallback)
```

- [ ] **Step 3: Replace `print()` calls with `_safe_print()` in TUI help output**

Find help banner with emoji (🔍, ⚡, 🛡️, etc.) and wrap with `_safe_print()`.

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/ -v
```
Expected: 127 pass; manual Windows test: no crash.

- [ ] **Step 5: Commit**

```bash
git add delta/core/tui.py
git commit -m "fix(tui): add cp1252-safe print fallback for Windows"
```

---

### Task 3: Delete empty namespaces

**Files:**
- Delete: `delta/knowledge/__init__.py` (if empty/re-export only)
- Delete: `delta/config/__init__.py` (if empty)
- Delete: `delta/templates/__init__.py` (if empty)
- Modify: any file importing from these namespaces

**Interfaces:**
- Consumes: grep for imports
- Produces: no empty namespace directories

- [ ] **Step 1: Audit imports**

```bash
grep -rn "from delta.knowledge\|from delta.config\|from delta.templates\|import delta.knowledge\|import delta.config\|import delta.templates" delta/ tests/
```

- [ ] **Step 2: Update imports if any found**

Replace `from delta.knowledge import X` with `from delta.ai.knowledge import X`.

- [ ] **Step 3: Delete empty directories**

```bash
rmdir delta/knowledge delta/config delta/templates
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/ -v
```
Expected: 127 pass.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove empty namespaces (knowledge, config, templates)"
```

---

## Milestone 2 — Contracts (minggu 3–4)

### Task 4: Add `delta/core/protocols.py`

**Files:**
- Create: `delta/core/protocols.py`
- Test: `tests/test_core.py` (verify protocols importable)

**Interfaces:**
- Consumes: `delta/core/engine.py`, `delta/core/config.py`
- Produces: `EngineProtocol`, `ConfigProtocol` (typing.Protocol)

- [ ] **Step 1: Write failing test**

```python
# tests/test_core.py
def test_core_protocols_exist():
    from delta.core.protocols import EngineProtocol, ConfigProtocol
    assert EngineProtocol is not None
    assert ConfigProtocol is not None
```

- [ ] **Step 2: Run test (expect fail)**

```bash
python -m pytest tests/test_core.py::test_core_protocols_exist -v
```
Expected: ImportError: cannot import from `delta.core.protocols`

- [ ] **Step 3: Create `delta/core/protocols.py`**

```python
"""Protocol contracts for delta.core namespace.

These typing.Protocol classes define the public surface contract
for core components. They are typing-only and do not affect runtime behavior.
"""
from typing import Protocol, runtime_checkable

@runtime_checkable
class EngineProtocol(Protocol):
    """Contract for DeltaEngine-like components."""
    def run(self) -> None: ...
    def execute(self, command: str) -> str: ...

@runtime_checkable
class ConfigProtocol(Protocol):
    """Contract for DeltaConfig-like components."""
    def load(self, config_path: str | None = None) -> None: ...
    def save(self, config_path: str | None = None) -> None: ...
    def get(self, key: str, default = None) -> object: ...
    def set(self, key: str, value: object) -> None: ...
```

- [ ] **Step 4: Run test**

```bash
python -m pytest tests/test_core.py::test_core_protocols_exist -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/core/protocols.py tests/test_core.py
git commit -m "feat(core): add EngineProtocol and ConfigProtocol contracts"
```

---

### Task 5: Add `delta/modules/protocols.py`

**Files:**
- Create: `delta/modules/protocols.py`
- Test: `tests/test_modules.py`

**Interfaces:**
- Consumes: `delta/modules/scanner.py`, `delta/modules/dns.py`
- Produces: `ModuleBase` protocol

- [ ] **Step 1: Write failing test**

```python
# tests/test_modules.py
def test_module_protocol_exists():
    from delta.modules.protocols import ModuleBase
    assert ModuleBase is not None
```

- [ ] **Step 2: Run test (expect fail)**

```bash
python -m pytest tests/test_modules.py::test_module_protocol_exists -v
```

- [ ] **Step 3: Create `delta/modules/protocols.py`**

```python
"""Protocol contract for delta.modules namespace."""
from typing import Protocol, runtime_checkable

@runtime_checkable
class ModuleBase(Protocol):
    """Contract for all command modules."""
    name: str
    description: str

    def execute(self, args: list[str]) -> str: ...
    def validate_args(self, args: list[str]) -> bool: ...
```

- [ ] **Step 4: Run test**

```bash
python -m pytest tests/test_modules.py::test_module_protocol_exists -v
```

- [ ] **Step 5: Commit**

```bash
git add delta/modules/protocols.py tests/test_modules.py
git commit -m "feat(modules): add ModuleBase protocol contract"
```

---

## Milestone 3 — Boundaries (minggu 5–6)

### Task 6: Create import audit script

**Files:**
- Create: `scripts/import_audit.py`
- Test: manual run against codebase

**Interfaces:**
- Consumes: all `delta/` source files
- Produces: violations report (stdout)

- [ ] **Step 1: Create `scripts/import_audit.py`**

```python
#!/usr/bin/env python3
"""Scan delta/ imports and enforce dependency direction rules."""
import ast
import sys
from pathlib import Path

RULES = {
    "delta.core": [],  # core can only import stdlib
    "delta.ai": ["delta.core"],  # ai can import core only
    "delta.modules": ["delta.utils", "delta.core"],  # modules can import utils + core
    "delta.web": ["delta.modules", "delta.utils", "delta.core"],  # web can import modules/utils/core
    "delta.ml": ["delta.ai", "delta.core", "delta.utils"],  # ml can import ai/core/utils
    "delta.utils": [],  # utils stdlib only
    "delta.skills": [],  # skills stdlib only
    "delta.plugins": [],  # plugins stdlib only
}

VIOLATIONS = []

for pyfile in Path("delta").rglob("*.py"):
    if pyfile.name == "__init__.py" and pyfile.parent == Path("delta"):
        continue
    tree = ast.parse(pyfile.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("delta."):
                source_ns = ".".join(pyfile.parts[:2])
                target_ns = node.module.split(".")[:2]
                target_ns = ".".join(target_ns)
                allowed = RULES.get(source_ns, [])
                if target_ns not in allowed and target_ns != source_ns:
                    VIOLATIONS.append(
                        f"VIOLATION: {pyfile} imports {node.module} "
                        f"(allowed: {allowed or 'stdlib only'})"
                    )

if VIOLATIONS:
    print("\n".join(VIOLATIONS))
    sys.exit(1)
else:
    print("OK: all imports follow dependency rules")
    sys.exit(0)
```

- [ ] **Step 2: Run against codebase**

```bash
python scripts/import_audit.py
```
Expected: violations reported (or OK if clean).

- [ ] **Step 3: Commit**

```bash
git add scripts/import_audit.py
git commit -m "feat(ci): add import direction audit script"
```

---

### Task 7: Fix import violations found by audit

**Files:**
- Modify: files flagged by audit script
- Test: `python scripts/import_audit.py` exits 0

**Interfaces:**
- Consumes: audit report from Task 6
- Produces: zero violations

- [ ] **Step 1: Run audit, collect violations**

```bash
python scripts/import_audit.py 2>&1
```

- [ ] **Step 2: Fix each violation**

For each violation:
- If `core/` imports from `ai/` or `modules/`: move import to method-level or use protocol.
- If `modules/` imports from `ai/`: extract to interface or callback.
- If `__init__.py` has cross-namespace imports: reduce to essential only.

- [ ] **Step 3: Verify**

```bash
python scripts/import_audit.py && python -m pytest tests/ -v
```
Expected: exit 0, 127 pass.

- [ ] **Step 4: Commit per fix (or batch if small)**

```bash
git add -A
git commit -m "fix(deps): resolve import direction violations"
```

---

## Milestone 4 — Ownership (minggu 7–8)

### Task 8: Add owner docstrings to `__init__.py`

**Files:**
- Modify: every `delta/*/__init__.py`
- Test: grep for `@owner` tag

**Interfaces:**
- Consumes: none
- Produces: owner metadata in each namespace

- [ ] **Step 1: Template for owner docstring**

```python
"""Delta [namespace] package.

@owner: @[team]-team
@dependencies: [list]
@description: [one line]
"""
```

- [ ] **Step 2: Update all `__init__.py` files**

Apply template to:
- `delta/__init__.py` → @core-team
- `delta/ai/__init__.py` → @ai-team
- `delta/core/__init__.py` → @core-team
- `delta/modules/__init__.py` → @modules-team
- `delta/web/__init__.py` → @web-team
- `delta/ml/__init__.py` → @ml-team
- `delta/utils/__init__.py` → @utils-team
- `delta/skills/__init__.py` → @skills-team
- `delta/plugins/__init__.py` → @plugins-team

- [ ] **Step 3: Verify**

```bash
grep -rn "@owner:" delta/*/__init__.py
```
Expected: 9 matches.

- [ ] **Step 4: Commit**

```bash
git add delta/*/__init__.py
git commit -m "chore: add owner docstrings to namespace __init__.py files"
```

---

## Milestone 5 — YAGNI trim (minggu 9+)

### Task 9: Delete unused namespaces and files

**Files:**
- Delete: `delta/knowledge/` (if not already deleted in M1)
- Delete: `delta/config/` (if not already deleted in M1)
- Delete: `delta/templates/` (if not already deleted in M1)
- Delete: `delta/utils/router_manager.py` (if unused)
- Delete: `check_llm.py`, `update_kilo.py`, `delta/ai/llm.py.bak` (scratch files)

**Interfaces:**
- Consumes: grep for usage
- Produces: clean namespace

- [ ] **Step 1: Audit usage**

```bash
grep -rn "router_manager\|delta.knowledge\|delta.config\|delta.templates" delta/ tests/
```

- [ ] **Step 2: Delete confirmed unused**

```bash
rm -f delta/utils/router_manager.py
rm -f check_llm.py update_kilo.py delta/ai/llm.py.bak
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/ -v
```
Expected: 127 pass (or fewer if tests for deleted modules existed).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: YAGNI trim unused files and scratch scripts"
```

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-08-08-delta-architecture-design.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
