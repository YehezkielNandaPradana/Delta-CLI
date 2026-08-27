# TopBar Floating Island HUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the conventional static top navigation bar into a 3-piece Floating Island HUD with Cyberpunk & Modern Glassmorphism aesthetic for Delta IDE.

**Architecture:** Replace the standard flat `<header>` with a lightweight wrapper hosting three floating, glassmorphic capsule islands (Left Brand & Context, Center Omnibar, Right Telemetry & Controls). Preserve all existing DOM element IDs, event handlers, modals, and dynamic data bindings (`header-target-badge`, `status-indicator-text`, `theme-toggle-btn`).

**Tech Stack:** HTML5, Tailwind CSS, Material Symbols Outlined, Vanilla JS, CSS3 Backdrop-Filter & Keyframe Animations.

## Global Constraints
- Keep all existing IDs intact: `header-target-badge`, `status-indicator-text`, `theme-toggle-btn`, `theme-toggle-icon`.
- Maintain all modal actions: `toggleModal('command-palette')`, `toggleModal('branch-modal')`, `toggleModal('notifications-modal')`, `toggleModal('settings-modal')`, `cycleTheme()`, `switchNav('execution')`.
- Support Dark/Light mode seamlessly via Tailwind `dark:` variants and `backdrop-blur-xl`.
- Respect `@media (prefers-reduced-motion: reduce)`.
- Keep `delta/web/index.html` and `delta/web/static/index.html` strictly synchronized.

---

### Task 1: CSS Animations & Floating Island Styling

**Files:**
- Modify: `delta/web/index.html:110-175`
- Modify: `delta/web/static/index.html:110-175`

**Interfaces:**
- Produces: CSS utility classes for floating island shadows, cyber border glows, and telemetry indicators (`.hud-island`, `.hud-glow`).

- [ ] **Step 1: Add HUD Island & Cyber Glow CSS styles to `delta/web/index.html`**

Add the following styles into the `<style>` block in `delta/web/index.html`:
```css
/* Floating Island HUD Styles */
.hud-island {
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05), 0 2px 6px -1px rgba(0, 0, 0, 0.03);
}
.dark .hud-island {
    box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4), 0 2px 8px -1px rgba(0, 0, 0, 0.2);
}
.hud-island:hover {
    box-shadow: 0 8px 30px -4px rgba(99, 102, 241, 0.12), 0 4px 12px -2px rgba(0, 0, 0, 0.05);
}
.dark .hud-island:hover {
    box-shadow: 0 10px 32px -4px rgba(99, 102, 241, 0.25), 0 4px 14px -2px rgba(0, 0, 0, 0.3);
}
```

- [ ] **Step 2: Replicate CSS changes into `delta/web/static/index.html`**

Ensure `delta/web/static/index.html` has the identical CSS rules in its `<style>` block.

- [ ] **Step 3: Verification**

Check that the `<style>` block contains `.hud-island` without syntax errors.

- [ ] **Step 4: Commit**

```bash
git add delta/web/index.html delta/web/static/index.html
git commit -m "style(web): add floating island HUD CSS styles"
```

---

### Task 2: Implement 3-Piece Floating Island HUD in `delta/web/index.html`

**Files:**
- Modify: `delta/web/index.html:176-225`

**Interfaces:**
- Consumes: `.hud-island` classes from Task 1.
- Produces: Updated `<header>` component with 3 floating capsules preserving `header-target-badge`, `status-indicator-text`, `theme-toggle-btn`, `theme-toggle-icon`, and all `onclick` handlers.

- [ ] **Step 1: Replace `<header>` markup in `delta/web/index.html`**

Replace the current `<header>` block (lines ~176-224) with:
```html
    <!-- TopAppBar Floating Island HUD -->
    <header class="w-full px-3.5 pt-2.5 pb-1 flex justify-between items-center z-50 shrink-0 select-none bg-transparent gap-2">
        <!-- Island 1: Brand & Project Context (Left) -->
        <div class="hud-island bg-white/80 dark:bg-zinc-900/85 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-800/80 hover:border-indigo-500/40 rounded-2xl px-3 py-1.5 flex items-center gap-2.5 transition-base">
            <div class="flex items-center gap-2 cursor-pointer group" onclick="switchNav('execution')" title="Delta Core Home">
                <div class="w-7 h-7 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 text-white flex items-center justify-center font-bold text-xs shadow-md transition-all duration-300 group-hover:scale-105 group-hover:rotate-3 group-hover:shadow-indigo-500/30">
                    Δ
                </div>
                <div class="flex flex-col">
                    <span class="text-xs font-bold tracking-tight text-zinc-900 dark:text-zinc-100 flex items-center gap-1">
                        DELTA <span class="text-[9px] font-mono font-semibold px-1 py-0.2 rounded bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">HUD</span>
                    </span>
                </div>
            </div>

            <div class="h-4 w-px bg-zinc-200 dark:bg-zinc-800 mx-0.5"></div>

            <div class="hidden sm:flex items-center gap-1.5 font-mono text-[10px]">
                <span class="px-2 py-0.5 rounded-full border border-zinc-200/90 dark:border-zinc-800 bg-zinc-50/80 dark:bg-zinc-800/50 text-zinc-600 dark:text-zinc-300 flex items-center gap-1 font-medium" title="Target Directory / Host">
                    <span class="material-symbols-outlined text-[12px] text-indigo-500">folder_open</span>
                    <span id="header-target-badge" class="truncate max-w-[120px] md:max-w-[180px]">localhost</span>
                </span>
            </div>
        </div>

        <!-- Island 2: Interactive Floating Omnibar (Center) -->
        <button onclick="toggleModal('command-palette')" class="hud-island flex items-center bg-white/80 dark:bg-zinc-900/85 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-800/80 hover:border-indigo-500/50 hover:bg-white dark:hover:bg-zinc-850 rounded-2xl px-3.5 py-1.5 text-zinc-400 dark:text-zinc-500 font-mono text-xs transition-base group w-64 md:w-96">
            <span class="material-symbols-outlined text-[16px] mr-2 text-zinc-400 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 transition-colors">search</span>
            <span class="text-left flex-1 text-zinc-500 dark:text-zinc-400 group-hover:text-zinc-800 dark:group-hover:text-zinc-200 transition-colors text-[11px]">Search actions, tools, files...</span>
            <kbd class="text-[9px] bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/80 px-1.5 py-0.5 rounded-md text-zinc-500 dark:text-zinc-400 font-mono font-semibold shadow-2xs group-hover:border-indigo-500/30">⌘K</kbd>
        </button>

        <!-- Island 3: Telemetry & Controls Pod (Right) -->
        <div class="hud-island bg-white/80 dark:bg-zinc-900/85 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-800/80 hover:border-indigo-500/40 rounded-2xl px-2.5 py-1.5 flex items-center gap-1.5 transition-base text-zinc-500 dark:text-zinc-400">
            <!-- Live Status Telemetry -->
            <div class="flex items-center gap-1 text-[10px] font-mono text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 font-semibold" title="Connection Status">
                <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                <span class="tracking-wider uppercase text-[9px]" id="status-indicator-text">Online</span>
            </div>

            <div class="h-4 w-px bg-zinc-200 dark:bg-zinc-800 mx-0.5"></div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-0.5">
                <button title="Branch Info" onclick="toggleModal('branch-modal')" class="text-zinc-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-base p-1.5 rounded-xl">
                    <span class="material-symbols-outlined text-[17px]">account_tree</span>
                </button>
                <button title="Notifications" onclick="toggleModal('notifications-modal')" class="text-zinc-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-base p-1.5 rounded-xl relative">
                    <span class="material-symbols-outlined text-[17px]">notifications</span>
                    <span class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-500 border border-white dark:border-zinc-900"></span>
                </button>
                <button title="Settings (Ctrl+L)" onclick="toggleModal('settings-modal')" class="text-zinc-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-base p-1.5 rounded-xl">
                    <span class="material-symbols-outlined text-[17px]">settings</span>
                </button>
                <button id="theme-toggle-btn" title="Toggle Theme" onclick="cycleTheme()" class="text-zinc-500 dark:text-zinc-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-base p-1.5 rounded-xl">
                    <span class="material-symbols-outlined text-[17px]" id="theme-toggle-icon">desktop_windows</span>
                </button>
            </div>
        </div>
    </header>
```

- [ ] **Step 2: Verification**

Ensure all IDs (`header-target-badge`, `status-indicator-text`, `theme-toggle-btn`, `theme-toggle-icon`) are present and intact.

- [ ] **Step 3: Commit**

```bash
git add delta/web/index.html
git commit -m "feat(web): redesign topbar into floating island HUD"
```

---

### Task 3: Synchronize Floating Island HUD to `delta/web/static/index.html`

**Files:**
- Modify: `delta/web/static/index.html:176-225`

**Interfaces:**
- Consumes: Task 2 implementation.
- Produces: Exact synchronized TopBar structure in static assets.

- [ ] **Step 1: Replace `<header>` markup in `delta/web/static/index.html`**

Apply the same markup replacement as Task 2 to `delta/web/static/index.html`.

- [ ] **Step 2: Verification**

Compare diff between `delta/web/index.html` and `delta/web/static/index.html` header sections to guarantee 100% parity.

- [ ] **Step 3: Commit**

```bash
git add delta/web/static/index.html
git commit -m "feat(web): sync floating island HUD to static index.html"
```

---

### Task 4: Verification & Smoke Test

**Files:**
- Inspect: `delta/web/index.html`, `delta/web/static/index.html`

- [ ] **Step 1: Verify DOM structure and bindings**

Check that Python web server endpoints and client-side scripts can read/manipulate all header elements without throwing errors:
- `document.getElementById('header-target-badge')` exists
- `document.getElementById('status-indicator-text')` exists
- `document.getElementById('theme-toggle-icon')` exists
- `cycleTheme()` works properly with dark and light modes.

- [ ] **Step 2: Commit final status**

```bash
git status
```
