import { useCameraMonitoringStore } from '../src/store/useCameraMonitoringStore';

function assert(condition: boolean, msg: string) {
  if (!condition) {
    throw new Error(`FAIL: ${msg}`);
  }
}

function runTests() {
  console.log('Testing useCameraMonitoringStore state machine...');

  const store = useCameraMonitoringStore;

  // 1. Initial State
  assert(store.getState().status === 'OFFLINE', 'Initial status must be OFFLINE');
  assert(!store.getState().isDialogVisible, 'Dialog must be initially hidden');

  // 2. Request start monitoring -> requires user permission
  store.getState().requestStartMonitoring();
  assert(store.getState().status === 'USER_PERMISSION_REQUIRED', 'Status must be USER_PERMISSION_REQUIRED');
  assert(store.getState().isDialogVisible, 'Dialog must be visible');

  // 3. User grants consent -> transitions to REQUESTING_CAMERA_PERMISSION
  store.getState().grantUserConsent();
  assert(store.getState().status === 'REQUESTING_CAMERA_PERMISSION', 'Status must be REQUESTING_CAMERA_PERMISSION');
  assert(!store.getState().isDialogVisible, 'Dialog must close after consent');

  // 4. Camera permission granted -> CAMERA_READY
  store.getState().onCameraPermissionGranted();
  assert(store.getState().status === 'CAMERA_READY', 'Status must transition to CAMERA_READY');

  // 5. Connect & start monitoring
  store.getState().setConnecting('sess_123');
  assert(store.getState().status === 'CONNECTING', 'Status must be CONNECTING');
  assert(store.getState().sessionId === 'sess_123', 'SessionId must be set');

  store.getState().setMonitoringActive('sess_123');
  assert(store.getState().status === 'MONITORING', 'Status must be MONITORING');
  assert(store.getState().activeSince !== null, 'activeSince timestamp must be recorded');

  // 6. Stop monitoring -> OFFLINE
  store.getState().requestStopMonitoring();
  assert(store.getState().status === 'STOPPING', 'Status must transition to STOPPING');

  store.getState().setOffline();
  assert(store.getState().status === 'OFFLINE', 'Status must be OFFLINE');
  assert(store.getState().sessionId === null, 'SessionId must be cleared');

  // 7. Denial path
  store.getState().requestStartMonitoring();
  store.getState().grantUserConsent();
  store.getState().onCameraPermissionDenied(true);
  assert(store.getState().status === 'ERROR', 'Status must be ERROR');
  assert(store.getState().errorReason === 'PERMISSION_PERMANENTLY_DENIED', 'Error reason must match');

  console.log('PASS: All state machine transitions verified.');
}

runTests();
