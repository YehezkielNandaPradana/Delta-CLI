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
