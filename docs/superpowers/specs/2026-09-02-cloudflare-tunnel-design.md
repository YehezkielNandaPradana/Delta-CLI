# Delta Cloudflare Quick Tunnel Integration Design Specification

## 1. Overview & Objective
Memungkinkan pengguna menjalankan Delta Web Server / Gateway di PC / Termux secara lokal, lalu secara otomatis membuat Secure HTTPS Public URL via **Cloudflare Quick Tunnel** (`https://*.trycloudflare.com`) tanpa perlu konfigurasi port forwarding, IP publik, atau akun Cloudflare. 

Aplikasi Mobile Delta dapat langsung terhubung ke server Delta dan 9Router dari mana saja via internet.

---

## 2. Architecture & Components

```
[ Delta Mobile App ] (Anywhere / 4G / Wi-Fi)
        │
        ▼ HTTPS / SSE
[ Cloudflare Edge Network ]
        │
        ▼ Secure Encrypted Tunnel (cloudflared)
[ Local PC / Termux ]
   ├── cloudflared tunnel (auto-spawned binary / subprocess)
   ├── Delta Web API Server (Port 8080)
   └── 9Router AI Gateway (Port 20128)
```

### 2.1 Backend Subsystem (`delta/utils/tunnel_manager.py`)
- **Binary Detection & Auto-Download**:
  - Cek ketersediaan binary `cloudflared` (PATH atau di cache direktori Delta `.delta/bin/`).
  - Jika belum ada, sediakan helper auto-download binary resmi Cloudflare sesuai platform (Windows x64, Linux ARM/x64, Termux, MacOS).
- **Tunnel Lifecycle Controller**:
  - Command: `delta tunnel start [--port 8080]` atau integrasi otomatis saat `delta web start --tunnel`.
  - Membaca stdout/stderr stream `cloudflared tunnel --url http://127.0.0.1:8080` untuk mengekstrak URL publik `https://<random-id>.trycloudflare.com`.
  - Menyimpan URL publik aktif ke runtime bridge dan status API (`/api/status` & `/api/tunnel`).

### 2.2 CLI Commands
- `delta tunnel start` : Menjalankan tunnel untuk Delta Web Server.
- `delta tunnel stop` : Menghentikan tunnel aktif.
- `delta tunnel status` : Menampilkan URL publik aktif & QR Code di terminal.
- `delta web --tunnel` : Menjalankan web server langsung bersamaan dengan Cloudflare tunnel.

### 2.3 Mobile App Connection UI (`delta/mobile`)
- **Settings Screen**:
  - Menambahkan opsi koneksi baru: **Cloudflare Tunnel (Remote Online)**.
  - Input field untuk memasukkan URL `https://*.trycloudflare.com` dengan validasi latency otomatis.
  - Opsi simpan URL tunnel ke `AsyncStorage`.
- **Auto-Routing Engine**:
  - `embeddedRouterEngine` dan `apiClient` mengarahkan request REST API & SSE events ke endpoint Cloudflare jika mode tunnel aktif.

---

## 3. Security & Access Control
- **CORS & Headers**: Delta HTTP server sudah mendukung CORS wildcard (`*`) dan streaming chunked SSE headers.
- **Session Auth**: Jika `auth_enabled: true` di konfigurasi Delta, seluruh request via tunnel wajib menyertakan credential atau API token.

---

## 4. Error Handling & Recovery
- **Tunnel Disconnect**: Otomatis mendeteksi proses `cloudflared` yang terminate dan melakukan restart jika diminta.
- **Mobile Reconnect**: Mobile app menerapkan retry exponential backoff pada SSE connection (`/api/events`) saat jaringan seluler berganti IP.
