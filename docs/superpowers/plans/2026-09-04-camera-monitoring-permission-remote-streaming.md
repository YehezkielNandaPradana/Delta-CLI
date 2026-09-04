# Implementation Plan: Delta Camera Monitoring Permission & Remote WebRTC Streaming

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement explicit Delta permission popup, Android native camera permission flow, WebRTC remote video streaming, signaling session manager, and Delta Web live viewer with strict privacy controls.

**Architecture:** Delta Mobile requests permission via custom dialog -> upon consent requests Android camera permission -> starts WebRTC sender with persistent foreground notification -> exchanges SDP/ICE with Delta Web via Delta Backend signaling endpoints -> Delta Web renders live stream in HTML5 video with telemetry.

**Tech Stack:** React Native (Expo 51 Prebuild / EAS Dev Client), `react-native-webrtc`, Zustand, Python HTTPServer/Signaling, Vanilla JS + WebRTC in Delta Web.

## Global Constraints
- No camera access without explicit Delta dialog + Android system permission.
- No silent background camera streaming.
- Persistent indicators on mobile ("● Camera Monitoring Active" + "Stop Monitoring").
- Mobile and Web do not need to be on same network (STUN/TURN NAT traversal).
- Clean Delta design, no AI slop.

---

### Task 1: Delta Mobile Privacy Cleanup & Dependency/Config Setup

**Files:**
- Modify: `delta/mobile/app/_layout.tsx`
- Modify: `delta/mobile/package.json`
- Modify: `delta/mobile/app.json`
- Modify: `delta/mobile/src/services/camera/autoCameraStreamService.ts`

**Interfaces:**
- Consumes: `useSettingsStore`
- Produces: Clean startup without silent camera access, Android permissions (`CAMERA`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_CAMERA`) in `app.json`.

- [ ] **Step 1: Write test to verify auto camera stream is disabled**
- [ ] **Step 2: Remove autoCameraStreamService.start() from app/_layout.tsx and deactivate silent background loop**
- [ ] **Step 3: Add react-native-webrtc dependency to package.json and config plugins/permissions to app.json**
- [ ] **Step 4: Verify typecheck and syntax**
- [ ] **Step 5: Commit changes**

---

### Task 2: Mobile Camera Monitoring State Machine (Zustand)

**Files:**
- Create: `delta/mobile/src/store/useCameraMonitoringStore.ts`
- Create: `delta/mobile/tests/cameraMonitoringStore.test.ts`

**Interfaces:**
- Produces: `useCameraMonitoringStore` with state:
  - `status`: `'OFFLINE' | 'USER_PERMISSION_REQUIRED' | 'REQUESTING_CAMERA_PERMISSION' | 'CAMERA_READY' | 'CONNECTING' | 'MONITORING' | 'STOPPING' | 'ERROR'`
  - `errorReason`: `'PERMISSION_DENIED' | 'CONNECTION_FAILED' | 'CAMERA_ERROR' | 'SESSION_EXPIRED' | null`
  - `sessionId`: `string | null`
  - `actions`: `requestPermission()`, `grantUserConsent()`, `denyUserConsent()`, `onCameraPermissionGranted()`, `onCameraPermissionDenied()`, `startMonitoring(sessionId)`, `stopMonitoring()`, `setError(reason)`

- [ ] **Step 1: Write unit test for state machine transitions in cameraMonitoringStore.test.ts**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement useCameraMonitoringStore.ts**
- [ ] **Step 4: Run test to verify pass**
- [ ] **Step 5: Commit changes**

---

### Task 3: Camera Monitoring Permission UI Components

**Files:**
- Create: `delta/mobile/src/components/camera/CameraMonitoringPermissionDialog.tsx`
- Create: `delta/mobile/src/components/camera/ActiveMonitoringIndicator.tsx`
- Modify: `delta/mobile/app/(tabs)/index.tsx` or main tab layout to render dialog & persistent indicator

**Interfaces:**
- Consumes: `useCameraMonitoringStore`, `useThemeColors`
- Produces:
  - `CameraMonitoringPermissionDialog`: Explains permission in Indonesian ("Izinkan Delta melakukan monitoring kamera perangkat ini?"), handles [ Batal ] and [ Izinkan ], and provides "Buka Pengaturan" if permanently denied.
  - `ActiveMonitoringIndicator`: Floating persistent pill "● Camera Monitoring Active" with [ Hentikan ] button.

- [ ] **Step 1: Implement CameraMonitoringPermissionDialog.tsx**
- [ ] **Step 2: Implement ActiveMonitoringIndicator.tsx**
- [ ] **Step 3: Integrate components into mobile root/layout**
- [ ] **Step 4: Verify typecheck via tsc**
- [ ] **Step 5: Commit changes**

---

### Task 4: Mobile WebRTC & Signaling Service

**Files:**
- Create: `delta/mobile/src/services/camera/webrtcMonitoringService.ts`

**Interfaces:**
- Consumes: `useCameraMonitoringStore`, `useSettingsStore`
- Produces: `webrtcMonitoringService` with methods:
  - `startMonitoringSession(serverUrl: string): Promise<boolean>`
  - `stopMonitoringSession(): Promise<void>`
  - `switchCamera(): Promise<void>`

- [ ] **Step 1: Write webrtcMonitoringService with RTCPeerConnection and signaling exchange**
- [ ] **Step 2: Add STUN servers (stun:stun.l.google.com:19302) and session token lifecycle**
- [ ] **Step 3: Add teardown logic (stop tracks, close peer connection, notify server)**
- [ ] **Step 4: Typecheck and lint validation**
- [ ] **Step 5: Commit changes**

---

### Task 5: Backend Camera Monitoring Signaling & Session Engine

**Files:**
- Create: `delta/web/camera_signaling.py`
- Modify: `delta/web/server.py`
- Modify: `delta/web/bridge.py`
- Create: `tests/test_camera_signaling.py`

**Interfaces:**
- Produces endpoints:
  - `POST /api/camera/session/init` -> `{ sessionId, token, expiresAt, iceServers }`
  - `POST /api/camera/session/signal` -> Handles `{ sessionId, type: 'offer'|'answer'|'candidate', data }`
  - `GET /api/camera/session/signal?sessionId=xxx&role=viewer|sender` -> Polls pending signals
  - `POST /api/camera/session/stop` -> Revokes session & broadcasts shutdown
  - `GET /api/camera/status` -> Returns live device status, session details

- [ ] **Step 1: Write unit test in tests/test_camera_signaling.py**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement delta/web/camera_signaling.py**
- [ ] **Step 4: Wire endpoints into delta/web/server.py and delta/web/bridge.py**
- [ ] **Step 5: Run tests to verify pass**
- [ ] **Step 6: Commit changes**

---

### Task 6: Delta Web Live Camera Monitoring Interface

**Files:**
- Modify: `delta/web/static/index.html`

**Interfaces:**
- Consumes: `/api/camera/session/*`, WebRTC browser APIs (`RTCPeerConnection`)
- Produces:
  - Devices status card: "● Android Phone - Camera Monitoring: Active"
  - WebRTC HTML5 `<video id="webrtc-camera-video" autoplay playsinline>`
  - Live Telemetry bar: Resolution, FPS counter, RTT latency, WebRTC ICE state
  - "Stop Monitoring" button to terminate remote session
  - User-friendly error banners (no raw stack traces)

- [ ] **Step 1: Update HTML layout for WebRTC video element and device card**
- [ ] **Step 2: Implement client-side WebRTC peer connection & signaling listener**
- [ ] **Step 3: Add telemetry metrics calculations (FPS, resolution, latency)**
- [ ] **Step 4: Add Stop Monitoring handler**
- [ ] **Step 5: Commit changes**

---

### Task 7: End-to-End Verification & Documentation

**Files:**
- Create: `tests/test_camera_monitoring_e2e.py`
- Modify: `delta/mobile/README.md`

- [ ] **Step 1: Write automated integration test verifying session start -> SDP exchange -> stop revocation**
- [ ] **Step 2: Execute python tests and verify 100% pass**
- [ ] **Step 3: Update documentation with instructions for EAS Dev Build / Prebuild**
- [ ] **Step 4: Commit and finalize**
