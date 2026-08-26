# Delta Web UI Dark & Light Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a toggleable Dark / Light / System theme controller to Delta Web UI with full preference persistence in localStorage and zero Flash of Unstyled Content (FOUC).

**Architecture:** Tailwind CSS `dark:` variant class toggled on the `document.documentElement` (`<html>` element). Inline script initialization in document `<head>` reads `localStorage` or `prefers-color-scheme` media query to set the initial class before layout rendering. Topbar header button renders theme status and handles user interaction.

**Tech Stack:** HTML5, Tailwind CSS, Vanilla JavaScript, Pytest.

## Global Constraints

- Native Tailwind CSS `dark` variant (`darkMode: 'class'`).
- Theme selection values: `'light'`, `'dark'`, `'system'`.
- Default fallback: `'system'`.
- Storage key: `'delta-theme'`.

---

### Task 1: Head Theme Initialization Script & CSS Dark Base

**Files:**
- Modify: `delta/web/static/index.html:1-200`
- Test: `tests/test_web_frontend.py:1-22`

**Interfaces:**
- Consumes: `localStorage.getItem('delta-theme')`, `window.matchMedia('(prefers-color-scheme: dark)')`
- Produces: Class `.dark` on `document.documentElement` if dark theme active.

- [ ] **Step 1: Write the failing test for Theme Head Script presence**

Modify `tests/test_web_frontend.py` to assert that the static HTML includes theme initialization script and dark mode configuration:

```python
def test_web_static_html_has_theme_script():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8997)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8997/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "darkMode: 'class'" in html
            assert "delta-theme" in html
            assert "applyTheme" in html
    finally:
        server.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_frontend.py::test_web_static_html_has_theme_script -v`
Expected: FAIL with `AssertionError: assert "darkMode: 'class'" in html`

- [ ] **Step 3: Implement minimal head script & dark configuration in index.html**

Modify `delta/web/static/index.html`:
1. Configure `darkMode: 'class'` inside `tailwind.config`.
2. Add inline `<script>` in `<head>`:

```html
<script id="tailwind-config">
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: { ... }
    }
  }
</script>
<script>
  (function() {
    function applyTheme() {
      const savedTheme = localStorage.getItem('delta-theme') || 'system';
      const isDark = savedTheme === 'dark' || (savedTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
      if (isDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
    window.applyTheme = applyTheme;
    applyTheme();
  })();
</script>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_frontend.py::test_web_static_html_has_theme_script -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/web/static/index.html tests/test_web_frontend.py
git commit -m "feat(web): add dark mode script and tailwind config in head"
```

---

### Task 2: Header Theme Switcher UI & Handler

**Files:**
- Modify: `delta/web/static/index.html:200-350`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: `window.applyTheme()`
- Produces: `window.setTheme(mode)` JS global function, theme switch button in header topbar.

- [ ] **Step 1: Write the failing test for Header Theme Controller presence**

Add to `tests/test_web_frontend.py`:

```python
def test_web_static_html_has_theme_toggle_button():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8996)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8996/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "id=\"theme-toggle-btn\"" in html
            assert "setTheme(" in html
    finally:
        server.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_frontend.py::test_web_static_html_has_theme_toggle_button -v`
Expected: FAIL with `AssertionError: assert 'id="theme-toggle-btn"' in html`

- [ ] **Step 3: Implement Header Theme Switcher Button & JS Handler**

In `delta/web/static/index.html`:
1. Add button inside Header topbar action buttons group:

```html
<button id="theme-toggle-btn" title="Toggle Theme (Light / Dark / System)" onclick="cycleTheme()" class="hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors duration-150 p-1.5 rounded-lg flex items-center justify-center btn-active-scale">
    <span class="material-symbols-outlined text-[18px]" id="theme-toggle-icon">light_mode</span>
</button>
```

2. Add JS helper function for cycling theme and updating icon:

```javascript
function setTheme(mode) {
    if (mode === 'system') {
        localStorage.removeItem('delta-theme');
    } else {
        localStorage.setItem('delta-theme', mode);
    }
    window.applyTheme();
    updateThemeIcon();
}

function cycleTheme() {
    const current = localStorage.getItem('delta-theme') || 'system';
    const next = current === 'system' ? 'dark' : (current === 'dark' ? 'light' : 'system');
    setTheme(next);
}

function updateThemeIcon() {
    const iconEl = document.getElementById('theme-toggle-icon');
    if (!iconEl) return;
    const theme = localStorage.getItem('delta-theme') || 'system';
    if (theme === 'dark') {
        iconEl.textContent = 'dark_mode';
    } else if (theme === 'light') {
        iconEl.textContent = 'light_mode';
    } else {
        iconEl.textContent = 'desktop_windows';
    }
}
document.addEventListener('DOMContentLoaded', updateThemeIcon);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_frontend.py::test_web_static_html_has_theme_toggle_button -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/web/static/index.html tests/test_web_frontend.py
git commit -m "feat(web): add header theme switcher button and javascript controller"
```

---

### Task 3: Apply Dark Classes to Web UI Components & Layout

**Files:**
- Modify: `delta/web/static/index.html:200-600`
- Test: `tests/test_web_frontend.py`

**Interfaces:**
- Consumes: Tailwind `dark:` classes on `body`, `header`, `aside`, `main`, modal dialogs.
- Produces: Complete dark theme styling for entire workspace.

- [ ] **Step 1: Write failing test for Dark theme class mappings in HTML**

Add to `tests/test_web_frontend.py`:

```python
def test_web_static_html_has_dark_mode_classes():
    server = DeltaWebServer(engine=None, host="127.0.0.1", port=8995)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        req = urllib.request.Request("http://127.0.0.1:8995/")
        with urllib.request.urlopen(req, timeout=2) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "dark:bg-slate-950" in html
            assert "dark:bg-slate-900" in html
            assert "dark:border-slate-800" in html
            assert "dark:text-slate-100" in html
    finally:
        server.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web_frontend.py::test_web_static_html_has_dark_mode_classes -v`
Expected: FAIL with `AssertionError: assert 'dark:bg-slate-950' in html`

- [ ] **Step 3: Update index.html HTML elements with dark: classes**

Add `dark:` classes to key elements in `delta/web/static/index.html`:
- `body`: `dark:bg-slate-950 dark:text-slate-100`
- `header`: `dark:bg-slate-900 dark:border-slate-800`
- `aside`: `dark:bg-slate-900 dark:border-slate-800`
- Sidebar items, cards, modals, input containers: `dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100 dark:hover:bg-slate-800`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web_frontend.py::test_web_static_html_has_dark_mode_classes -v`
Expected: PASS

- [ ] **Step 5: Run all web tests**

Run: `pytest tests/test_web_frontend.py tests/test_web_server.py -v`
Expected: PASS (All tests passing)

- [ ] **Step 6: Commit**

```bash
git add delta/web/static/index.html tests/test_web_frontend.py
git commit -m "feat(web): apply dark theme classes across all workspace components"
```
