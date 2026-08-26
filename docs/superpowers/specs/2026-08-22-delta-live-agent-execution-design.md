# Spec: Delta Live Agent Execution & Thinking UI

**Date:** 2026-08-22
**Status:** Approved

## Executive Summary
This document specifies the real-time execution state machine and live event streaming UI for Delta Web UI. It eliminates empty/blank execution states during agent execution, providing live feedback for reasoning (`thinking`), planning (`planning`), tool execution (`tool_start`/`tool_result`), auto-scrolling, error states, and live Inspector status updates.

---

## 1. Architecture & State Machine

### 1.1 State Machine Values
The frontend and backend tracking states:
- `idle`: Ready for user command.
- `thinking`: Agent is analyzing input / querying LLM.
- `planning`: Agent is formulating multi-step strategy.
- `executing`: Agent is executing tasks or react loop.
- `tool_running`: Active tool call in progress.
- `waiting`: Waiting for subprocess or network.
- `completed`: Execution loop completed successfully.
- `error`: Execution failed or error encountered.

### 1.2 Event Lifecycle & Types
Backend emits structured `AgentEvent` objects over SSE (`/api/events`):
- `agent_start` / `agent_status` (with `state` payload)
- `agent_thinking`
- `tool_start` (`tool`, `input`, `target`)
- `tool_result` (`tool`, `success`, `output`, `error`, `duration_ms`)
- `agent_complete`

---

## 2. Backend Enhancements (`delta/core/engine.py`, `delta/ai/events.py`, `delta/ai/tools.py`)
1. Emit `agent_start` and `agent_thinking` immediately upon receiving any command input (not just task requests).
2. Emit `tool_start` before running tool methods, passing `target` (e.g. filename, query).
3. Emit `tool_result` immediately after execution with duration and formatted output/error.
4. Emit `agent_complete` when response generation finishes.

---

## 3. Frontend Live UI Enhancements (`delta/web/index.html` & `delta/web/static/index.html`)

### 3.1 Immediate UI Placeholder
When the user submits a command (`handleSubmit`):
- Immediately create an execution timeline block with execution ID.
- Render initial state: `⠋ Thinking...` inside the canvas before `/api/execute` fetch completes.
- Ensure area is NEVER blank.

### 3.2 Live Braille Terminal Spinner & Animations
- Subtle terminal spinner sequence: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` updated at ~80ms interval.
- Fade-in & slide-up node animations (150ms duration).

### 3.3 Execution Timeline Nodes
- **Thinking Node**: `⠋ Thinking... (Understanding request)`
- **Tool Pending Node**: `⠋ Read File - src/main.py`
- **Tool Success Node**: `✓ Read File - src/main.py (12ms)` with collapsable output details.
- **Tool Error Node**: `× Read File - src/main.py (Permission denied)`
- Human-readable format only (no raw JSON blobs).

### 3.4 Auto-Scroll & Scroll Lock Indicator
- Auto-scroll canvas to bottom on new event if user is at bottom.
- If user scrolls up > 50px from bottom, pause auto-scroll and display `↓ New activity` floating pill button. Clicking it resumes auto-scroll.

### 3.5 Inspector Live Integration
- Live updates to `Status` (`RUNNING`, `THINKING`, `IDLE`, `COMPLETED`, `ERROR`), `Active Tool`, `Commands Executed`, `Files Touched`.
- Real-time populating of `Activity` tab with timeline nodes and `Logs` tab with raw events.

---

## 4. Verification Plan
1. Run pytest test suite: `pytest tests/`
2. Test commands in Web UI:
   - `tes` (simple text response -> immediate thinking -> complete)
   - `baca file main.py` (tool execution -> tool pending -> tool success -> output)
   - `perbaiki bug pada project ini` (multi-step react loop -> tool execution -> completed)
