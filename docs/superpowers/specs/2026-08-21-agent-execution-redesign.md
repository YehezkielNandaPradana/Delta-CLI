# Spec Design: Agent Execution UI Redesign — Delta Web

- **Date:** 2026-08-21
- **Target File:** `delta/web/index.html`
- **Scope:** Complete presentation redesign of the "Agent Execution" page dashboard in Delta Web UI.

---

## 1. Executive Summary & Goals

Redesign the Delta Web UI "Agent Execution" dashboard to match the aesthetic of modern premium developer tools (Linear, Warp Terminal, Raycast, Vercel).

### Key Improvements
1. **Modern Rounded Aesthetic**: Transition from sharp corners (`0.125rem`/`0.25rem`) to soft modern rounded corners (`rounded-xl` / `12px` for cards & modals; `rounded-lg` / `8px` for buttons, inputs, & sidebar items).
2. **Elevation & Contrast over Heavy Borders**: Replace hard 1px borders with layered background shade depth (`#080A0C` body, `#0E1216` panels, `#13181E` cards, `#161C24` inputs/user cards) and subtle soft shadows (`0 4px 20px -2px rgba(0,0,0,0.5)`).
3. **Consistent Color & Badge System**: Pure single accent primary (`#41D7FA` / `#84E4FF`). Status badges standardisation across ONLINE, RUNNING, SUCCESS, ERROR with dot indicators + transparent tinted pills.
4. **2-Tier Typography**: Sans-serif (`Geist`) for UI labels & conversational prose; Monospace (`JetBrains Mono`) for commands, status codes, terminal outputs, git status, and keyboard shortcuts (`kbd`).
5. **Feed Card Hierarchy**:
   - *System Message:* Muted slate background (`#0F1318`), low visual priority, monospace logs.
   - *User Input/Command:* Visually distinct container (`#161C24`), right-aligned or `$ ` terminal prompt styling.
   - *Agent Response:* Primary focal point (`#13181E`), left accent border (`border-l-4 border-primary`), elevated shadow, badge header.
6. **Micro-interactions & Animations**: Animated dot pulse indicators, hover scale feedback, smooth transition states, active sidebar left-bar glow.
7. **Inspector Panel**: Organized into distinct grouped cards with muted uppercase sub-headers and bright high-contrast values.
8. **Bottom Command Input**: Focal point floating input box with glowing border focus state and inline `[ ↵ send ]` keyboard hints.

---

## 2. Technical Stack & Constraints

- **File**: `delta/web/index.html` (Single-file HTML with embedded Tailwind CSS config & vanilla JavaScript event handlers).
- **Dependencies**: Tailwind CSS CDN (`tailwind.config`), Material Symbols Outlined, Google Fonts (`Geist` & `JetBrains Mono`).
- **Preserved Structure**: 3-column layout (Sidebar, Execution Feed, Inspector Panel), modal system (`command-palette`, `model-modal`, `context-modal`, `attach-modal`, `branch-modal`, `notifications-modal`, `settings-modal`), SSE event stream listeners (`/api/events`), view navigation routing (`files`, `tasks`, `history`, `agents`, `tools`, `mcp`).

---

## 3. UI Component Specifications

### 3.1 Design Tokens (Tailwind Config)
```js
borderRadius: {
  'none': '0px',
  'sm': '0.25rem',  // 4px
  'DEFAULT': '0.5rem', // 8px
  'md': '0.5rem',   // 8px
  'lg': '0.75rem',  // 12px
  'xl': '1rem',     // 16px
  'full': '9999px'
}
```

### 3.2 Left Sidebar Navigation (`w-[240px]`)
- Panel background: `bg-[#0E1216]`
- Brand header: Bold Delta Δ icon + project name + branch switcher pill (`rounded-full`).
- Navigation buttons: `rounded-lg`, hover `bg-[#161C24] text-slate-200`.
- Active button: `bg-primary/10 text-primary font-medium border-l-2 border-primary rounded-lg shadow-sm`.
- Quick Commands & Workspace Group Titles: `text-[10px] font-mono tracking-widest text-slate-500 uppercase font-semibold mt-4 mb-1 px-3`.

### 3.3 Middle Execution Canvas & Feed (`flex-1`)
- Canvas background: `bg-[#080A0C]`
- Header bar: Title "AGENT EXECUTION", status indicator pill (`rounded-full bg-[#12171D] border border-[#1E252D] px-2.5 py-0.5 text-xs text-primary font-mono flex items-center gap-2`).
- Feed items (`#messages-container`):
  - Card rounded corners: `rounded-xl`.
  - User Command: `bg-[#161C24] border border-[#222B35] rounded-xl p-4 shadow-sm`.
  - Agent Response: `bg-[#13181E] border border-[#1E2630] border-l-4 border-l-primary rounded-xl p-4 shadow-md`.
  - System Message: `bg-[#0F1318] border border-[#1A2027] rounded-xl p-3 text-slate-400 font-mono text-xs`.
- Input container: Floating card `rounded-xl border border-[#1F2937] bg-[#0E1216] focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/40 shadow-xl transition-all duration-200`.

### 3.4 Right Inspector Panel (`w-[320px]`)
- Background: `bg-[#0E1216]`
- Grouped sections (`Context`, `Agent Info`, `Session Activity`): Encapsulated inside `rounded-xl bg-[#11161C] border border-[#1A2027] p-3.5 space-y-2.5`.
- Key-Value contrast:
  - Key label: `text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold`.
  - Value: `text-xs font-mono font-medium text-slate-200 bg-[#161C24] px-2 py-1 rounded-md border border-[#222A33]`.

---

## 4. Verification & Testing Criteria

1. Verify layout integrity of 3-column responsiveness on desktop and mobile view.
2. Confirm SSE event updates (`/api/events`) seamlessly update messages, file counts, and task status.
3. Test all modal dialog triggers (⌘K Palette, Model Selector, Context Modal, Branch Selector, Settings).
4. Verify accessibility & text contrast against WCAG AA standards in dark mode.
