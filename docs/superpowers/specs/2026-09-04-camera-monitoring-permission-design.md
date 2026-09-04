# Design Specification: Delta Camera Monitoring Permission & WebRTC Remote Streaming

**Date:** 2026-09-04
**Target:** Delta Mobile (Expo Prebuild / EAS Development Build) & Delta Web & Delta Backend Server

---

## 1. Executive Summary & Privacy Tenets
Fitur Camera Monitoring memungkinkan streaming video realtime kamera perangkat Android ke Delta Web.
Prinsip privasi absolut:
1. Tidak ada inisialisasi atau akses kamera tanpa persetujuan eksplisit user.
2. Dialog izin khusus Delta mendahului dialog runtime permission OS Android.
3. Persistent notification & banner indikator visual aktif wajib ditampilkan selama streaming.
4. Penghentian streaming (Stop Monitoring) langsung membubarkan WebRTC track, menutup socket, dan me-revoke session token.

---

## 2. Architecture & Data Flow

```text
[ Delta Mobile ]                              [ Delta Web ]
      │                                             │
      │ 1. POST /api/camera/session/request         │
      │ (deviceId, clientAuth)                      │
      ▼                                             │
[ Signaling / Backend ]                             │
      │ 2. Session created (sessionId, token, ICE)  │
      ├────────────────────────────────────────────►│
      │                                             │ 3. View Camera clicked
      │ 4. WebSocket Signaling Channel              │    Join session
      │◄───────────────────────────────────────────►│
      │                                             │
      │ 5. SDP Offer / Answer & ICE Candidates      │
      │◄═══════════════════════════════════════════►│
      │                                             │
      ▼                                             ▼
[ PeerConnection: Mobile (Sender) ] ───WebRTC───► [ PeerConnection: Web (Viewer) ]
                                (STUN / TURN fallback)
```

---

## 3. Component Breakdown

### A. Delta Mobile
- `app.json`: Tambahkan permissions Android (`CAMERA`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_CAMERA`), dan config plugin `@config-plugins/react-native-webrtc`.
- `useCameraMonitoringStore.ts`: State machine Zustand:
  - `OFFLINE` -> `USER_PERMISSION_REQUIRED` -> `REQUESTING_CAMERA_PERMISSION` -> `CAMERA_READY` -> `CONNECTING` -> `MONITORING` -> `STOPPING` -> `OFFLINE`.
  - Error: `PERMISSION_DENIED`, `CONNECTION_FAILED`, `CAMERA_ERROR`, `SESSION_EXPIRED`.
- `CameraMonitoringPermissionDialog.tsx`: Dialog izin eksplisit Delta berbahasa Indonesia natural.
- `ActiveMonitoringIndicator.tsx`: Persistent UI indicator + tombol "Stop Monitoring".
- `webrtcMonitoringService.ts`: Inisialisasi `react-native-webrtc`, media stream, peer connection, signaling lifecycle, dan Android foreground notification.
- Hapus otomatis streaming diam-diam pada `app/_layout.tsx` dan depresi `autoCameraStreamService.ts`.

### B. Delta Backend & Signaling
- `delta/web/camera_signaling.py`: In-memory session manager:
  - Session metadata: `sessionId`, `deviceId`, `status`, `created_at`, `expires_at`, `offer_sdp`, `answer_sdp`, `candidates`.
  - REST & WebSocket signaling exchange endpoint.
- `delta/web/server.py`:
  - `POST /api/camera/session/init`: Buat session monitoring baru.
  - `POST /api/camera/session/signal`: Exchange SDP & ICE candidate jika melalui HTTP REST polling/fallback.
  - `GET /api/camera/session/status`: Cek status session.
  - `POST /api/camera/session/stop`: Revoke session & stop streaming.

### C. Delta Web
- `delta/web/static/index.html`:
  - Panel Camera Monitoring dengan status live badge, tombol "View Camera", "Stop Monitoring".
  - HTML5 `<video id="remote-video" autoplay playsinline>` terhubung ke WebRTC `RTCPeerConnection` browser standar.
  - Telemetry: resolution, FPS, connection state.

---

## 4. Error & Edge Case Handling
- **Kamera Ditolak Permanen:** Tampilkan dialog arahan buka Pengaturan aplikasi.
- **Koneksi Terputus (WiFi / Data Switch):** State `CONNECTING` (Reconnecting...), ICE restart jika timeout < 15s.
- **User Tekan Stop:** Sesi langsung dicabut, camera track `.stop()` dan dilepas.
