# Spec: Delta Branched Thinking & Real-Time Agent Execution Tree

## 1. Context & Objectives

Delta AI Coding Agent memerlukan indikator status eksekusi real-time yang compact dan transparan bagi pengguna tanpa mengotori ruang percakapan dengan log mentah atau *chain-of-thought* internal model.

Desain ini menetapkan komponen **Compact Thinking Bar** yang dapat di-expand menjadi **Branched Execution Tree**. visualisasi ini mencerminkan struktur *step-by-step* eksekusi ReAct/Tool Agent yang sebenarnya secara real-time.

---

## 2. Architecture Boundaries & Data Flow

```
┌──────────────────────┐
│  ReAct Agent Engine  │ ── (Authoritative Source of Truth for AgentStep & Lifecycle)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     EventBus         │ ── (Structured Event Distribution, Execution Sequence Isolation)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  SSE Web Transport   │ ── (Transport Layer Only, Stream JSON Events)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Frontend (Web UI)   │ ── (Reconstruct Tree, DOM Grid Layout, SVG Connector Overlay)
└──────────────────────┘
```

- **Agent Engine:** Authoritative source of truth untuk `AgentStep`, lifecycle, duration, error, dan operational status.
- **EventBus:** Meneruskan `AgentEvent` terstruktur dengan penomoran `sequence` yang diisolasi per `execution_id`.
- **SSE Transport:** Murni sebagai transport layer (`/api/events`), tidak mengubah payload atau state.
- **Frontend (Web UI):** Menerima event, merekonstruksi tree secara lokal berdasarkan `parent_id`, serta mengelola state visual `collapsed` / `expanded`. Frontend TIDAK BOLEH menjadi authoritative source untuk status `AgentStep`.
- **SVG Connector:** Presentation-only overlay, tidak menyimpan business state.
- **Payload & Data Efficiency:** Heavy tool output (raw terminal log, full file diff) menggunakan `output_preview` ringkas di tree node, dengan *lazy loading* detail penuh saat node diklik.

---

## 3. Data Model & Event Contracts (`delta/ai/events.py`)

### 3.1 Step Kind & Step Status Enums

```python
class StepKind(str, Enum):
    ROOT = "root"
    UNDERSTAND = "understand"
    CONTEXT = "context"
    SEARCH = "search"
    READ = "read"
    ANALYZE = "analyze"
    PLAN = "plan"
    TOOL = "tool"
    COMMAND = "command"
    EDIT = "edit"
    CREATE = "create"
    DELETE = "delete"
    TEST = "test"
    VERIFY = "verify"
    RESULT = "result"

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### 3.2 AgentStep Dataclass

```python
@dataclass
class AgentStep:
    id: str
    task_id: str
    execution_id: str
    parent_id: Optional[str]
    kind: StepKind
    label: str
    status: StepStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    tool_name: Optional[str] = None
    file_path: Optional[str] = None
    command: Optional[str] = None
    diff_stats: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    output_preview: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, existing_steps: Optional[Dict[str, "AgentStep"]] = None) -> None:
        """Validate ROOT constraints and circular parent chain dependencies."""
        if self.kind == StepKind.ROOT or self.kind == "root":
            if self.parent_id is not None:
                raise ValueError(f"Root step {self.id} must have parent_id=None")
        if self.parent_id and self.parent_id == self.id:
            raise ValueError(f"Self-parent circular dependency detected: step {self.id} cannot be its own parent")
        if self.parent_id and existing_steps:
            visited = {self.id}
            curr_parent_id: Optional[str] = self.parent_id
            while curr_parent_id:
                if curr_parent_id in visited:
                    raise ValueError(f"Circular parent chain detected involving step {curr_parent_id}")
                visited.add(curr_parent_id)
                parent_step = existing_steps.get(curr_parent_id)
                curr_parent_id = parent_step.parent_id if parent_step else None
```

### 3.3 Event Sequence & Isolation (`EventBus`)
- Setiap `AgentEvent` yang di-emit melalui `EventBus` memiliki field `sequence` yang dihitung secara terpisah per `execution_id` (`self._sequences[exec_id]`).
- Event deduplication pada Client dilakukan dengan kombinasi `event_id` + `step_id`.

---

## 4. UI Specification (Compact Thinking & Hybrid Execution Tree)

### 4.1 Compact Thinking Bar
- **Collapsed State:** `[animated Delta icon] Thinking..... >`
- **Completed State:** `✓ Completed · 8 steps · 4.2s >`
- **Failed State:** `× Failed · 5 steps · 2.1s >`
- **Transitions:** Smooth height/opacity CSS transitions tanpa layout shift kasar.

### 4.2 Hybrid DOM/SVG Execution Tree
- **DOM Hierarchy (Source of Truth for Layout):** Node dirender sebagai CSS grid/flex tree bertingkat.
- **SVG Line Overlay:** `<svg>` overlay digambar di atas container DOM untuk menghubungkan koordinat Parent Node ke Child Node (`ResizeObserver` auto-update).
- **Parallel Branches:** Child nodes yang berbagi `parent_id` sama dan berstatus `running` akan tampil secara berdampingan.
- **Orphan Handling:** Child step yang datang sebelum parent node akan disimpan di buffer sementara dan disambungkan saat parent node dirender.
- **Node Selection & Detail Popover:**
  - Klik node membuka popover ringan (Tool, Path, Duration, Args).
  - Untuk log terminal atau file diff besar, tombol `[View Output]` / `[View Diff]` membuka Modal/Drawer khusus.

---

## 5. File & Component Organization

### Frontend Structure (`delta/web/index.html`)
Karena frontend Delta saat ini berbasis single-file HTML, komponen JavaScript dipisahkan secara modular melalui IIFE/Namespace:
- `DeltaThinkingTree.Core` — Tree Data Store, Parent-Child Mapping, Orphan Buffer, Sequence Deduplication.
- `DeltaThinkingTree.DOMRenderer` — Layout Generator, Node Cards, Status Badges.
- `DeltaThinkingTree.SVGOverlay` — Bezier Connector Path Drawer & ResizeObserver Sync.
- `DeltaThinkingTree.DetailViewer` — Popover detail, Log Modal, Diff Viewer.

### Backend Updates
- `delta/ai/events.py` — Dataclass `AgentStep`, `StepKind`, `StepStatus`, `EventBus` sequence per execution.
- `delta/core/engine.py` — Integrasi penciptaan `AgentStep` & emisi event `agent_step_*` pada ReAct loop & tool execution.
- `delta/web/server.py` — Verifikasi SSE streaming format.

---

## 6. Verification & Test Strategy

1. **Unit Tests (`tests/test_agent_events.py`):**
   - Self-parent rejection (`validate()`).
   - Circular parent chain rejection (`A -> B -> C -> A`).
   - Root step validation (`parent_id == None`).
   - Execution sequence isolation (`exec_1` vs `exec_2`).
2. **Web Server Tests (`tests/test_web_server.py`):**
   - SSE format streaming & event structure verification.
3. **End-to-End Test (`tests/test_e2e_refactor.py`):**
   - Simulasi eksekusi ReAct Agent dengan multi-step tools & verifikasi tree structure.
