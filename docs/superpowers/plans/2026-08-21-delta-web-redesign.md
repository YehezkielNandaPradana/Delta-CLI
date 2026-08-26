# Delta Web SOC Operations Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Delta Web IDE into a high-performance, Light Theme Cyber Assessment Operations Dashboard (SOC Style) with Lightning Emblem Branding (`⚡`).

**Architecture:** Tailwind CSS-driven single-page application (`delta/web/index.html` and `delta/web/static/index.html`), integrated with Python HTTP SSE event server (`delta/web/server.py`) and Engine Bridge (`delta/web/bridge.py`).

**Tech Stack:** HTML5, Tailwind CSS (via CDN with custom config), Vanilla JavaScript (ES6+), Server-Sent Events (SSE), Python 3 stdlib / pytest.

## Global Constraints

- Light theme Slate-50 background (`#f8fafc`), White panels (`#ffffff`), Sky-700 primary text/accents (`#0369a1`), Amber-600 lightning/warning accents (`#d97706`).
- Pure Lightning emblem (`⚡`) in rounded container (`bg-sky-50 border border-sky-200 shadow-sm`), NO triangle/Delta shape.
- Synchronize all changes between `delta/web/index.html` and `delta/web/static/index.html`.
- Run pytest verification after changes.

---

### Task 1: Header Topbar & Lightning Emblem Branding

**Files:**
- Modify: `delta/web/index.html`
- Modify: `delta/web/static/index.html`
- Test: `tests/test_web_server.py`

**Interfaces:**
- Consumes: `/api/status`, SSE `/api/events`
- Produces: Header Topbar DOM elements with brand title `DELTA`, lightning logo `⚡`, SOC metrics, and status pulse.

- [ ] **Step 1: Verify current web server test passes**

Run: `pytest tests/test_web_server.py -v`
Expected: PASS

- [ ] **Step 2: Update Header Brand Identity and Metrics in `delta/web/index.html`**

Ensure `header` in `delta/web/index.html` has:
```html
<header class="bg-white border-b border-slate-200 flex justify-between items-center h-12 px-4 w-full z-50 shrink-0 select-none shadow-sm">
    <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-xl bg-sky-50 border border-sky-200 text-sky-600 flex items-center justify-center font-bold text-lg shadow-sm">⚡</div>
        <div class="flex flex-col">
            <span class="text-sm font-bold tracking-wider text-slate-900 font-sans flex items-center gap-2">DELTA</span>
            <span class="text-[9px] font-mono font-bold tracking-widest text-sky-700 bg-sky-50 px-1.5 py-0.2 rounded border border-sky-200">SOC CYBER OPS</span>
        </div>
        <button onclick="toggleModal('command-palette')" class="flex items-center bg-slate-100 border border-slate-200 hover:border-sky-500/50 rounded-lg px-3 py-1 ml-2 text-slate-600 font-mono text-xs transition-all btn-active-scale group">
            <span class="material-symbols-outlined text-[14px] mr-2 text-slate-400 group-hover:text-sky-600">search</span>
            <span>Search files, symbols, commands</span>
            <kbd class="ml-4 text-[10px] bg-slate-200 px-1.5 py-0.5 rounded text-slate-600 border border-slate-300 font-mono">⌘K</kbd>
        </button>
    </div>
    <div class="flex items-center gap-3">
        <div class="hidden md:flex items-center gap-2 font-mono text-xs">
            <span class="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 font-bold" id="header-target-badge">Target: localhost</span>
            <span class="bg-red-50 text-red-700 px-2 py-0.5 rounded border border-red-200 font-bold text-[11px]">0 High</span>
            <span class="bg-amber-50 text-amber-700 px-2 py-0.5 rounded border border-amber-200 font-bold text-[11px]">0 Med</span>
            <span class="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded border border-emerald-200 font-bold text-[11px]">0 Low</span>
        </div>
        <div class="flex items-center gap-2 border border-sky-200 rounded-full px-2.5 py-0.5 bg-sky-50 text-xs font-mono">
            <div class="w-2 h-2 rounded-full bg-sky-500 animate-pulse-subtle" id="status-indicator-dot"></div>
            <span class="text-sky-700 uppercase tracking-wider text-[11px] font-bold" id="status-indicator-text">Online</span>
        </div>
    </div>
</header>
```

- [ ] **Step 3: Sync changes to `delta/web/static/index.html`**

Update `delta/web/static/index.html` header structure to match `delta/web/index.html`.

- [ ] **Step 4: Verify test suite passes**

Run: `pytest tests/test_web_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit Header Changes**

```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "feat(web): update SOC header topbar with lightning emblem and severity counters"
```

---

### Task 2: Left Control Panel & Quick Action Toolbar

**Files:**
- Modify: `delta/web/index.html`
- Modify: `delta/web/static/index.html`

**Interfaces:**
- Consumes: `sendPrompt(cmd)`, `switchNav(viewName)`
- Produces: Sidebar DOM structure for Quick Security Commands (`scan`, `audit`, `explain`, `password`, `cve`, `brute`) and Active Branch/Project metadata.

- [ ] **Step 1: Update Left Sidebar Quick Commands & Action Buttons in `delta/web/index.html`**

Ensure `aside` left sidebar contains:
```html
<aside class="bg-white border-r border-slate-200 w-[240px] shrink-0 flex flex-col h-full z-40 hidden md:flex select-none">
    <div class="p-3 border-b border-slate-200 flex justify-between items-center bg-slate-50">
        <div>
            <h2 class="text-[10px] font-mono tracking-widest text-slate-500 uppercase font-semibold mb-0.5">PROJECT WORKSPACE</h2>
            <p class="text-slate-800 font-mono text-xs flex items-center gap-1.5 font-medium">
                <span class="w-2 h-2 rounded-full bg-sky-500 animate-pulse"></span> main-branch
            </p>
        </div>
    </div>
    <nav class="flex-1 overflow-y-auto p-2 flex flex-col gap-1 bg-white" id="sidebar-nav">
        <button onclick="switchNav('files')" id="nav-files" class="nav-btn active-nav w-full text-left flex items-center text-sky-700 bg-sky-50 border-l-2 border-sky-600 rounded-lg px-3 py-2 text-xs transition-all duration-150 btn-active-scale font-medium">
            <span class="material-symbols-outlined text-[16px] mr-2">folder</span>
            <span>Files</span>
        </button>
        <button onclick="switchNav('tasks')" id="nav-tasks" class="nav-btn w-full text-left flex items-center text-slate-600 px-3 py-2 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all duration-150 border-l-2 border-transparent text-xs btn-active-scale">
            <span class="material-symbols-outlined text-[16px] mr-2">assignment</span>
            <span>Tasks</span>
        </button>
        <div class="mt-3 px-3 mb-1">
            <h3 class="text-[10px] font-mono tracking-widest text-slate-400 uppercase font-semibold">QUICK ACTIONS</h3>
        </div>
        <button onclick="sendPrompt('scan localhost')" class="w-full text-left flex items-center text-slate-700 px-3 py-2 hover:bg-sky-50 hover:text-sky-800 rounded-lg transition-all text-xs group btn-active-scale">
            <span class="material-symbols-outlined text-[16px] mr-2 text-sky-600">radar</span>
            <span class="truncate font-mono text-[11px]">scan localhost</span>
        </button>
        <button onclick="sendPrompt('audit example.com')" class="w-full text-left flex items-center text-slate-700 px-3 py-2 hover:bg-amber-50 hover:text-amber-800 rounded-lg transition-all text-xs group btn-active-scale">
            <span class="material-symbols-outlined text-[16px] mr-2 text-amber-600">security</span>
            <span class="truncate font-mono text-[11px]">audit example.com</span>
        </button>
        <button onclick="sendPrompt('explain SQL injection')" class="w-full text-left flex items-center text-slate-700 px-3 py-2 hover:bg-sky-50 hover:text-sky-800 rounded-lg transition-all text-xs group btn-active-scale">
            <span class="material-symbols-outlined text-[16px] mr-2 text-sky-600">menu_book</span>
            <span class="truncate font-mono text-[11px]">explain SQLi</span>
        </button>
    </nav>
</aside>
```

- [ ] **Step 2: Sync Left Sidebar to `delta/web/static/index.html`**

Update `delta/web/static/index.html` to mirror the sidebar structure.

- [ ] **Step 3: Run pytest to verify no broken routes/templates**

Run: `pytest tests/test_web_server.py -v`
Expected: PASS

- [ ] **Step 4: Commit Sidebar Changes**

```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "feat(web): update left sidebar quick security actions"
```

---

### Task 3: Center Operational Console, Live Event Stream Cards & Floating Input

**Files:**
- Modify: `delta/web/index.html`
- Modify: `delta/web/static/index.html`

**Interfaces:**
- Consumes: SSE `/api/events` payload (`agent_start`, `tool_start`, `tool_result`, `file_update`), `handleSubmit(e)`
- Produces: Live Execution Timeline step cards, user command bubbles (`YOU COMMAND`), AI response cards (`Δ DELTA AGENT`), inline file diff viewer cards, floating input textarea.

- [ ] **Step 1: Refactor Floating Input & Message Card Styling in `delta/web/index.html`**

Verify input card has lightning submit button `SEND ⚡`:
```html
<button type="submit" class="bg-sky-600 text-white px-4 py-1.5 rounded-lg flex items-center gap-1.5 font-mono hover:bg-sky-700 transition-all duration-150 font-bold text-xs btn-active-scale shadow-sm">
    <span>SEND</span>
    <span class="text-[14px]">⚡</span>
</button>
```

- [ ] **Step 2: Sync Center Console & Input to `delta/web/static/index.html`**

Sync `delta/web/static/index.html` JavaScript functions (`appendUserMessage`, `appendAiMessage`, `renderToolCallCard`, `renderFileUpdateCard`) and HTML structure.

- [ ] **Step 3: Verify pytest suite**

Run: `pytest tests/test_web_server.py -v`
Expected: PASS

- [ ] **Step 4: Commit Center Console Changes**

```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "feat(web): enhance center console execution stream and floating input bar"
```

---

### Task 4: Right SOC Inspector Sidebar & Modals

**Files:**
- Modify: `delta/web/index.html`
- Modify: `delta/web/static/index.html`

**Interfaces:**
- Consumes: Client activity state (`executedCommandsCount`, `toolCount`, `fileCount`)
- Produces: SOC Inspector sidebar cards (`Context`, `Agent Info`, `Session Activity`), Light theme Command Palette (`⌘K`), Model selection modal, Attach modal.

- [ ] **Step 1: Ensure Right Inspector cards in `delta/web/index.html` have Light Slate Theme styling**

Check `aside` right inspector contains cards:
```html
<aside class="bg-white border-l border-slate-200 w-[320px] shrink-0 flex flex-col h-full z-40 hidden lg:flex select-none shadow-sm">
    <div class="p-3 border-b border-slate-200 flex justify-between items-center bg-slate-50">
        <div>
            <h2 class="text-[10px] font-mono tracking-widest text-slate-500 uppercase font-semibold mb-0.5">INSPECTOR</h2>
            <p class="text-slate-500 font-mono text-xs">active-context</p>
        </div>
    </div>
    <div class="flex-1 overflow-y-auto p-3 space-y-3">
        <!-- Context Card -->
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2.5 shadow-sm">
            <div class="flex items-center gap-2 text-slate-700">
                <span class="material-symbols-outlined text-[16px] text-sky-600">description</span>
                <h3 class="text-[10px] font-mono tracking-widest text-slate-500 uppercase font-semibold">Context</h3>
            </div>
            <ul class="flex flex-col gap-2 font-mono text-xs">
                <li class="flex justify-between items-center p-1.5 text-slate-600 hover:bg-slate-200/60 rounded-lg transition-colors cursor-pointer" onclick="toggleModal('model-modal')">
                    <span>Engine Protocol</span>
                    <span class="text-[10px] bg-sky-50 px-2 py-0.5 rounded-md text-sky-700 border border-sky-200 font-bold">9Router</span>
                </li>
            </ul>
        </div>
    </div>
</aside>
```

- [ ] **Step 2: Sync Inspector to `delta/web/static/index.html`**

Update `delta/web/static/index.html` right inspector.

- [ ] **Step 3: Run tests to verify clean build**

Run: `pytest tests/test_web_server.py -v`
Expected: PASS

- [ ] **Step 4: Commit Inspector Changes**

```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "feat(web): update right SOC inspector and modals to light slate theme"
```

---

### Task 5: End-to-End Test Suite Verification

**Files:**
- Test: `tests/test_web_server.py`
- Test: `tests/test_agent_scenarios.py`

**Interfaces:**
- Consumes: Entire Delta Web Server and Agent Engine
- Produces: Test verification pass for all scenarios and web endpoints.

- [ ] **Step 1: Run full pytest test suite**

Run: `pytest -v`
Expected: ALL PASS

- [ ] **Step 2: Final Git Commit**

```bash
git add .
git commit -m "chore(web): finalize SOC Light Theme Web UI redesign"
```
