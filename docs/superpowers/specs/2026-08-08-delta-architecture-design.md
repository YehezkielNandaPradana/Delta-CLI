# Delta CLI Architecture Design
Date: 2026-08-08
Status: Proposed — awaiting user review

## Context

Delta CLI adalah Python CLI murni (no framework) dengan 13 namespace di bawah `delta/`,
127 unit test passing (ketika Flask diabaikan), dan dua bug pre-existing:
- `delta.web` gagal import tanpa Flask (`ModuleNotFoundError`)
- TUI crash di Windows cp1252 saat mencetak emoji

Default runtime yang dijamin preserve:
- Provider: `9router`
- Base URL: `http://localhost:20128/v1`
- Model: `KiloCombo`

## Decision

**Pilih Approach A (Namespace Ownership) + milestone stabilisasi dulu.**

Tolak B (capability-first) karena redundant dengan A dan tidak eksplisit preserve defaults.
Tolak C (feature branches) karena engine.py 4924 baris monolith menyebabkan merge hell.

## 1. Ownership — 9 area non-overlap

| Owner | Namespace | Tanggung jawab | Dependensi |
|---|---|---|---|
| @core-team | `delta/core/` | engine, tui, config, session, database, display, plugin, policy, auth | stdlib only |
| @ai-team | `delta/ai/` + `delta/ai/protocols.py` | LLMEngine, IntentEngine, Memory, context, knowledge, reasoning, recommendation, presets | stdlib + `core/config` (protocol-only) |
| @modules-team | `delta/modules/` | 16 command modules (scanner, dns, encode, crypto, ssl, web, dll) | stdlib + `utils/` |
| @web-team | `delta/web/` | Flask web UI (opsional, lazy import) | stdlib + lazy Flask |
| @ml-team | `delta/ml/` | pipeline, engine, classifier, anomaly | stdlib + `ai/` (jika LLM needed) |
| @utils-team | `delta/utils/` | helpers, validators, text_utils, network, router_manager | stdlib only |
| @skills-team | `delta/skills/` | skill store (data-only folders + manager) | stdlib only |
| @plugins-team | `delta/plugins/` | plugin registry | stdlib only |
| @qa-team | `tests/` + `delta/__init__.py` | test harness, CI gates, minimal re-export | — |

## 2. Dependency direction (target)

```
delta/core/   → stdlib only
delta/ai/     → stdlib + core/config (protocol-only; tidak import modules/web)
delta/modules/ → stdlib + utils/ (tidak import ai/web)
delta/web/    → stdlib + lazy Flask (opsional)
delta/ml/     → stdlib + ai/
delta/utils/  → stdlib only
delta/skills/ → stdlib only
delta/plugins/→ stdlib only
```

## 3. Current state vs target

| Item | Current | Target |
|---|---|---|
| Circular import config→llm | HILANG (config.py zero refs; llm.py imports protocols.py) | ✅ preserved |
| Flask optional | eager import di `web/__init__.py:10` | lazy import + graceful fallback |
| Windows cp1252 emoji | crash di TUI | detect + fallback ASCII |
| `delta/knowledge/` | re-export only | hapus, ganti import ke `delta.ai.knowledge` |
| `delta/config/` | docstring only | hapus entirely |
| `delta/templates/` | docstring only | hapus entirely |
| Engine god object | 4924 baris, tetap | refactor hanya jika coverage >80% atau contributor >3 |
| Import audit CI | belum ada | script stdlib `ast` scan |

## 4. Milestone

### M1 — Stabilize (minggu 1–2)
Pekerjaan: perbaiki sisa defect sebelum ownership aktif.

1. Flask lazy import — `delta/web/__init__.py` dan `delta/web/chat.py` guard import Flask; jika missing, expose stub message, bukan crash.
2. Windows TUI cp1252 — detect `sys.stdout.encoding`; fallback ke ASCII art/strip emoji sebelum print. Jangan ubah personality system prompt, hanya sanitize output.
3. Hapus namespace kosong — `delta/knowledge/`, `delta/config/`, `delta/templates/` (jika confirmed empty).
4. Dokumentasikan defaults — pastikan `config._migrate_to_9router()` eksplisit 9Router + KiloCombo locked.

**Safe parallel:** Flask-fix ‖ TUI-fix ‖ namespace-cleanup (file berbeda).

**Acceptance gate:** 127 tests tetap passing; `delta.web` import tanpa Flask tidak crash discovery.

### M2 — Contracts (minggu 3–4)
Pekerjaan: tambah `typing.Protocol` minimal per namespace sebagai public surface contract.

1. `delta/ai/protocols.py` — sudah ada, tinjau kelengkapan.
2. `delta/core/protocols.py` — `EngineProtocol`, `ConfigProtocol`.
3. `delta/modules/protocols.py` — `ModuleBase` protocol.

**Tidak ubah behavior** — hanya typing contract. Engine tetap god-object.

**Safe parallel:** protocols per namespace — 3 file terpisah, zero overlap.

**Acceptance gate:** `mypy --strict` (atau `pyright`) passes tanpa error baru.

### M3 — Boundaries (minggu 5–6)
Pekerjaan: enforce dependency direction via import audit script.

1. Script CI (`scripts/import_audit.py`) scan semua `from delta.` import, validasi aturan.
2. Fix violations yang ditemukan (config→ai sudah hilang; sisanya audit).
3. `delta/__init__.py` — kurangi cross-namespace re-export ke essential only.

**SEQUENTIAL** — audit dulu, baru fix satu per satu (dependencies saling terkait).

**Acceptance gate:** import audit script green; zero violation.

### M4 — Ownership (minggu 7–8)
Pekerjaan: assign owner per namespace via CODEOWNERS-style convention.

1. Docstring owner di setiap `__init__.py` namespace.
2. CI gate: PR harus sesuai namespace owner.
3. Migrasi proof-of-concept `delta/modules/skills.py` → `delta/skills/manager.py` (jika belum).

**Safe parallel:** docstring per namespace independent.

**Acceptance gate:** setiap `__init__.py` punya `@owner` tag.

### M5 — YAGNI trim (minggu 9+)
Pekerjaan: eval dan hapus yang tidak dipakai.

1. `delta/knowledge/` — hapus jika confirmed empty.
2. `delta/config/` — hapus jika confirmed empty.
3. `delta/templates/` — hapus jika confirmed empty.
4. `delta/utils/router_manager.py` — eval apakah masih dipakai; hapus jika tidak.

**Safe parallel:** evaluasi per item independent.

**Acceptance gate:** zero unused namespace; `delta/__init__.py` minimal.

## 5. Risiko dan mitigasi

| Risiko | Prob | Impact | Mitigasi |
|---|---|---|---|
| Circular import meledak saat tambah contracts | rendah | tinggi | protocols.py data-only; config→protocols sudah aman |
| Merge conflict di engine.py | tinggi | sedang | M1-M4 stabilkan dulu; engine tetap god-object |
| LLMEngine race condition (stateful + concurrent) | sedang | sedang | YAGNI; refactor hanya jika contributor >3 |
| MemoryManager JSON tanpa lock | rendah | rendah | Jangan paralel session write (documented ceiling) |
| Flask optional crash | tinggi | rendah | M1 fix lazy import |

## 6. Out of scope (YAGNI)

- DI framework (manual wiring cukup)
- ABC hierarchy (Protocol cukup)
- Event system
- DeltaEngine command registry refactor (trigger: coverage >80% atau contributor >3)
- Structured logging (bisa ditinjau di M5 jika butuh observability)

## 7. Spec self-review

- [x] No placeholders
- [x] No contradictions — dependency direction konsisten; M1–M5 sequential logic valid
- [x] Scope: 5 milestone, masing-masing bounded
- [x] No ambiguity — ownership, gates, dan deliverables eksplisit
- [x] Behavior preservation: 9Router/KiloCombo defaults dijamin via existing `_migrate_to_9router()`
