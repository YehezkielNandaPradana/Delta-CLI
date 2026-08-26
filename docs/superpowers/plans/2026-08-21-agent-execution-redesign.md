# Agent Execution UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the presentation layer of the "Agent Execution" page in `delta/web/index.html` to a modern, rounded developer tool aesthetic (Linear, Warp Terminal, Raycast) with refined color elevation, contrast hierarchy, micro-interactions, and 2-tier typography.

**Architecture:** Single-file HTML refactor targeting `delta/web/index.html`. Refine embedded `tailwind.config` tokens (border-radius, color palette, custom shadows), update CSS utility classes across 3 main layout columns (Left Sidebar, Middle Execution Canvas, Right Inspector), and enhance message card templates inside inline JavaScript DOM handlers.

**Tech Stack:** HTML5, Tailwind CSS (via CDN with extended config), Material Symbols Outlined, Google Fonts (Geist & JetBrains Mono), Vanilla JavaScript.

## Global Constraints

- Modify only `delta/web/index.html` (and test files if needed).
- Preserve existing JavaScript function names, modal IDs, SSE stream handlers (`/api/events`), and DOM element IDs (`#messages-container`, `#user-input`, `#sidebar-nav`, `#inspector-file-count`, etc.).
- Maintain dark theme base with WCAG AA compliant text contrast.
- Use soft rounded corners (`rounded-xl` for cards/modals, `rounded-lg` for buttons/inputs/badges).

---

### Task 1: Refine Tailwind Design Tokens & Base Styles in `delta/web/index.html`

**Files:**
- Modify: `delta/web/index.html:10-157`

**Interfaces:**
- Consumes: Tailwind CDN script & CSS rules
- Produces: Updated `tailwind.config` tokens for colors, `borderRadius`, font families, and custom CSS animations/shadows.

- [ ] **Step 1: Read Tailwind configuration block**

Inspect `delta/web/index.html` lines 10-157 to target `tailwind.config` and custom CSS styles.

- [ ] **Step 2: Update `tailwind.config` theme extensions**

Update `tailwind.config` in `delta/web/index.html`:
- Set `borderRadius`: `sm: '0.25rem'`, `DEFAULT: '0.5rem'`, `md: '0.5rem'`, `lg: '0.75rem'`, `xl: '1rem'`, `full: '9999px'`.
- Add custom elevation colors to `theme.extend.colors`:
  - `canvas`: `#080A0C`
  - `panel`: `#0E1216`
  - `card-agent`: `#13181E`
  - `card-user`: `#161C24`
  - `card-system`: `#0F1318`
  - `border-subtle`: `#1A2027`
  - `border-focus`: `#1F2937`
- Add custom box shadow: `'card-agent': '0 4px 20px -2px rgba(0,0,0,0.5)'`.

- [ ] **Step 3: Test HTML file parsing/rendering**

Verify syntax of `delta/web/index.html` script tag and open/load HTML in local server or test runner.

Run: `python -m unittest tests/test_web_server.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add delta/web/index.html
git commit -m "style(web): refine design tokens and tailwind config for rounded agent ui"
```

---

### Task 2: Redesign Navigation Top AppBar and Left Sidebar Layout

**Files:**
- Modify: `delta/web/index.html:160-264`

**Interfaces:**
- Consumes: Tailwind tokens from Task 1
- Produces: Modern rounded top header & left sidebar with left-glow active indicators and styled quick command section headers.

- [ ] **Step 1: Redesign `<header>` Top AppBar**

In `delta/web/index.html`:
- Style `<header>`: `bg-[#0E1216] border-b border-[#1A2027] h-12 px-4 shadow-sm`.
- Command palette trigger button: `bg-[#080A0C] border border-[#1A2027] hover:border-primary/50 rounded-lg px-3 py-1 text-slate-400 font-mono text-xs transition-all flex items-center`.
- Shortcut badge: `kbd` element with `bg-[#161C24] border border-[#222A33] rounded px-1.5 py-0.5 text-[10px] text-slate-400 font-mono`.

- [ ] **Step 2: Redesign `<aside>` Left Sidebar**

In `delta/web/index.html`:
- Sidebar container: `bg-[#0E1216] border-r border-[#1A2027] w-[240px]`.
- Section titles (`PROJECT`, `QUICK COMMANDS`, `WORKSPACE`): `text-[10px] font-mono tracking-widest text-slate-500 uppercase font-semibold mt-4 mb-1.5 px-3`.
- Nav buttons (`.nav-btn`): `w-full text-left flex items-center gap-2.5 px-3 py-2 text-slate-400 hover:text-slate-200 hover:bg-[#161C24] rounded-lg transition-all text-xs font-sans`.
- Active nav button state (`.active-nav`): `bg-primary/10 text-primary font-medium border-l-2 border-primary rounded-lg shadow-sm`.

- [ ] **Step 3: Run web server unit tests to ensure endpoints and templates render intact**

Run: `python -m unittest tests/test_web_server.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add delta/web/index.html
git commit -m "style(web): redesign top appbar and left sidebar navigation"
```

---

### Task 3: Redesign Middle Execution Canvas, Feed Cards & Bottom Command Bar

**Files:**
- Modify: `delta/web/index.html:265-325`

**Interfaces:**
- Consumes: Tailwind tokens & UI components
- Produces: Refactored Execution Canvas, User Command input bar with glowing focus ring, and status indicator header.

- [ ] **Step 1: Redesign Workspace Header & Main Canvas Container**

In `delta/web/index.html`:
- Main view background: `bg-[#080A0C]`.
- Workspace header: `h-12 border-b border-[#1A2027] bg-[#0E1216] px-4 flex justify-between items-center`.
- Title "AGENT EXECUTION": `text-sm font-semibold tracking-wider text-slate-200 uppercase font-sans`.
- Status pill: `flex items-center gap-2 border border-[#1E252D] rounded-full px-2.5 py-0.5 bg-[#12171D] text-xs font-mono text-primary`.

- [ ] **Step 2: Redesign Bottom Command Input Bar**

In `delta/web/index.html`:
- Form container (`#chat-form`): `relative flex flex-col bg-[#0E1216] border border-[#1F2937] rounded-xl focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/40 shadow-xl transition-all duration-200`.
- Textarea (`#user-input`): `w-full bg-transparent border-none text-slate-100 font-sans text-sm resize-none focus:ring-0 p-3.5 h-[64px] placeholder:text-slate-500 focus:outline-none`.
- Bottom toolbar: `flex justify-between items-center p-2 border-t border-[#1A2027] text-xs font-mono text-slate-400`.
- Add inline keyboard hint badge: `<div class="flex items-center gap-2 text-[11px] text-slate-500"><kbd class="bg-[#161C24] px-1.5 py-0.5 rounded border border-[#222A33]">↵</kbd> send</div>`.
- Send button: `bg-primary text-black px-4 py-1.5 rounded-lg font-bold font-mono text-xs flex items-center gap-1.5 hover:bg-primary-fixed-dim transition-all shadow-sm`.

- [ ] **Step 3: Run web server unit tests**

Run: `python -m unittest tests/test_web_server.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add delta/web/index.html
git commit -m "style(web): redesign execution canvas header and bottom input bar"
```

---

### Task 4: Redesign Right Inspector Panel & Modals

**Files:**
- Modify: `delta/web/index.html:326-595`

**Interfaces:**
- Consumes: Tailwind design tokens
- Produces: Grouped card layout inside Inspector panel and modern `rounded-xl` modal popups.

- [ ] **Step 1: Redesign Right Inspector Panel Layout**

In `delta/web/index.html`:
- Inspector container: `bg-[#0E1216] border-l border-[#1A2027] w-[320px] shadow-sm`.
- Header: `p-3 border-b border-[#1A2027] flex justify-between items-center`.
- Group sections (`Context`, `Agent Info`, `Session Activity`): Encapsulate each section inside `m-3 p-3.5 bg-[#11161C] border border-[#1A2027] rounded-xl space-y-2.5 shadow-sm`.
- Section Header: `text-[10px] font-mono tracking-widest text-slate-400 uppercase font-semibold flex items-center gap-1.5 mb-2`.
- Key-Value rows: Key label `text-slate-400 text-xs font-sans`, Value badge `text-slate-200 text-xs font-mono bg-[#161C24] px-2 py-1 rounded-md border border-[#222A33] font-medium`.

- [ ] **Step 2: Redesign Modals & Dialogs (`command-palette`, `model-modal`, etc.)**

In `delta/web/index.html`:
- Update modal containers: `bg-[#11161C] border border-[#1A2027] rounded-xl shadow-2xl overflow-hidden`.
- Update input search bars & option buttons inside modal dialogs to use `rounded-lg` and `hover:bg-[#161C24]`.

- [ ] **Step 3: Run web server unit tests**

Run: `python -m unittest tests/test_web_server.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add delta/web/index.html
git commit -m "style(web): redesign inspector panel into grouped cards and refine modal popups"
```

---

### Task 5: Refactor Dynamic Message Renderers in JavaScript Client Script

**Files:**
- Modify: `delta/web/index.html:598-1000`

**Interfaces:**
- Consumes: Client script message handlers (`appendUserMessage`, `appendAiMessage`, `handleAgentEvent`, etc.)
- Produces: Visual card templates for User Input, Agent Response (with left cyan accent border), and System Messages.

- [ ] **Step 1: Update message renderer JS functions in `delta/web/index.html`**

In `<script>` section of `delta/web/index.html`:
- Update `appendUserMessage(text)`: Render container with `bg-[#161C24] border border-[#222B35] rounded-xl p-4 shadow-sm animate-slide-up`, right-aligned/distinct input styling with badge `<span class="text-[10px] font-mono text-primary font-semibold uppercase bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">$ USER COMMAND</span>`.
- Update `appendAiMessage(text)`: Render container with `bg-[#13181E] border border-[#1E2630] border-l-4 border-l-primary rounded-xl p-4 shadow-card-agent animate-slide-up`, header badge `<span class="text-[10px] font-mono text-primary font-bold uppercase tracking-wider flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span> DELTA AGENT</span>`.
- Update System message renderer: Render container with `bg-[#0F1318] border border-[#1A2027] rounded-xl p-3 text-slate-400 font-mono text-xs`.
- Update processing indicator / typing status: `flex items-center gap-2 text-slate-400 font-mono text-xs bg-[#13181E] border border-[#1E2630] rounded-xl p-3`.

- [ ] **Step 2: Run full web server test suite**

Run: `python -m unittest tests/test_web_server.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add delta/web/index.html
git commit -m "feat(web): update js client renderers for elevated message cards and typing indicators"
```

---

## Plan Verification

Run the web server unit tests to confirm server & web asset integrity:
`python -m unittest tests/test_web_server.py`
