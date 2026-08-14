# Delta Web UI Design Specification

**Date:** 2026-08-14  
**Status:** Approved  
**Topic:** Embedded Web Dashboard & Terminal for Delta CLI  

## 1. Overview
Delta Web UI menyediakan antarmuka web modern, clean, dan rapi untuk Delta CLI. Web UI ini terintegrasi langsung dengan Python core Delta tanpa memerlukan dependensi external heavy build step (React/Vue/Node.js).

## 2. Goals
- Menjalankan Web UI melalui perintah `delta web` atau `delta --web`.
- Menyediakan Dashboard visual (system metrics, recent scans, vulnerability summaries).
- Menyediakan Web Terminal interaktif (real-time command execution via WebSocket).
- Menampilkan report hasil scanning secara visual dan interaktif.
- Menggunakan tema cybersecurity modern (Dark Mode, Tailwind CSS, xterm.js).

## 3. Architecture & Components

```
Delta CLI (`delta web`)
 ├── Web Server Engine (`delta/web/server.py` - FastAPI / Starlette / ASGI)
 ├── Core Bridge (`delta/web/bridge.py` - Connects Engine & Session)
 └── Single Page Frontend (`delta/web/static/index.html`)
      ├── Dashboard View (Stats & Metrics)
      ├── Interactive Terminal (xterm.js + WebSocket)
      ├── Target Scanner Form
      └── Report Viewer
```

### 3.1 Backend Modules
1. `delta/web/__init__.py`: Package initialization.
2. `delta/web/server.py`: Server entry point & API endpoints (`/api/status`, `/api/scans`, `/api/reports`, `/ws/terminal`).
3. `delta/web/bridge.py`: Async wrapper memanggil `DeltaEngine` dan mengalirkan stdout/events ke WebSocket.

### 3.2 Frontend Stack
- **HTML5 + Modern JS (VanillaES6)**: Fast loading, low memory overhead.
- **Tailwind CSS (via CDN/Standalone asset)**: Cyberpunk/Dark clean theme (zinc-900 background, emerald-500 accents).
- **xterm.js**: Terminal emulator di browser untuk WebSocket terminal.
- **Chart.js**: Visualisasi statistik vulnerability & scan target.

## 4. API & Communication Spec
- `GET /`: Serves `index.html`.
- `GET /api/status`: Engine status, active sessions, target counts.
- `GET /api/reports`: List generated reports from `reports/`.
- `GET /api/reports/{id}`: Detailed JSON/HTML report.
- `WS /ws/terminal`: Bidirectional terminal stream for running Delta commands (`scan`, `audit`, `ssl`, etc.).

## 5. Security & Isolation
- Server default listen pada `127.0.0.1:8000` (Localhost only) untuk keamanan.
- Parameter Token Optional jika diakses jaringan luar.

## 6. Implementation Plan Reference
- Module directory: `delta/web/`
- CLI Entrypoint integration: `delta/main.py`
