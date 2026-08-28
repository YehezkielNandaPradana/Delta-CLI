# Spec: Delta Agent Workflow & Live Pipeline UI Redesign

**Date:** 2026-08-27  
**Status:** Approved  
**Author:** Delta Engineering Team  

---

## 1. Executive Summary
Dokumen ini mendefinisikan desain visual dan arsitektur interaktif baru untuk komponen **Agent Workflow / Pipeline Execution Card** pada antarmuka web dan terminal Delta CLI. Redesain ini mengadopsi gaya **Cyber Glass / Modern HUD** dengan glowing radar accents, tree connector hierarchy, interactive collapsible tool output drawers, serta live telemetry header.

---

## 2. Visual Architecture & HUD Header Card

### 2.1 Container Styling
- **Cyber Glass Backdrop**:
  - `bg-white/85 dark:bg-zinc-950/80 backdrop-blur-xl`
  - Border: `border border-indigo-500/25 dark:border-indigo-500/20`
  - Shadow: `shadow-lg shadow-indigo-500/5 hover:border-indigo-500/40 rounded-2xl p-4`
  - Top edge subtle glowing linear gradient (`from-indigo-500/30 via-sky-500/20 to-transparent`).

### 2.2 Header Telemetry & Controls
- **Left Indicator**:
  - Glowing animated radar dot (`bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.8)]` with CSS pulse).
  - Title: `DELTA AGENT PIPELINE` in uppercase font with tracking.
  - Subtitle / Execution Tag: `[exec-id]` in muted font-mono.
- **Right Status Pill**:
  - `RUNNING`: Indigo glowing pill (`bg-indigo-500/10 border-indigo-500/30 text-indigo-400`) + spinning orbit glyph.
  - `COMPLETED`: Emerald pill (`bg-emerald-500/10 border-emerald-500/30 text-emerald-400`) + checkmark + total execution time.
  - `FAILED`: Crimson alert pill + error summary.
- **Live Shimmer Telemetry Bar**:
  - Progress bar running full-width below the header.
  - Indeterminate scan wave shimmer animation during active execution.
  - Smoothly converts to solid emerald 100% on completion.
  - Telemetry chips: `⏱️ Duration (ms/s)`, `⚡ Steps count`, `🧠 Tokens`, `📁 Files touched`.

---

## 3. Step Timeline Tree & Interactive Drawers

### 3.1 Connector Hierarchy
- Steps dikelompokkan dengan garis vertikal berstruktur pohon (`border-l-2 border-indigo-500/20 dark:border-indigo-500/30`).
- Setiap step memiliki dot/badge status:
  - **Running**: Double-ring animated scanner icon (`progress_activity` spin + cyan/indigo soft halo).
  - **Success**: Emerald circle checkmark (`check_circle`) dengan bounce-in micro animation.
  - **Error**: Crimson badge (`cancel` / `warning`) dengan alert highlight.

### 3.2 Step Card Details
- **Glass Pill Layout**:
  - `bg-zinc-100/60 dark:bg-zinc-900/50 hover:bg-white/80 dark:hover:bg-zinc-800/80 border border-zinc-200/60 dark:border-zinc-800/70 rounded-xl p-2.5 px-3`
  - Action / Tool title dengan typography kontras tinggi.
  - Tool/Path badge: `font-mono text-indigo-500 bg-indigo-500/10 px-1.5 py-0.5 rounded text-[10.5px]`.
  - Duration chip di sisi kanan (`font-mono text-zinc-400 text-[10px]`).

### 3.3 Collapsible Tool Output Drawer
- Step yang menghasilkan payload/output (seperti hasil command, AST, read file, diff) memiliki toggle chevron `expand_more`.
- Klik pada baris step membuka drawer berkonten:
  - Formatted syntax-highlighted code / log box.
  - Tombol aksi: `Copy Output`, `Expand Fullscreen`.

---

## 4. Animation & Responsive Performance
1. **Enter Animations**:
   - `animate-process-enter`: Keyframes `translateY(4px) -> translateY(0)` dengan spring bezier `cubic-bezier(0.22, 1, 0.36, 1)`.
2. **Reduced Motion**:
   - `@media (prefers-reduced-motion: reduce)` me-nonaktifkan shimmer, spin-slow, dan pulse effects.

---

## 5. Files to Update
- `delta/web/static/index.html` (Main Web UI HTML & JavaScript timeline engine)
- `delta/web/index.html` (Mirror template)
- `delta/ai/cli_renderer.py` (CLI ANSI terminal renderer alignment)

---

## 6. Verification & Self-Review Checklist
- [x] **No Placeholders**: Semua style tokens, classnames, dan state machine terdefinisi jelas.
- [x] **Consistency**: Selaras dengan tema Dark Slate / Emerald / Sky / Indigo dari Delta Web IDE & CLI.
- [x] **Completeness**: Mencakup header, telemetry, step hierarchy, drawer output, dan animations.
