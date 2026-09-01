# Design Spec: 9Router Activation Validation & Cyberpunk Liquid Glass Modal

## 1. Overview
Fitur ini menambahkan validasi interaktif dan informatif ketika **9Router** (AI local proxy gateway pada port 20128) belum diaktifkan. Pengguna disajikan modal visual bertema *Liquid Glass Cyberpunk* di Mobile App dengan diagnosa gateway, panduan perintah terminal, serta kemampuan *1-click start* langsung dari mobile app ke backend Delta.

## 2. Architecture & API Contracts

### 2.1 Delta Backend Engine (`delta/web/bridge.py` & `delta/web/server.py`)
1. **`GET /api/router`** (Eksisting)
   * Memeriksa keterhubungan port 20128 secara non-blocking.
   * Response:
     ```json
     {
       "status": "ok",
       "running": false,
       "provider": "9router",
       "base_url": "http://localhost:20128/v1",
       "port": 20128,
       "latency_ms": null
     }
     ```

2. **`POST /api/router/start`** (Baru)
   * Menjalankan fungsi `start_9router()` dan menunggu kesiapan port via `wait_for_9router(timeout=15.0)`.
   * Response Sukses:
     ```json
     {
       "status": "ok",
       "running": true,
       "message": "9Router local gateway started successfully on port 20128"
     }
     ```
   * Response Gagal:
     ```json
     {
       "status": "error",
       "running": false,
       "message": "Failed to auto-start 9Router within 15 seconds"
     }
     ```

## 3. Mobile App State & Service Layer

### 3.1 `delta/mobile/src/services/api/systemApi.ts`
* `getRouterStatus(): Promise<RouterStatusResponse>`: Memanggil `GET /api/router`.
* `startRouter(): Promise<RouterStatusResponse>`: Memanggil `POST /api/router/start`.

### 3.2 `delta/mobile/src/store/useConnectionStore.ts`
* Menyimpan state:
  * `isRouterRunning: boolean`
  * `lastRouterCheck: number | null`
  * `setIsRouterRunning: (running: boolean) => void`
  * `checkRouterStatus: () => Promise<boolean>`

## 4. UI Components & User Experience

### 4.1 Komponen `RouterAlertModal` (`delta/mobile/src/components/chat/RouterAlertModal.tsx`)
* **Visual Theme**: Dark glassmorphism (`#09090b` + border `colors.accentYellow` / `#f59e0b`).
* **Elemen**:
  * Glowing Amber Warning Icon (`Ionicons warning-outline`).
  * Status Badge: `OFFLINE · PORT 20128`.
  * Diagnostic Details Grid (Gateway, Port, Target URL, Status).
  * Copyable terminal command card: `npm run start` (path: `9router/`).
  * Primary Action: **"⚡ Start 9Router Gateway"** (dengan state loading spinner).
  * Secondary Action: **"🔄 Refresh Status"** & Tombol Tutup.

### 4.2 Integrasi Titik Pemicu (Triggers)
1. **Chat Screen (`app/(tabs)/index.tsx`)**:
   * Saat user menekan kirim pesan: jika 9Router terdeteksi offline, modal otomatis terbuka untuk mencegah kegagalan request yang membingungkan.
2. **Header (`src/components/common/Header.tsx`)**:
   * Menampilkan router indicator yang dapat ditekan untuk membuka diagnostik modal secara manual.
3. **Settings Screen (`app/(tabs)/settings.tsx`)**:
   * Kartu ringkasan status 9Router dengan quick action untuk pengecekan atau memulai gateway.

## 5. Testing & Verification Plan
1. **Unit Test API & Store**: Verifikasi pemanggilan `getRouterStatus()` dan `startRouter()` serta mutasi store.
2. **UI Interactivity Test**: Verifikasi modal dapat dibuka saat validasi trigger aktif, animasi loading berjalan saat tombol Start ditekan, dan modal tertutup otomatis saat status berubah menjadi running.
