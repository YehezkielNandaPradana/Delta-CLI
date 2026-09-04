import { create } from 'zustand';

export type MonitoringStatus =
  | 'OFFLINE'
  | 'USER_PERMISSION_REQUIRED'
  | 'REQUESTING_CAMERA_PERMISSION'
  | 'CAMERA_READY'
  | 'CONNECTING'
  | 'MONITORING'
  | 'STOPPING'
  | 'ERROR';

export type ErrorReason =
  | 'PERMISSION_DENIED'
  | 'PERMISSION_PERMANENTLY_DENIED'
  | 'CONNECTION_FAILED'
  | 'CAMERA_ERROR'
  | 'SESSION_EXPIRED'
  | null;

export interface CameraMonitoringState {
  status: MonitoringStatus;
  errorReason: ErrorReason;
  errorMessage: string | null;
  sessionId: string | null;
  deviceId: string;
  facing: 'back' | 'front';
  isDialogVisible: boolean;
  activeSince: number | null;

  // State transitions
  requestStartMonitoring: () => void;
  grantUserConsent: () => void;
  denyUserConsent: () => void;
  onCameraPermissionGranted: () => void;
  onCameraPermissionDenied: (isPermanent?: boolean) => void;
  setConnecting: (sessionId: string) => void;
  setMonitoringActive: (sessionId: string) => void;
  requestStopMonitoring: () => void;
  setOffline: () => void;
  setError: (reason: ErrorReason, message?: string) => void;
  toggleFacing: () => void;
  dismissDialog: () => void;
}

export const useCameraMonitoringStore = create<CameraMonitoringState>((set) => ({
  status: 'OFFLINE',
  errorReason: null,
  errorMessage: null,
  sessionId: null,
  deviceId: 'Delta-Android-Terminal',
  facing: 'back',
  isDialogVisible: false,
  activeSince: null,

  requestStartMonitoring: () =>
    set((state) => {
      // If already active or requesting, do not re-prompt
      if (state.status === 'MONITORING' || state.status === 'CONNECTING') return state;
      return {
        status: 'USER_PERMISSION_REQUIRED',
        isDialogVisible: true,
        errorReason: null,
        errorMessage: null,
      };
    }),

  grantUserConsent: () =>
    set({
      status: 'REQUESTING_CAMERA_PERMISSION',
      isDialogVisible: false,
    }),

  denyUserConsent: () =>
    set({
      status: 'OFFLINE',
      isDialogVisible: false,
      errorReason: null,
      errorMessage: null,
    }),

  onCameraPermissionGranted: () =>
    set((state) => {
      // State invariant: Only progress to CAMERA_READY if consent was given
      if (state.status !== 'REQUESTING_CAMERA_PERMISSION') return state;
      return {
        status: 'CAMERA_READY',
        errorReason: null,
      };
    }),

  onCameraPermissionDenied: (isPermanent = false) =>
    set({
      status: 'ERROR',
      errorReason: isPermanent ? 'PERMISSION_PERMANENTLY_DENIED' : 'PERMISSION_DENIED',
      errorMessage: isPermanent
        ? 'Izin kamera ditolak secara permanen. Buka Pengaturan untuk mengaktifkannya.'
        : 'Izin kamera diperlukan untuk monitoring.',
      isDialogVisible: false,
    }),

  setConnecting: (sessionId: string) =>
    set({
      status: 'CONNECTING',
      sessionId,
      errorReason: null,
    }),

  setMonitoringActive: (sessionId: string) =>
    set({
      status: 'MONITORING',
      sessionId,
      activeSince: Date.now(),
      errorReason: null,
      errorMessage: null,
    }),

  requestStopMonitoring: () =>
    set({
      status: 'STOPPING',
    }),

  setOffline: () =>
    set({
      status: 'OFFLINE',
      sessionId: null,
      activeSince: null,
      isDialogVisible: false,
      errorReason: null,
      errorMessage: null,
    }),

  setError: (reason: ErrorReason, message?: string) =>
    set({
      status: 'ERROR',
      errorReason: reason,
      errorMessage: message || 'Terjadi kesalahan pada sesi monitoring.',
    }),

  toggleFacing: () =>
    set((state) => ({
      facing: state.facing === 'back' ? 'front' : 'back',
    })),

  dismissDialog: () =>
    set({
      isDialogVisible: false,
    }),
}));
