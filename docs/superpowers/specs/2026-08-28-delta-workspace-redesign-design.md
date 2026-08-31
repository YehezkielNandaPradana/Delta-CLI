# Delta Workspace UI Redesign Specification

Date: 2026-08-28  
Status: Approved  

---

## 1. Executive Summary
Redesign the Delta Workspace UI from a generic AI chatbot dashboard into a high-precision, minimal cybersecurity workstation for technical operators.

---

## 2. Core Visual & Architectural Rules

### 2.1 Elimination of AI Slop
- **Removed Terms**: "DELTA AUTONOMOUS ENGINE", "Thinking...", "Understanding request", "Analyzing user request...", "Generating response".
- **Removed Visuals**: Checkmark circles, AI sparkles, pulsing gradients, spinning AI loading indicators, excessive glassmorphism, decorative particle animations.
- **Removed Telemetry Slop**: Arbitrary step counters, fake token counters, artificial AI progress bars.

### 2.2 Operational Tone & State Realism
- Speak like a technically skilled operator.
- Show real system operational states (`Checking scope`, `Scope verified`, `Resolving DNS`, `Running reconnaissance`, `Enumerating endpoints`, `Inspecting HTTP responses`, `Validating finding`, `Generating report`).

---

## 3. Layout Specification (3-Column Workstation)

### 3.1 Header Bar
- Minimalist height bar with neutral dark background (`zinc-950`), subtle border (`zinc-800`).
- Left: `DELTA` workspace title + Run ID badge (`run_...`).
- Center/Right: Target (`api.example.com`), Scope Status (`SCOPE: VERIFIED`), Operation Status (`RUNNING`/`IDLE`/`COMPLETED`).

### 3.2 Left Sidebar (Navigation & Workspaces)
- Compact width (`w-52` or collapsible `w-16`).
- **Operations Section**: Recon, Web, Network, Exploit, Evidence, Reports.
- **Workspace Section**: Current operation, Targets, History.
- Simple, high-contrast monochrome icons with minimal hover states (`zinc-800/50`).

### 3.3 Center Area (Unified Operational Stream)
- Single unified stream feed without chat bubbles or corporate AI container styles.
- Integrated **Live Activity** block showing technical metrics (`DNS: 12 records`, `HTTP: 3 endpoints`, `TECH: nginx/Node.js`, `PORTS: 4 discovered`).
- Clean terminal-style command input box (`> ` prompt) at the bottom.

### 3.4 Right Sidebar (Operational Metadata & Line Chart)
- **Top Panel**: Real operational status metadata (Target, Scope, Active Task, Findings count, Risk rating, Progress %).
- **Integrated Line Chart**:
  - Maintained in workspace as supporting analytical visualization.
  - Redesigned: dark neutral background (`zinc-950`), subtle zinc borders (`zinc-800`), clean typography, minimal line path stroke, no gradient fills under the line, no neon glow effects.
  - Smooth 100-150ms transitions on data update.

---

## 4. Animation & Interaction System
- All animations constrained to 100–150ms functional transitions.
- Fade-in for log entry insertions (2–4px subtle slide).
- No animated line-drawing loops on chart render.
- Status indicators use subtle solid dots (`● CONNECTED`, `● RUNNING`, `● COMPLETED`).
