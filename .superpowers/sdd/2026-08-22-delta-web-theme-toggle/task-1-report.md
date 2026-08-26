# Task 1 Report

## Status
DONE

## Summary of Changes
1. Added `darkMode: 'class'` to `tailwind-config` script in `delta/web/static/index.html`.
2. Added inline `<script>` in `<head>` of `delta/web/static/index.html` to auto-detect theme preference from `localStorage` or `matchMedia` and apply the `.dark` class to `document.documentElement`.
3. Created test `test_web_static_html_has_theme_script` in `tests/test_web_frontend.py`.

## Test Results
`test_web_static_html_has_theme_script`: PASS
