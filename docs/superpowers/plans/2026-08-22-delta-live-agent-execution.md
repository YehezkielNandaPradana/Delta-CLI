# Delta Live Agent Execution & Thinking UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement real-time, non-empty live execution streaming in Delta Web UI with state machine tracking, terminal braille spinners, timeline nodes, auto-scrolling, and live Inspector status updates.

**Architecture:** Enhance backend `event_bus` emissions in `delta/core/engine.py` & `delta/ai/tools.py` for immediate start/thinking/tool/completion events. Enhance frontend `delta/web/index.html` and `delta/web/static/index.html` to generate immediate UI placeholder elements on prompt submit and stream live state transitions & timeline nodes via SSE (`/api/events`).

**Tech Stack:** Python 3.11, HTTP/SSE, HTML5, JavaScript (ES6+), Tailwind CSS, Pytest.

**Spec:** `docs/superpowers/specs/2026-08-22-delta-live-agent-execution-design.md`

## Global Constraints
- Minimal terminal-native design (Claude Code / Cursor style). No AI slop or fake progress bars.
- Live streaming state machine transitions (`idle`, `thinking`, `planning`, `executing`, `tool_running`, `completed`, `error`).
- Zero blank execution area upon user submit.
- Full test coverage across backend event emissions and web server handling.

---

### Task 1: Enhance Backend Real-Time Event Emission System

**Files:**
- Modify: `delta/core/engine.py:1140-1350`
- Modify: `delta/ai/tools.py:115-180`
- Test: `tests/test_agent_events.py`

**Interfaces:**
- Consumes: `event_bus.emit(AgentEvent(...))`
- Produces: Structured `agent_start`, `agent_thinking`, `agent_status`, `tool_start`, `tool_result`, `agent_complete` events with execution metadata.

- [ ] **Step 1: Write tests for engine event emission**

```python
def test_engine_emits_immediate_events(monkeypatch):
    from delta.ai.events import event_bus, EventType
    events = []
    def listener(ev):
        events.append(ev.type)
    sub = event_bus.subscribe(listener)
    try:
        # verify event_bus captures agent_start and agent_thinking
        event_bus.emit_agent_start("task-1", "Thinking...")
        assert EventType.AGENT_START in events
    finally:
        sub()
```

- [ ] **Step 2: Run pytest to verify test passes/fails as expected**

Run: `pytest tests/test_agent_events.py -v`

- [ ] **Step 3: Update `delta/core/engine.py` & `delta/ai/tools.py` to emit immediate start & tool events**

Modify `delta/core/engine.py` inside `_process_input` or `_process_with_llm` so that every query (task or standard prompt) emits `AGENT_START` and `AGENT_THINKING` immediately.

- [ ] **Step 4: Run pytest to verify implementation**

Run: `pytest tests/test_agent_events.py -v`

- [ ] **Step 5: Commit changes**

```bash
git add delta/core/engine.py delta/ai/tools.py tests/test_agent_events.py
git commit -m "feat(events): emit immediate agent_start and thinking events for all requests"
```

---

### Task 2: Implement Frontend Immediate Placeholder & State Machine Rendering

**Files:**
- Modify: `delta/web/index.html:840-1020,1350-1400`
- Modify: `delta/web/static/index.html:740-800,1370-1420`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: SSE `/api/events` payload stream and `handleSubmit(e)`
- Produces: Non-empty live execution canvas, terminal braille spinner, execution state badge, human-readable tool nodes, auto-scroll with `↓ New activity` pill button, and live Inspector updates.

- [ ] **Step 1: Write frontend unit test checking HTML script contents**

Ensure `handleSubmit` initializes `getOrCreateExecutionTimeline` immediately with initial thinking state.

- [ ] **Step 2: Run pytest**

Run: `pytest tests/test_web_frontend.py -v`

- [ ] **Step 3: Update `delta/web/index.html` & `delta/web/static/index.html`**

1. In `handleSubmit(e)`:
   - Call `restoreExecutionCanvas()` if not active.
   - Immediately create timeline execution box and append initial thinking node (`⠋ Thinking...`) before `fetch('/api/execute')` completes.
2. In `handleAgentEvent(event)`:
   - Implement terminal braille spinner interval (`⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`).
   - Map state machine badges (`IDLE`, `THINKING`, `PLANNING`, `EXECUTING`, `COMPLETED`, `ERROR`).
   - Human-readable tool nodes without raw JSON.
3. Auto-scroll lock detector:
   - Detect user manual scroll up (>50px from bottom).
   - Display `↓ New activity` button when new events arrive while scrolled up.
   - Clicking resumes auto-scroll.
4. Live Inspector sync:
   - Update `Status`, `Current Tool`, `Commands Executed` in right Inspector panel.

- [ ] **Step 4: Run pytest to verify web tests pass**

Run: `pytest tests/test_web_frontend.py tests/test_web_server.py -v`

- [ ] **Step 5: Commit changes**

```bash
git add delta/web/index.html delta/web/static/index.html tests/test_web_frontend.py
git commit -m "feat(web): add live agent execution timeline, state machine, and auto-scroll"
```
