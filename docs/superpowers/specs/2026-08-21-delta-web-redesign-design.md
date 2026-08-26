# Design Specification: Delta Web SOC Operations Dashboard Redesign (Light Theme)

Date: 2026-08-21
Status: Approved

---

## 1. Executive Summary

This document specifies the complete visual and structural redesign of the Delta AI Coding Agent Web Interface into a high-performance **Cyber Assessment Operations Dashboard (SOC Style)** featuring a clean, professional **Light Theme** aesthetic and lightning-themed branding.

---

## 2. Branding & Identity

- **Logo Emblem**: Pure Lightning Cyber Icon (`⚡`) inside a rounded container (`bg-sky-50 border border-sky-200 shadow-sm`).
- **Brand Text**: `DELTA` (Font: Geist, Weight: 700, Color: `#0f172a` Slate-900).
- **Badge**: `SOC CYBER OPS` (Font: JetBrains Mono, Size: 10px, Color: `#0369a1` Sky-700, Background: `#f0f9ff`).
- **Theme Philosophy**: High-contrast, clean light theme for Security Operations Centers (SOC).

---

## 3. Color Palette & Typography

### Colors (Tailwind Tokens)
- **Canvas/Background**: `#f8fafc` (`bg-slate-50`)
- **Panel & Card Surface**: `#ffffff` (`bg-white`, `border-slate-200`, `shadow-sm`)
- **Primary Accent**: `#0284c7` (`sky-600`) / `#0369a1` (`sky-700`)
- **Lightning/Warning Accent**: `#d97706` (`amber-600`) / `#f59e0b` (`amber-500`)
- **Text Primary**: `#0f172a` (`slate-900`)
- **Text Secondary**: `#475569` (`slate-600`)
- **Text Muted**: `#94a3b8` (`slate-400`)
- **Borders & Lines**: `#e2e8f0` (`slate-200`)
- **Status Indicators**:
  - Low Risk / Online: `#10b981` (`emerald-500`)
  - Medium Risk / Warning: `#f59e0b` (`amber-500`)
  - High Risk / Failed: `#ef4444` (`red-500`)

### Typography
- **Headings & Body**: `Geist`, `sans-serif`
- **Code, Metrics & Badges**: `JetBrains Mono`, `monospace`

---

## 4. UI Architecture & Grid Layout

### A. Header Topbar (Height: 52px)
1. **Brand Identity (Left)**: Logo Petir (`⚡`), Title (`DELTA`), Subtitle Badge (`SOC CYBER OPS`).
2. **Metrics Bar (Center)**:
   - Active Target pill badge (e.g. `Target: localhost`).
   - Vulnerability severity counters: `High: 0` (Red), `Med: 0` (Amber), `Low: 0` (Emerald).
3. **Control Bar (Right)**:
   - System Status Pulse (`● Online`).
   - Active LLM Model Selector (`MODEL: AntigravityCombo`).
   - Quick Command Palette trigger (`⌘K`).
   - Settings & Reset session.

### B. Main Workspace Grid (3-Column Layout)
1. **Left Operations Control Sidebar (Width: 260px)**:
   - Project & Branch Card (`main-branch`).
   - Quick Action Security Buttons (`scan`, `audit`, `explain`, `password`, `cve`, `brute`).
   - Navigation links (`Files`, `Tasks`, `History`, `Agents`, `Tools`, `MCP`).
2. **Center Operational Console & Canvas (Flex-1)**:
   - **Header Sub-bar**: View title & Real-time Task progress indicator.
   - **Timeline Stream**: Step-by-step progress cards (`agent_start`, `tool_start`, `tool_result`, `file_update`).
   - **Message Canvas**: User Command Cards, AI Agent Markdown Responses, Code & File Diff viewers.
   - **Floating Input Box**: Textarea with `Send ⚡`, `Attach File`, `Context`, and shortcut hint (`↵ send`).
3. **Right SOC Inspector Sidebar (Width: 320px)**:
   - **Target Overview**: IP/Host, Latency.
   - **Active Context Details**: Active Model, Protocol (9Router), Git Working Tree Status.
   - **Session Activity Stats**: Total Executed Commands, Tool Call Counter, Modified File Counter.

---

## 5. SSE Event Integration & Data Flow

- Real-time SSE listener at `/api/events`.
- Events update the UI dynamically:
  - `agent_start` / `agent_status` → Displays timeline step and status spinner.
  - `tool_start` / `tool_result` → Adds tool execution card with duration timer (`duration_ms`).
  - `file_update` → Renders inline code diff card (green `+` added / red `-` removed lines).
  - `agent_complete` → Updates header status to `Idle` and marks execution finished.

---

## 6. Implementation Scope & Files Affected

- `delta/web/index.html` (Main Template)
- `delta/web/static/index.html` (Static Standalone Fallback)

---

## 7. Self-Review Verification

- [x] Placeholder scan: No TBD or vague requirements.
- [x] Internal consistency: All colors match the Slate & Sky Light Theme spec.
- [x] Scope check: Cleanly isolated to web templates and styling.
- [x] Ambiguity check: Layout and logo specifications explicitly defined.
