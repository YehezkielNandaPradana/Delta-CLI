import { useCameraMonitoringStore } from '../src/store/useCameraMonitoringStore';
import { ForegroundCameraNotificationManager } from '../src/services/camera/foregroundNotificationService';

function assert(condition: boolean, msg: string) {
  if (!condition) {
    throw new Error(`FAIL: ${msg}`);
  }
}

function runTests() {
  console.log('--- Unit Testing Phase 1: Foreground Camera Service & Permission Flow ---');

  const store = useCameraMonitoringStore;

  // 1. Initial State
  store.getState().setOffline();
  assert(store.getState().status === 'OFFLINE', 'Initial status must be OFFLINE');

  // 2. User Permission Flow
  store.getState().requestStartMonitoring();
  assert(store.getState().status === 'USER_PERMISSION_REQUIRED', 'Status must be USER_PERMISSION_REQUIRED');

  // User Cancels -> Must return to OFFLINE without any camera call
  store.getState().denyUserConsent();
  assert(store.getState().status === 'OFFLINE', 'Status must return to OFFLINE on denial');

  // User Grants -> Moves to REQUESTING_CAMERA_PERMISSION
  store.getState().requestStartMonitoring();
  store.getState().grantUserConsent();
  assert(store.getState().status === 'REQUESTING_CAMERA_PERMISSION', 'Must transition to REQUESTING_CAMERA_PERMISSION');

  // OS Camera Permission Granted -> CAMERA_READY
  store.getState().onCameraPermissionGranted();
  assert(store.getState().status === 'CAMERA_READY', 'Must transition to CAMERA_READY');

  // Session Connected -> MONITORING
  store.getState().setConnecting('sess_test_foreground');
  store.getState().setMonitoringActive('sess_test_foreground');
  assert(store.getState().status === 'MONITORING', 'Must transition to MONITORING');

  // Verify Notification Manager API signature
  assert(typeof ForegroundCameraNotificationManager.showMonitoringNotification === 'function', 'showMonitoringNotification must exist');
  assert(typeof ForegroundCameraNotificationManager.dismissNotification === 'function', 'dismissNotification must exist');
  assert(typeof ForegroundCameraNotificationManager.registerNotificationActionListener === 'function', 'registerNotificationActionListener must exist');

  // Stopping Monitoring
  store.getState().requestStopMonitoring();
  assert(store.getState().status === 'STOPPING', 'Must transition to STOPPING');

  store.getState().setOffline();
  assert(store.getState().status === 'OFFLINE', 'Must return to OFFLINE');
  assert(store.getState().sessionId === null, 'Session ID must be null');

  console.log('PASS: Phase 1 Unit Test completed successfully.');
}

runTests();
