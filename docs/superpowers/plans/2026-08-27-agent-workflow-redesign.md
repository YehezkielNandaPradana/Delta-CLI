# Agent Workflow & Live Pipeline UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Delta's Agent Workflow / Pipeline execution component into a modern Cyber Glass HUD with tree connector hierarchy, live telemetry bar, glowing radar status pills, and interactive collapsible tool output drawers.

**Architecture:** Update the frontend event renderer and template in `delta/web/static/index.html` (and mirror `delta/web/index.html`) to structure execution turns with Cyber Glass container styling, telemetry headers with live duration/tokens counters, step tree nodes with expand/collapse capability for tool details, and smooth micro-animations. Complement with alignment in `delta/ai/cli_renderer.py` for terminal parity.

**Tech Stack:** HTML5, Tailwind CSS, JavaScript (Vanilla ES6+), Python 3.10+ (CLI renderer & pytest).

## Global Constraints

- Preserve all existing event bus subscriptions and message streaming functionality (`agent_start`, `agent_thinking`, `tool_start`, `tool_result`, `file_update`, `message_delta`).
- Maintain dark/light mode compatibility using Tailwind zinc/indigo/emerald tokens.
- No external heavy frontend frameworks; keep single-file self-contained vanilla JS in `index.html`.
- Full backward compatibility with existing tests in `tests/test_web_frontend.py` and `tests/test_agent_events.py`.

---

### Task 1: Add Cyber Glass Card & Shimmer Keyframes CSS

**Files:**
- Modify: `delta/web/static/index.html:80-190`
- Modify: `delta/web/index.html:80-190`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: Tailwind CSS base stylesheet
- Produces: CSS animation utility classes (`animate-radar-pulse`, `animate-shimmer-fast`, `animate-step-enter`, `connector-line`)

- [ ] **Step 1: Write test checking for new CSS classes in web templates**

Add test in `tests/test_web_frontend.py`:
```python
def test_workflow_cyber_glass_css_classes():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "animate-radar-pulse" in static_html
    assert "connector-line" in static_html
    assert "cyber-glass" in static_html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_frontend.py -k test_workflow_cyber_glass_css_classes -v`
Expected: FAIL

- [ ] **Step 3: Implement CSS styling & keyframes in `delta/web/static/index.html` and `delta/web/index.html`**

Add styling to `<style>` block:
```css
        @keyframes radarPulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7); }
            70% { transform: scale(1.05); box-shadow: 0 0 0 6px rgba(99, 102, 241, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
        }
        .animate-radar-pulse {
            animation: radarPulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .cyber-glass {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }
        .dark .cyber-glass {
            background: rgba(9, 9, 11, 0.80);
        }

        .connector-line {
            position: relative;
        }
        .connector-line::before {
            content: '';
            position: absolute;
            left: 17px;
            top: 24px;
            bottom: 0;
            width: 2px;
            background: rgba(99, 102, 241, 0.2);
        }
        .dark .connector-line::before {
            background: rgba(99, 102, 241, 0.25);
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_web_frontend.py -k test_workflow_cyber_glass_css_classes -v`
Expected: PASS

---

### Task 2: Redesign `getOrCreateTurnContainer` with Cyber Glass Header & Telemetry Bar

**Files:**
- Modify: `delta/web/static/index.html:995-1045`
- Modify: `delta/web/index.html:995-1045`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: `execId: string`
- Produces: DOM structure containing `timeline-box-${execId}`, `timeline-badge-${execId}`, `timeline-progress-${execId}`, `timeline-stats-${execId}`, `timeline-steps-${execId}`

- [ ] **Step 1: Write test verifying DOM structure of Turn Container**

Add test in `tests/test_web_frontend.py`:
```python
def test_workflow_turn_container_structure():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "DELTA AGENT PIPELINE" in static_html
    assert "timeline-progress-" in static_html
    assert "timeline-steps-" in static_html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_frontend.py -k test_workflow_turn_container_structure -v`
Expected: FAIL

- [ ] **Step 3: Update `getOrCreateTurnContainer` in HTML templates**

Replace template in `getOrCreateTurnContainer`:
```javascript
function getOrCreateTurnContainer(execId) {
    const turnId = `turn-${execId}`;
    let turnEl = document.getElementById(turnId);
    if (!turnEl) {
        const html = `
            <div id="${turnId}" class="flex flex-col gap-3 w-full animate-fade-in">
                <div id="timeline-box-${execId}" class="w-full cyber-glass border border-indigo-500/25 dark:border-indigo-500/20 rounded-2xl p-4 space-y-3 transition-base shadow-lg shadow-indigo-500/5 hover:border-indigo-500/40 relative overflow-hidden">
                    <!-- Top subtle ambient gradient line -->
                    <div class="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500/40 via-sky-500/30 to-transparent"></div>
                    
                    <!-- Header Bar -->
                    <div class="flex items-center justify-between border-b border-zinc-200/60 dark:border-zinc-800/80 pb-2.5">
                        <div class="flex items-center gap-2.5">
                            <div class="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-radar-pulse" id="timeline-dot-${execId}"></div>
                            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 tracking-wider flex items-center gap-2" id="timeline-header-${execId}">
                                <span>DELTA AGENT PIPELINE</span>
                                <span class="text-[10px] font-mono text-zinc-400 font-normal px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800/70 border border-zinc-200/60 dark:border-zinc-700/60">${execId}</span>
                            </span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 font-semibold px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/30 flex items-center gap-1.5 shadow-sm" id="timeline-badge-${execId}">
                                <span class="material-symbols-outlined text-[13px] animate-spin-slow">progress_activity</span> RUNNING
                            </span>
                        </div>
                    </div>

                    <!-- Telemetry Progress Strip -->
                    <div class="w-full space-y-1.5">
                        <div class="w-full h-1 bg-zinc-100 dark:bg-zinc-800/80 rounded-full overflow-hidden">
                            <div id="timeline-progress-${execId}" class="h-full bg-gradient-to-r from-indigo-500 to-sky-500 animate-shimmer w-full transition-all duration-300"></div>
                        </div>
                        <div class="flex items-center justify-between text-[10px] font-mono text-zinc-400 dark:text-zinc-500 px-0.5" id="timeline-stats-${execId}">
                            <span id="stat-time-${execId}" class="flex items-center gap-1">⏱️ <span class="text-zinc-600 dark:text-zinc-300 font-medium">0.0s</span></span>
                            <span id="stat-steps-${execId}" class="flex items-center gap-1">⚡ <span class="text-zinc-600 dark:text-zinc-300 font-medium">1 step</span></span>
                            <span id="stat-tokens-${execId}" class="flex items-center gap-1">🧠 <span class="text-zinc-600 dark:text-zinc-300 font-medium">0 tok</span></span>
                        </div>
                    </div>

                    <!-- Step Tree connector container -->
                    <div class="timeline-steps connector-line space-y-2 pt-1" id="timeline-steps-${execId}">
                        <!-- Step items will enter here -->
                    </div>
                </div>

                <!-- Assistant Response Bubble -->
                <div id="assistant-bubble-${execId}" class="hidden w-full animate-response-enter">
                    <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 border-l-4 border-indigo-500 rounded-xl p-4 shadow-sm w-full space-y-2">
                        <div class="flex items-center justify-between text-[10px] font-mono border-b border-zinc-100 dark:border-zinc-800 pb-1.5 mb-2 gap-4">
                            <span class="text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-1.5">
                                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> DELTA ASSISTANT
                            </span>
                            <span class="text-zinc-400" id="assistant-time-${execId}">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <div class="text-sm leading-relaxed font-mono whitespace-pre-wrap text-zinc-800 dark:text-zinc-200 msg-content" id="msg-content-${execId}"></div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
        turnEl = document.getElementById(turnId);
        smartScrollToBottom();
    }
    return turnEl;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_web_frontend.py -k test_workflow_turn_container_structure -v`
Expected: PASS

---

### Task 3: Implement Step Tree Node & Collapsible Tool Output Drawer

**Files:**
- Modify: `delta/web/static/index.html:1075-1150`
- Modify: `delta/web/index.html:1075-1150`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: `addOrUpdateProcessStep(execId, stepKey, title, status, detail, durationMs, outputData)`
- Produces: Interactive DOM node with toggle drawer `toggleStepDrawer(stepId)` and styled badges

- [ ] **Step 1: Write test verifying drawer and step tree renderer in frontend script**

Add test in `tests/test_web_frontend.py`:
```python
def test_workflow_step_drawer_functions():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "toggleStepDrawer" in static_html
    assert "step-drawer-" in static_html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_web_frontend.py -k test_workflow_step_drawer_functions -v`
Expected: FAIL

- [ ] **Step 3: Update `addOrUpdateProcessStep` and add `toggleStepDrawer` in templates**

```javascript
window.toggleStepDrawer = function(drawerId) {
    const drawer = document.getElementById(drawerId);
    const icon = document.getElementById(`icon-${drawerId}`);
    if (drawer) {
        drawer.classList.toggle('hidden');
        if (icon) {
            icon.classList.toggle('rotate-180');
        }
    }
};

function addOrUpdateProcessStep(execId, stepKey, title, status = 'running', detail = '', durationMs = null, outputData = null) {
    getOrCreateTurnContainer(execId);
    const stepsContainer = document.getElementById(`timeline-steps-${execId}`);
    if (!stepsContainer) return;

    let stepEl = document.getElementById(`step-${execId}-${stepKey}`);
    const drawerId = `drawer-${execId}-${stepKey}`;

    let statusIconHtml = '';
    if (status === 'running') {
        statusIconHtml = `<span class="material-symbols-outlined text-[15px] text-indigo-500 animate-spin-slow">progress_activity</span>`;
    } else if (status === 'success') {
        statusIconHtml = `<span class="material-symbols-outlined text-[15px] text-emerald-500 font-semibold">check_circle</span>`;
    } else if (status === 'error') {
        statusIconHtml = `<span class="material-symbols-outlined text-[15px] text-red-500 font-semibold">cancel</span>`;
    } else {
        statusIconHtml = `<span class="material-symbols-outlined text-[15px] text-zinc-400">radio_button_unchecked</span>`;
    }

    const durationBadge = durationMs !== null ? `<span class="text-[10px] font-mono text-zinc-400 font-normal ml-auto">${Math.round(durationMs)}ms</span>` : '';
    const hasOutput = outputData && String(outputData).trim().length > 0;
    const expandBtnHtml = hasOutput ? `
        <button onclick="toggleStepDrawer('${drawerId}')" class="p-1 hover:bg-zinc-200/50 dark:hover:bg-zinc-700/50 rounded transition-transform text-zinc-400 hover:text-zinc-200">
            <span id="icon-${drawerId}" class="material-symbols-outlined text-[14px] transition-transform duration-200">expand_more</span>
        </button>
    ` : '';

    if (!stepEl) {
        const stepHtml = `
            <div id="step-${execId}-${stepKey}" class="flex flex-col gap-1 text-xs animate-process-enter transition-base group">
                <div class="flex items-center justify-between py-1.5 px-3 rounded-xl bg-zinc-100/70 dark:bg-zinc-900/60 border border-zinc-200/60 dark:border-zinc-800/80 hover:border-indigo-500/30 transition-base">
                    <div class="flex items-center gap-2.5 min-w-0 flex-1">
                        <span class="step-status-icon flex items-center justify-center shrink-0">${statusIconHtml}</span>
                        <span class="step-title font-medium text-zinc-800 dark:text-zinc-200 truncate text-[12px]">${escapeHtml(title)}</span>
                        ${detail ? `<span class="step-detail text-[10px] font-mono text-indigo-500 dark:text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded truncate max-w-[220px]">${escapeHtml(detail)}</span>` : ''}
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                        <div class="step-duration flex items-center">${durationBadge}</div>
                        ${expandBtnHtml}
                    </div>
                </div>
                ${hasOutput ? `
                    <div id="${drawerId}" class="hidden ml-7 mr-1 p-2.5 rounded-lg bg-zinc-950 border border-zinc-800 text-[11px] font-mono text-zinc-300 overflow-x-auto whitespace-pre-wrap max-h-48 scrollbar-thin">
                        ${escapeHtml(String(outputData))}
                    </div>
                ` : ''}
            </div>
        `;
        stepsContainer.insertAdjacentHTML('beforeend', stepHtml);
    } else {
        const iconContainer = stepEl.querySelector('.step-status-icon');
        if (iconContainer) iconContainer.innerHTML = statusIconHtml;
        const titleContainer = stepEl.querySelector('.step-title');
        if (titleContainer && title) titleContainer.textContent = title;
        const durationContainer = stepEl.querySelector('.step-duration');
        if (durationContainer && durationBadge) durationContainer.innerHTML = durationBadge;
    }

    // Update step count in telemetry strip
    const stepsCount = stepsContainer.children.length;
    const statSteps = document.getElementById(`stat-steps-${execId}`);
    if (statSteps) {
        statSteps.innerHTML = `⚡ <span class="text-zinc-600 dark:text-zinc-300 font-medium">${stepsCount} step${stepsCount > 1 ? 's' : ''}</span>`;
    }

    smartScrollToBottom();
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_web_frontend.py -k test_workflow_step_drawer_functions -v`
Expected: PASS

---

### Task 4: Telemetry Finalizer & Completion Transitions

**Files:**
- Modify: `delta/web/static/index.html:1120-1160`
- Modify: `delta/web/index.html:1120-1160`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: `finalizeTimelineSuccess(execId)`
- Produces: Completed badge pill (`DONE`), static 100% emerald progress bar, total duration calculation

- [ ] **Step 1: Write test verifying `finalizeTimelineSuccess` updates**

Add test in `tests/test_web_frontend.py`:
```python
def test_workflow_finalize_success_logic():
    from pathlib import Path
    static_html = Path("delta/web/static/index.html").read_text(encoding="utf-8")
    assert "finalizeTimelineSuccess" in static_html
    assert "bg-emerald-500" in static_html
```

- [ ] **Step 2: Run test to verify it passes or fails**

Run: `python -m pytest tests/test_web_frontend.py -k test_workflow_finalize_success_logic -v`
Expected: FAIL / PASS depending on initial state

- [ ] **Step 3: Update `finalizeTimelineSuccess` implementation**

```javascript
function finalizeTimelineSuccess(execId) {
    const badgeEl = document.getElementById(`timeline-badge-${execId}`);
    if (badgeEl) {
        badgeEl.className = "text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 flex items-center gap-1.5 shadow-sm";
        badgeEl.innerHTML = `<span class="material-symbols-outlined text-[13px] font-bold">check</span> COMPLETED`;
    }
    const dotEl = document.getElementById(`timeline-dot-${execId}`);
    if (dotEl) {
        dotEl.className = "w-2.5 h-2.5 rounded-full bg-emerald-500";
    }
    const progressEl = document.getElementById(`timeline-progress-${execId}`);
    if (progressEl) {
        progressEl.className = "h-full bg-emerald-500 w-full transition-all duration-500";
    }
    const runningIcons = document.querySelectorAll(`#timeline-steps-${execId} .animate-spin-slow`);
    runningIcons.forEach(icon => {
        icon.parentElement.innerHTML = `<span class="material-symbols-outlined text-[15px] text-emerald-500 font-semibold">check_circle</span>`;
    });
}
```

- [ ] **Step 4: Run full frontend test suite**

Run: `python -m pytest tests/test_web_frontend.py -v`
Expected: ALL PASS

---

### Task 5: Full Regression Testing & Verification

**Files:**
- Test: `tests/test_web_frontend.py`
- Test: `tests/test_agent_events.py`
- Test: `tests/test_cli_web_integration.py`

- [ ] **Step 1: Run all test suites**

Run: `python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Verify both `delta/web/static/index.html` and `delta/web/index.html` are synchronized**

Run: `python -c "import filecmp; print('In sync:', filecmp.cmp('delta/web/static/index.html', 'delta/web/index.html'))"`
Expected: `In sync: True`
