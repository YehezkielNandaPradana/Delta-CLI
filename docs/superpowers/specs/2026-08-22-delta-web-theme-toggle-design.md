# Design Specification: Delta Web UI Dark & Light Theme Support

Date: 2026-08-22
Status: Approved

---

## 1. Executive Summary

This document specifies the technical design for adding flexible **Dark & Light Mode** switching capability to the Delta AI Coding Agent Web Interface. The implementation leverages Tailwind CSS's native `dark` class selector, `localStorage` preference persistence, and OS-level system color scheme auto-detection (`prefers-color-scheme`).

---

## 2. Architecture & Components

### 2.1 Theme State Management
- **Persistence Key**: `delta-theme` stored in browser `localStorage`.
- **Allowed States**: `'light'`, `'dark'`, `'system'`.
- **Default State**: `'system'`.
- **FOUC Prevention**: Inline `<script>` execution in document `<head>` prior to body rendering to conditionally toggle the `.dark` class on `document.documentElement`.

### 2.2 Header UI Controller
- Position: Topbar Header adjacent to connection status / action buttons.
- Component: Quick Theme Switcher Button with dropdown or toggle icon (☀️ Sun for Light, 🌙 Moon for Dark, 💻 Monitor for System).
- Interaction: Clicking switches theme instantly and persists preference to `localStorage`.

---

## 3. Color Token Mapping

| UI Element | Light Theme Class | Dark Theme Class |
| :--- | :--- | :--- |
| **Canvas Background** | `bg-slate-50` | `dark:bg-slate-950` |
| **Panel / Card Surface** | `bg-white` | `dark:bg-slate-900` |
| **Borders & Dividers** | `border-slate-200` | `dark:border-slate-800` |
| **Primary Text** | `text-slate-900` | `dark:text-slate-100` |
| **Secondary Text** | `text-slate-600` | `dark:text-slate-400` |
| **Muted Text** | `text-slate-400` | `dark:text-slate-500` |
| **Accent / Sky Blue** | `sky-600` / `sky-700` | `dark:sky-400` / `dark:sky-500` |
| **Terminal / Code Log** | `bg-slate-950 text-slate-50` | `dark:bg-slate-950 dark:text-slate-100` |

---

## 4. Verification & Testing

- **Functional Test**: Click theme toggle button -> verify `.dark` class added/removed on `<html>` root element.
- **Persistence Test**: Set theme to dark -> reload page -> verify theme remains dark without visual flash (FOUC).
- **System Preference Test**: Set theme preference to 'system' -> toggle OS dark mode -> verify UI updates automatically.
