/**
 * DEPRECATED & NEUTERED: Automatic background camera streaming without explicit user permission
 * is strictly disabled to adhere to Delta Privacy Guidelines.
 * All camera access now strictly routes through `webrtcMonitoringService` and `useCameraMonitoringStore`.
 */
class AutoCameraStreamService {
  start(): void {
    // No-op. Never run unpermitted background streaming.
  }

  stop(): void {
    // No-op.
  }
}

export const autoCameraStreamService = new AutoCameraStreamService();
