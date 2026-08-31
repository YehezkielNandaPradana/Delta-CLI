# Delta Workspace UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Delta Workspace into a cybersecurity workstation by eliminating AI slop, unifying operational feeds, and modernizing the Line Chart visual style.

**Architecture:** Refactor `delta/web/index.html` and `delta/web/static/index.html` layout structure into a 3-column cybersecurity workstation, update live activity feed generators, and re-style the integrated Line Chart to match dark neutral minimalism.

**Tech Stack:** HTML5, Tailwind CSS, Native JavaScript, Chart.js (Line Chart).

## Global Constraints

- Preserve Line Chart functionality without gradient fills, neon glow, or excessive animation.
- Unified stream feed without chat bubbles or corporate AI container styles.
- Eliminate terms: "DELTA AUTONOMOUS ENGINE", "Thinking...", "Understanding request", "Analyzing user request...", "Generating response".
- Workstation dark theme default with neutral zinc palette.

---

### Task 1: Header Bar & Navigation Left Sidebar Redesign

**Files:**
- Modify: `delta/web/index.html:240-340`
- Modify: `delta/web/static/index.html:240-340`

**Interfaces:**
- Consumes: Header status indicators & sidebar navigation routes
- Produces: 3-column layout left navigation sidebar (Operations & Workspace sections) and clean workstation top header.

- [ ] **Step 1: Inspect header & sidebar elements**
Read lines 240-340 of `delta/web/index.html`.

- [ ] **Step 2: Update Header Bar HTML**
Replace AI engine titles with `DELTA` cybersecurity workstation header (Target, Scope: VERIFIED, Operation Status, Run ID).

- [ ] **Step 3: Update Left Sidebar HTML**
Replace AI agent profile cards with compact navigation sections (Operations: Recon, Web, Network, Exploit, Evidence, Reports; Workspace: Current operation, Targets, History).

- [ ] **Step 4: Sync changes to static/index.html**
Copy updated header and left sidebar markup to `delta/web/static/index.html`.

- [ ] **Step 5: Verify layout in browser/static structure**
Ensure syntax is clean and valid.

- [ ] **Step 6: Commit**
```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "refactor(ui): update header bar and left sidebar for cybersecurity workstation"
```

---

### Task 2: Unified Operational Stream & Live Activity Area Redesign

**Files:**
- Modify: `delta/web/index.html:1280-1480`
- Modify: `delta/web/static/index.html:1280-1480`

**Interfaces:**
- Consumes: Agent WebSocket events (`agent_start`, `tool_start`, `tool_result`, `agent_thinking`)
- Produces: Single unified operational log stream without chat bubbles or AI slop wording.

- [ ] **Step 1: Read process timeline & turn container functions**
Read lines 1280-1480 of `delta/web/index.html`.

- [ ] **Step 2: Replace AI Slop Wording & Badges**
Update `addOrUpdateProcessStep`, `finalizeTimelineSuccess`, and `handleAgentEvent` to remove "DELTA AUTONOMOUS ENGINE", "Understanding request", etc., and use technical states (`Checking scope`, `Running reconnaissance`, `Resolving DNS`).

- [ ] **Step 3: Remove Chat Bubble Styles**
Update assistant bubble container HTML to blend cleanly with the unified stream feed instead of looking like a corporate messaging bubble.

- [ ] **Step 4: Sync to static/index.html**
Apply updated stream rendering functions to `delta/web/static/index.html`.

- [ ] **Step 5: Commit**
```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "refactor(ui): update unified operational stream and remove AI slop phrasing"
```

---

### Task 3: Right Sidebar Metadata Panel & Line Chart Visual Integration

**Files:**
- Modify: `delta/web/index.html:350-450`
- Modify: `delta/web/static/index.html:350-450`

**Interfaces:**
- Consumes: Operational status state & Chart.js latency/token line chart data.
- Produces: Modern dark neutral Line Chart and technical metadata panel.

- [ ] **Step 1: Read Right Sidebar and Chart initialization script**
Read lines 350-450 and chart rendering functions in `delta/web/index.html`.

- [ ] **Step 2: Redesign Right Sidebar Metadata**
Update target, scope status, findings count, risk rating, and progress percentage.

- [ ] **Step 3: Restyle Line Chart**
Update Chart.js configuration/SVG rendering options: set dark neutral background (`#09090b` / `zinc-950`), solid subtle zinc stroke, remove gradient fills, remove neon glow, and set clean monospace tooltips.

- [ ] **Step 4: Sync to static/index.html**
Apply right sidebar and line chart modifications to `delta/web/static/index.html`.

- [ ] **Step 5: Commit**
```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "refactor(ui): integrate dark neutral line chart and operational metadata right sidebar"
```
