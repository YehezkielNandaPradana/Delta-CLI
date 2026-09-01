# 9Router Activation Validation & Liquid Glass Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build interactive validation & Cyberpunk Liquid Glass Modal in the Mobile App and backend endpoint to detect and 1-click start 9Router on port 20128.

**Architecture:** Backend exposes `POST /api/router/start` in `delta/web/server.py` & `bridge.py` delegating to `delta.utils.router_manager`. Mobile app adds `systemApi.ts` router methods, reactive `useConnectionStore` router state, `RouterAlertModal` component, and attaches validation triggers to chat sending, header, and settings screen.

**Tech Stack:** Python 3.10+, TypeScript, React Native (Expo), Zustand, Ionicons / Feather.

## Global Constraints
- Modern Liquid Glass aesthetic (`#09090b` dark surface with amber/warning glow accents).
- Port 20128 validation check with timeout prevention.
- Non-blocking async start action with loading indicator.

---

### Task 1: Backend Router Start Endpoint (`POST /api/router/start`)

**Files:**
- Modify: `delta/web/bridge.py`
- Modify: `delta/web/server.py`
- Test: `tests/test_router_bridge.py`

**Interfaces:**
- Produces: `EngineBridge.start_router() -> Dict[str, Any]`
- Produces: HTTP endpoint `POST /api/router/start` returning `{"status": "ok", "running": bool, "message": str}`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_router_bridge.py
import pytest
from unittest.mock import patch
from delta.web.bridge import EngineBridge

def test_bridge_start_router_success():
    bridge = EngineBridge(engine=None)
    with patch("delta.utils.router_manager.is_9router_running", side_effect=[False, True]), \
         patch("delta.utils.router_manager.start_9router") as mock_start, \
         patch("delta.utils.router_manager.wait_for_9router", return_value=True):
        res = bridge.start_router()
        assert res["status"] == "ok"
        assert res["running"] is True
        mock_start.assert_called_once()

def test_bridge_start_router_failure():
    bridge = EngineBridge(engine=None)
    with patch("delta.utils.router_manager.is_9router_running", return_value=False), \
         patch("delta.utils.router_manager.start_9router"), \
         patch("delta.utils.router_manager.wait_for_9router", return_value=False):
        res = bridge.start_router()
        assert res["status"] == "error"
        assert res["running"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_router_bridge.py -v`
Expected: FAIL with `AttributeError: 'EngineBridge' object has no attribute 'start_router'`

- [ ] **Step 3: Implement `start_router` in `delta/web/bridge.py` and route in `delta/web/server.py`**

In `delta/web/bridge.py`:
```python
    def start_router(self) -> Dict[str, Any]:
        from delta.utils.router_manager import is_9router_running, start_9router, wait_for_9router
        if is_9router_running():
            return {
                "status": "ok",
                "running": True,
                "message": "9Router is already running on port 20128"
            }
        try:
            start_9router()
            ready = wait_for_9router(timeout=15.0)
            if ready:
                return {
                    "status": "ok",
                    "running": True,
                    "message": "9Router local gateway started successfully on port 20128"
                }
            return {
                "status": "error",
                "running": False,
                "message": "Failed to start 9Router within 15 seconds"
            }
        except Exception as exc:
            return {
                "status": "error",
                "running": False,
                "message": f"Error starting 9Router: {str(exc)}"
            }
```

In `delta/web/server.py` inside `do_POST`:
```python
            if clean_path == "/api/router/start":
                res = self.bridge.start_router() if self.bridge else {"status": "error", "message": "Bridge offline"}
                status_code = 200 if res.get("status") == "ok" else 500
                body = json.dumps(res).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self._safe_write(body)
                return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_router_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/web/bridge.py delta/web/server.py tests/test_router_bridge.py
git commit -m "feat(web): add POST /api/router/start endpoint to bridge"
```

---

### Task 2: Mobile Service & Store Integration (`systemApi.ts` & `useConnectionStore.ts`)

**Files:**
- Modify: `delta/mobile/src/services/api/systemApi.ts`
- Modify: `delta/mobile/src/store/useConnectionStore.ts`
- Test: `delta/mobile/tests/router_store.test.ts`

**Interfaces:**
- Produces: `getRouterStatus() -> Promise<RouterStatusResponse>`
- Produces: `startRouter() -> Promise<RouterStatusResponse>`
- Produces: `useConnectionStore.isRouterRunning`, `setIsRouterRunning`, `checkRouterStatus`

- [ ] **Step 1: Write the failing test**

```typescript
// delta/mobile/tests/router_store.test.ts
import { useConnectionStore } from '../src/store/useConnectionStore';

describe('useConnectionStore - Router State', () => {
  beforeEach(() => {
    useConnectionStore.setState({ isRouterRunning: true });
  });

  it('updates router running status', () => {
    useConnectionStore.getState().setIsRouterRunning(false);
    expect(useConnectionStore.getState().isRouterRunning).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd delta/mobile && npm test tests/router_store.test.ts`
Expected: FAIL (`setIsRouterRunning` not defined)

- [ ] **Step 3: Implement API helpers and store methods**

In `delta/mobile/src/services/api/systemApi.ts`:
```typescript
export interface RouterStatusResponse {
  status: string;
  running: boolean;
  provider: string;
  base_url: string;
  port: number;
  latency_ms?: number | null;
  message?: string;
}

export async function getRouterStatus(): Promise<RouterStatusResponse> {
  return apiRequest<RouterStatusResponse>('/api/router', {
    method: 'GET',
    timeoutMs: 4000,
  });
}

export async function startRouter(): Promise<RouterStatusResponse> {
  return apiRequest<RouterStatusResponse>('/api/router/start', {
    method: 'POST',
    timeoutMs: 20000,
  });
}
```

In `delta/mobile/src/store/useConnectionStore.ts`:
```typescript
interface ConnectionState {
  status: ConnectionStatus;
  isEngineRunning: boolean;
  isRouterRunning: boolean;
  activeTarget: string;
  workingDirectory: string;
  lastPing: number | null;
  errorMessage: string | null;
  setStatus: (status: ConnectionStatus) => void;
  setEngineRunning: (running: boolean) => void;
  setIsRouterRunning: (running: boolean) => void;
  setSystemInfo: (info: { workingDirectory?: string; activeTarget?: string }) => void;
  setLastPing: (timestamp: number) => void;
  setError: (msg: string | null) => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  status: 'disconnected',
  isEngineRunning: false,
  isRouterRunning: true,
  activeTarget: '',
  workingDirectory: '',
  lastPing: null,
  errorMessage: null,

  setStatus: (status: ConnectionStatus) => set({ status, errorMessage: status === 'connected' ? null : undefined }),
  setEngineRunning: (running: boolean) => set({ isEngineRunning: running }),
  setIsRouterRunning: (running: boolean) => set({ isRouterRunning: running }),
  setSystemInfo: (info) =>
    set((state) => ({
      workingDirectory: info.workingDirectory !== undefined ? info.workingDirectory : state.workingDirectory,
      activeTarget: info.activeTarget !== undefined ? info.activeTarget : state.activeTarget,
    })),
  setLastPing: (timestamp: number) => set({ lastPing: timestamp }),
  setError: (msg: string | null) => set({ errorMessage: msg, status: msg ? 'error' : 'disconnected' }),
}));
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd delta/mobile && npm test tests/router_store.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/mobile/src/services/api/systemApi.ts delta/mobile/src/store/useConnectionStore.ts delta/mobile/tests/router_store.test.ts
git commit -m "feat(mobile): add router status API and store state"
```

---

### Task 3: Cyberpunk Liquid Glass Modal (`RouterAlertModal.tsx`)

**Files:**
- Create: `delta/mobile/src/components/chat/RouterAlertModal.tsx`

**Interfaces:**
- Produces: `RouterAlertModal: React.FC<{ visible: boolean; onClose: () => void; onStartSuccess?: () => void }>`

- [ ] **Step 1: Create `RouterAlertModal.tsx`**

```tsx
// delta/mobile/src/components/chat/RouterAlertModal.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ActivityIndicator,
  TouchableWithoutFeedback,
  Alert,
} from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { startRouter, getRouterStatus } from '../../services/api/systemApi';
import { useConnectionStore } from '../../store/useConnectionStore';

interface RouterAlertModalProps {
  visible: boolean;
  onClose: () => void;
  onStartSuccess?: () => void;
}

export const RouterAlertModal: React.FC<RouterAlertModalProps> = ({
  visible,
  onClose,
  onStartSuccess,
}) => {
  const { colors } = useThemeColors();
  const { setIsRouterRunning } = useConnectionStore();
  const [starting, setStarting] = useState(false);
  const [checking, setChecking] = useState(false);

  const handleStartRouter = async () => {
    setStarting(true);
    try {
      const res = await startRouter();
      if (res.running) {
        setIsRouterRunning(true);
        Alert.alert('9Router Active', '9Router local gateway is now online!');
        if (onStartSuccess) onStartSuccess();
        onClose();
      } else {
        Alert.alert('Activation Incomplete', res.message || 'Could not verify port 20128.');
      }
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to start 9router');
    } finally {
      setStarting(false);
    }
  };

  const handleRefresh = async () => {
    setChecking(true);
    try {
      const res = await getRouterStatus();
      setIsRouterRunning(res.running);
      if (res.running) {
        Alert.alert('Online', '9Router is detected active on port 20128.');
        if (onStartSuccess) onStartSuccess();
        onClose();
      } else {
        Alert.alert('Offline', '9Router is still inactive on port 20128.');
      }
    } catch (err: any) {
      Alert.alert('Check Failed', err.message || 'Unable to query router endpoint');
    } finally {
      setChecking(false);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.backdrop}>
          <TouchableWithoutFeedback>
            <View
              style={[
                styles.card,
                {
                  backgroundColor: colors.bgSecondary,
                  borderColor: colors.accentYellow,
                },
              ]}
            >
              {/* Header */}
              <View style={styles.header}>
                <View
                  style={[
                    styles.iconBox,
                    {
                      backgroundColor: colors.accentYellowSubtle,
                      borderColor: colors.accentYellow,
                    },
                  ]}
                >
                  <Ionicons name="warning-outline" size={24} color={colors.accentYellow} />
                </View>
                <View style={styles.headerTextWrap}>
                  <Text style={[styles.title, { color: colors.textPrimary }]}>
                    9Router Belum Aktif
                  </Text>
                  <Text style={[styles.subtitle, { color: colors.textMuted }]}>
                    Local Gateway AI (Port 20128) Tidak Terdeteksi
                  </Text>
                </View>
                <TouchableOpacity onPress={onClose} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                  <Feather name="x" size={20} color={colors.textMuted} />
                </TouchableOpacity>
              </View>

              {/* Diagnostic Box */}
              <View
                style={[
                  styles.diagnosticBox,
                  {
                    backgroundColor: colors.bgPrimary,
                    borderColor: colors.cardBorder,
                  },
                ]}
              >
                <View style={styles.diagRow}>
                  <Text style={[styles.diagLabel, { color: colors.textMuted }]}>Target Gateway</Text>
                  <Text style={[styles.diagValue, { color: colors.accentCyan }]}>http://localhost:20128/v1</Text>
                </View>
                <View style={styles.diagRow}>
                  <Text style={[styles.diagLabel, { color: colors.textMuted }]}>Status Port</Text>
                  <View style={styles.statusBadge}>
                    <View style={[styles.dot, { backgroundColor: colors.accentRed }]} />
                    <Text style={[styles.statusText, { color: colors.accentRed }]}>INACTIVE</Text>
                  </View>
                </View>
                <View style={styles.diagRow}>
                  <Text style={[styles.diagLabel, { color: colors.textMuted }]}>Manual Command</Text>
                  <Text style={[styles.cmdText, { color: colors.textPrimary }]}>npm run start (di /9router)</Text>
                </View>
              </View>

              {/* Actions */}
              <View style={styles.actions}>
                <TouchableOpacity
                  style={[
                    styles.primaryBtn,
                    { backgroundColor: colors.accentYellow },
                    starting && { opacity: 0.7 },
                  ]}
                  onPress={handleStartRouter}
                  disabled={starting || checking}
                >
                  {starting ? (
                    <ActivityIndicator size="small" color="#000" />
                  ) : (
                    <>
                      <Ionicons name="flash" size={16} color="#000" />
                      <Text style={styles.primaryBtnText}>Start 9Router Gateway</Text>
                    </>
                  )}
                </TouchableOpacity>

                <View style={styles.secondaryRow}>
                  <TouchableOpacity
                    style={[
                      styles.secondaryBtn,
                      {
                        backgroundColor: colors.bgPrimary,
                        borderColor: colors.cardBorder,
                      },
                    ]}
                    onPress={handleRefresh}
                    disabled={starting || checking}
                  >
                    {checking ? (
                      <ActivityIndicator size="small" color={colors.textPrimary} />
                    ) : (
                      <>
                        <Ionicons name="refresh" size={15} color={colors.textPrimary} />
                        <Text style={[styles.secondaryBtnText, { color: colors.textPrimary }]}>
                          Cek Kembali
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[
                      styles.secondaryBtn,
                      {
                        backgroundColor: colors.bgPrimary,
                        borderColor: colors.cardBorder,
                      },
                    ]}
                    onPress={onClose}
                  >
                    <Text style={[styles.secondaryBtnText, { color: colors.textMuted }]}>Tutup</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    width: '100%',
    maxWidth: 420,
    borderRadius: 18,
    borderWidth: 1.5,
    padding: 20,
    shadowColor: '#f59e0b',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  headerTextWrap: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  subtitle: {
    fontSize: 11,
    marginTop: 2,
  },
  diagnosticBox: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    marginBottom: 20,
    gap: 8,
  },
  diagRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  diagLabel: {
    fontSize: 11,
    fontWeight: '500',
  },
  diagValue: {
    fontSize: 11,
    fontFamily: 'monospace',
    fontWeight: '600',
  },
  cmdText: {
    fontSize: 11,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '800',
  },
  actions: {
    gap: 10,
  },
  primaryBtn: {
    height: 44,
    borderRadius: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  primaryBtnText: {
    color: '#000',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  secondaryRow: {
    flexDirection: 'row',
    gap: 10,
  },
  secondaryBtn: {
    flex: 1,
    height: 38,
    borderRadius: 9,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  secondaryBtnText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
```

- [ ] **Step 2: Commit**

```bash
git add delta/mobile/src/components/chat/RouterAlertModal.tsx
git commit -m "feat(mobile): add RouterAlertModal component"
```

---

### Task 4: Connect Validation Triggers to Chat Screen, Header & Settings

**Files:**
- Modify: `delta/mobile/app/(tabs)/index.tsx`
- Modify: `delta/mobile/src/components/common/Header.tsx`
- Modify: `delta/mobile/app/(tabs)/settings.tsx`

**Interfaces:**
- Intercepts chat send if `getRouterStatus()` returns `running: false`, opening `RouterAlertModal`.
- Header and Settings provide visual indicator and manual trigger for `RouterAlertModal`.

- [ ] **Step 1: Update `app/(tabs)/index.tsx`**

Integrate `RouterAlertModal` and validate before `sendChatMessage`:
```tsx
  const [showRouterModal, setShowRouterModal] = React.useState(false);
  const [pendingMessage, setPendingMessage] = React.useState<string | null>(null);

  const handleSend = async (text: string) => {
    // Quick validation check
    try {
      const routerStatus = await getRouterStatus();
      if (!routerStatus.running) {
        setPendingMessage(text);
        setShowRouterModal(true);
        return;
      }
    } catch (_) {}

    // proceed normal sendChatMessage
  };
```

- [ ] **Step 2: Update `src/components/common/Header.tsx` & `app/(tabs)/settings.tsx`**

Add router status quick check and trigger button in Settings and Header.

- [ ] **Step 3: Verify TypeScript Compilation & Run Tests**

Run: `cd delta/mobile && npm test`
Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add delta/mobile/app/\(tabs\)/index.tsx delta/mobile/src/components/common/Header.tsx delta/mobile/app/\(tabs\)/settings.tsx
git commit -m "feat(mobile): connect 9router validation triggers and modal to UI"
```
