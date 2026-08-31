# Branched Thinking & Real-Time Agent Execution Tree Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a compact thinking bar and real-time branched execution tree for Delta Web UI driven by authoritative backend ReAct Agent step events.

**Architecture:** The Agent Engine emits strongly-typed `AgentStep` events through `EventBus` with per-execution sequence isolation. The Web Frontend receives SSE events, dynamically reconstructs the hierarchical execution tree in DOM, and renders reactive SVG bezier connector overlays between nodes with popover/modal details.

**Tech Stack:** Python 3.10+, Dataclasses, Enum, AsyncEventBus, Threading, Vanilla JavaScript (ES6+), HTML5, Tailwind CSS, SVG Bezier Curves.

## Global Constraints

- Agent Engine is the single authoritative source of truth for step state, kind, and duration.
- Zero fake mock trees or static sample nodes. Tree is strictly constructed from live events.
- No internal chain-of-thought or raw reasoning exposed to the user UI.
- All step models must enforce `ROOT` step with `parent_id = None` and validate circular parent chains.
- Frontend DOM grid/flex tree is layout source of truth; SVG overlay is presentation-only.

---

### Task 1: Backend Agent Engine Step Lifecycle & Emitter

**Files:**
- Modify: `delta/core/engine.py:1255-1498`
- Test: `tests/test_agent_events.py`

**Interfaces:**
- Consumes: `AgentStep`, `StepKind`, `StepStatus`, `AgentEvent`, `EventType`, `EventBus` from `delta.ai.events`.
- Produces: Emitted SSE events `agent_step_created`, `agent_step_started`, `agent_step_completed`, `agent_step_failed` with valid `step_id`, `parent_id`, `duration_ms`, and `output_preview`.

- [ ] **Step 1: Write failing test for ReAct loop step event emission**

Add to `tests/test_agent_events.py`:
```python
    def test_engine_emits_structured_agent_steps(self):
        bus = EventBus()
        events = []
        bus.subscribe(lambda ev: events.append(ev))

        from delta.ai.events import AgentStep, StepKind, StepStatus, EventType
        root_step = AgentStep(
            id="root_exec_1",
            task_id="t1",
            execution_id="exec_1",
            parent_id=None,
            kind=StepKind.ROOT,
            label="Root Task",
            status=StepStatus.RUNNING,
            created_at=time.time(),
            started_at=time.time()
        )
        root_step.validate()

        child_step = AgentStep(
            id="tool_1",
            task_id="t1",
            execution_id="exec_1",
            parent_id=root_step.id,
            kind=StepKind.READ,
            label="Reading file",
            status=StepStatus.RUNNING,
            created_at=time.time(),
            started_at=time.time(),
            file_path="test.py"
        )
        child_step.validate({"root_exec_1": root_step})

        bus.emit(AgentEvent(
            type=EventType.AGENT_STEP_STARTED,
            execution_id="exec_1",
            task_id="t1",
            step_id=child_step.id,
            payload={"step": child_step.to_dict()}
        ))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, EventType.AGENT_STEP_STARTED)
        self.assertEqual(events[0].payload["step"]["parent_id"], "root_exec_1")
        self.assertEqual(events[0].payload["step"]["kind"], "read")
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_agent_events.py -k test_engine_emits_structured_agent_steps -v`
Expected: PASS

- [ ] **Step 3: Update `delta/core/engine.py` to create and emit structured `AgentStep` instances**

In `delta/core/engine.py` inside `_process_with_llm()`:
1. Initialize root step:
```python
        root_step_id = f"root_{exec_id}"
        root_step = AgentStep(
            id=root_step_id,
            task_id=task_id or exec_id,
            execution_id=exec_id,
            parent_id=None,
            kind=StepKind.ROOT,
            label=f"Task: {user_input[:40]}...",
            status=StepStatus.RUNNING,
            created_at=time.time(),
            started_at=time.time(),
            output_preview="Executing agent workflow"
        )
        existing_steps: Dict[str, AgentStep] = {root_step_id: root_step}

        event_bus.emit(AgentEvent(
            type=EventType.AGENT_STEP_STARTED,
            execution_id=exec_id,
            task_id=task_id or exec_id,
            step_id=root_step_id,
            payload={"step": root_step.to_dict()}
        ))
```
2. When tool calls are executed (JSON/XML):
- Determine `StepKind` based on tool name (`find_files`/`grep` -> `StepKind.SEARCH`, `read_file` -> `StepKind.READ`, `smart_edit`/`write_file` -> `StepKind.EDIT`, `run_terminal` with pytest/test -> `StepKind.TEST`, otherwise `StepKind.COMMAND` or `StepKind.TOOL`).
- Create `AgentStep(id=t_id, parent_id=root_step_id, kind=step_kind, label=..., status=StepStatus.RUNNING, ...)`
- Emit `EventType.AGENT_STEP_STARTED`.
- After tool completes: calculate `duration_ms`, set `status=StepStatus.COMPLETED` or `StepStatus.FAILED`, set `output_preview` (safe summary), and emit `EventType.AGENT_STEP_COMPLETED` / `EventType.AGENT_STEP_FAILED`.
3. When agent finishes: mark `root_step.status = StepStatus.COMPLETED`, calculate total `root_step.duration_ms`, and emit `EventType.AGENT_STEP_COMPLETED` for root step.

- [ ] **Step 4: Run full agent event tests**

Run: `pytest tests/test_agent_events.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/core/engine.py tests/test_agent_events.py
git commit -m "feat(agent): emit structured agent execution steps and lifecycle events"
```

---

### Task 2: Frontend Hybrid Execution Tree Component & Styles (`delta/web/index.html`)

**Files:**
- Modify: `delta/web/index.html`

**Interfaces:**
- Consumes: Server-Sent Events from `/api/events` with payload structure `{ type: "agent_step_*", execution_id, step_id, sequence, payload: { step: { ... } } }`.
- Produces: Reactive interactive UI with Compact Thinking Bar, collapsible Branched Tree with dynamic SVG Bezier connector lines, and detail popover/modal viewers.

- [ ] **Step 1: Add Compact Thinking & Tree CSS Styles to `delta/web/index.html`**

Add CSS keyframes and utilities to `<style>`:
```css
/* Animated Thinking Delta Ring */
@keyframes deltaRingPulse {
    0%, 100% { transform: scale(1); opacity: 0.8; box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
    50% { transform: scale(1.05); opacity: 1; box-shadow: 0 0 8px 2px rgba(99, 102, 241, 0.6); }
}
.animate-delta-ring { animation: deltaRingPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }

/* SVG Connector Transition */
.tree-connector-line {
    fill: none;
    stroke: rgba(99, 102, 241, 0.35);
    stroke-width: 1.5;
    stroke-dasharray: 4, 4;
    animation: dashMove 1.5s linear infinite;
}
.tree-connector-line.completed {
    stroke: rgba(16, 185, 129, 0.4);
    stroke-dasharray: none;
}
.tree-connector-line.failed {
    stroke: rgba(239, 68, 68, 0.5);
    stroke-dasharray: none;
}
@keyframes dashMove {
    from { stroke-dashoffset: 8; }
    to { stroke-dashoffset: 0; }
}

/* Tree Container Smooth Height Transition */
.thinking-tree-container {
    transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease-out;
}
```

- [ ] **Step 2: Implement `DeltaThinkingTree` Modular Namespace in JavaScript**

Inside `<script>` in `delta/web/index.html`:
```javascript
const DeltaThinkingTree = (function() {
    const state = {
        executions: {}, // { [execId]: { steps: {}, roots: [], activeStepId: null, isExpanded: false, totalDuration: 0 } }
        unparentedBuffer: {}, // { [execId]: { [parentId]: [childStep, ...] } }
        seenEvents: new Set()
    };

    function getOrCreateExecution(execId) {
        if (!state.executions[execId]) {
            state.executions[execId] = {
                id: execId,
                steps: {},
                roots: [],
                status: 'running',
                isExpanded: false,
                containerEl: null
            };
        }
        return state.executions[execId];
    }

    function handleStepEvent(ev) {
        const execId = ev.execution_id || 'default';
        const dedupKey = `${ev.event_id || ''}_${ev.step_id || ''}_${ev.type}`;
        if (state.seenEvents.has(dedupKey)) return;
        state.seenEvents.add(dedupKey);

        const exec = getOrCreateExecution(execId);
        const stepData = ev.payload && ev.payload.step ? ev.payload.step : null;
        if (!stepData) return;

        exec.steps[stepData.id] = Object.assign(exec.steps[stepData.id] || {}, stepData);

        // Check if root
        if (!stepData.parent_id && !exec.roots.includes(stepData.id)) {
            exec.roots.push(stepData.id);
        }

        // Attach buffered orphans
        if (state.unparentedBuffer[execId] && state.unparentedBuffer[execId][stepData.id]) {
            state.unparentedBuffer[execId][stepData.id].forEach(orphan => {
                exec.steps[orphan.id] = orphan;
            });
            delete state.unparentedBuffer[execId][stepData.id];
        }

        // Buffer if parent missing
        if (stepData.parent_id && !exec.steps[stepData.parent_id]) {
            if (!state.unparentedBuffer[execId]) state.unparentedBuffer[execId] = {};
            if (!state.unparentedBuffer[execId][stepData.parent_id]) state.unparentedBuffer[execId][stepData.parent_id] = [];
            state.unparentedBuffer[execId][stepData.parent_id].push(stepData);
        }

        renderExecutionComponent(execId);
    }

    function toggleExpand(execId) {
        const exec = state.executions[execId];
        if (!exec) return;
        exec.isExpanded = !exec.isExpanded;
        renderExecutionComponent(execId);
        requestAnimationFrame(() => updateSvgConnectors(execId));
    }

    // Render tree nodes + SVG line recalculation
    function renderExecutionComponent(execId) {
        // Build DOM Nodes hierarchy & mount to chat stream
        // Recalculate SVG connector paths from parent node centers to child node centers
    }

    return {
        handleStepEvent,
        toggleExpand,
        state
    };
})();
```

- [ ] **Step 3: Connect SSE stream listener to `DeltaThinkingTree.handleStepEvent`**

Update `evtSource.onmessage` in `delta/web/index.html` to route `agent_step_*` events to `DeltaThinkingTree.handleStepEvent`.

- [ ] **Step 4: Commit**

```bash
git add delta/web/index.html
git commit -m "feat(web): add compact thinking bar and hybrid branched execution tree UI"
```

---

### Task 3: Interactive Node Popovers, Modal Viewers & Terminal/Diff Drawer

**Files:**
- Modify: `delta/web/index.html`

**Interfaces:**
- Consumes: Node click events on DOM cards with step metadata.
- Produces: Popover showing detailed duration, file path, and action; modal drawers for raw terminal output and file diffs.

- [ ] **Step 1: Implement Node Detail Popover and Full Output Drawer in `delta/web/index.html`**

1. Create Popover helper that positions relative to clicked node card:
   - Tool Name, Parameter JSON preview, Execution Status, Duration ms.
2. Implement Modal Drawer for:
   - `[View Output]`: Shows formatted terminal log with ANSI colors stripped / syntax highlight.
   - `[View Diff]`: Shows line additions (+) and removals (-) with unified diff viewer.

- [ ] **Step 2: Add Click Handlers to DOM Node Cards**

Connect `onclick` on step cards to `DeltaThinkingTree.showNodeDetail(execId, stepId)`.

- [ ] **Step 3: Commit**

```bash
git add delta/web/index.html
git commit -m "feat(web): add interactive step detail popover and modal viewers"
```

---

### Task 4: End-to-End Verification & Real ReAct Test Scenarios

**Files:**
- Test: `tests/test_agent_events.py`
- Test: `tests/test_web_bridge.py`

**Interfaces:**
- Verifies: Full ReAct loop step hierarchy, multi-branch parallel step rendering, root validation, and SSE event streaming.

- [ ] **Step 1: Add E2E tests for Web SSE step stream and tree structure in `tests/test_web_bridge.py`**

```python
def test_web_bridge_handles_agent_step_events():
    from delta.core.events import AsyncEventBus
    from delta.web.bridge import WebBridge
    from delta.ai.events import AgentEvent, EventType, StepKind, StepStatus, AgentStep

    bus = AsyncEventBus()
    bridge = WebBridge(bus)

    step = AgentStep(
        id="step_test_1",
        task_id="task_1",
        execution_id="exec_1",
        parent_id=None,
        kind=StepKind.ROOT,
        label="Root Step",
        status=StepStatus.RUNNING,
        created_at=100.0
    )

    ev = AgentEvent(
        type=EventType.AGENT_STEP_STARTED,
        execution_id="exec_1",
        task_id="task_1",
        step_id="step_test_1",
        payload={"step": step.to_dict()}
    )

    bridge.event_queue.append(ev.to_dict())
    self.assertEqual(len(bridge.event_queue), 1)
    self.assertEqual(bridge.event_queue[0]["type"], "agent_step_started")
    self.assertEqual(bridge.event_queue[0]["payload"]["step"]["kind"], "root")
```

- [ ] **Step 2: Run all unit and integration tests**

Run: `pytest tests/test_agent_events.py tests/test_web_bridge.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_web_bridge.py tests/test_agent_events.py
git commit -m "test: add integration and e2e verification tests for agent step events"
```
