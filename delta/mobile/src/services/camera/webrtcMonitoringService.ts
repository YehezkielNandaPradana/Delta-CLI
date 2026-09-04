import { Platform, AppState, AppStateStatus, NativeModules, NativeEventEmitter } from 'react-native';
import { useCameraMonitoringStore } from '../../store/useCameraMonitoringStore';
import { useSettingsStore } from '../../store/useSettingsStore';
import { ForegroundCameraNotificationManager } from './foregroundNotificationService';

const { CameraForegroundModule } = NativeModules;

// Safe lazy import of react-native-webrtc for prebuild / dev client
let webrtcModule: any = null;
try {
  webrtcModule = require('react-native-webrtc');
} catch (_) {
  // Gracefully fallback when running under static bundle analyzer or web
}

export class WebRTCMonitoringService {
  private peerConnection: any = null;
  private localStream: any = null;
  private signalPollTimer: any = null;
  private notificationActionUnsub: any = null;
  private nativeStopEventSub: any = null;
  private appStateSubscription: any = null;
  private isRunning: boolean = false;
  private sessionId: string | null = null;
  private serverUrl: string = '';

  /**
   * Acquire camera & media stream with explicit permission check
   */
  async acquireCameraStream(facing: 'back' | 'front' = 'back'): Promise<any> {
    if (!webrtcModule || !webrtcModule.mediaDevices) {
      throw new Error('WebRTC native module tidak tersedia. Jalankan di Android Development Build.');
    }

    const { mediaDevices } = webrtcModule;

    const constraints = {
      audio: false,
      video: {
        facingMode: facing === 'back' ? 'environment' : 'user',
        width: { ideal: 1280 },
        height: { ideal: 720 },
        frameRate: { ideal: 24, max: 30 },
      },
    };

    const stream = await mediaDevices.getUserMedia(constraints);
    this.localStream = stream;
    return stream;
  }

  /**
   * Start a monitoring session connecting to Delta Backend signaling
   */
  async startMonitoringSession(): Promise<boolean> {
    if (this.isRunning) return true;

    const store = useCameraMonitoringStore.getState();
    const settings = useSettingsStore.getState();

    let targetUrl = settings.serverUrl || 'http://192.168.1.6:8000';
    targetUrl = targetUrl.replace(/\/v1\/?$/, '').replace(/\/+$/, '');
    this.serverUrl = targetUrl;

    try {
      store.grantUserConsent();

      // 1. Acquire Camera
      const stream = await this.acquireCameraStream(store.facing);
      store.onCameraPermissionGranted();

      // 2. Request new Monitoring Session from Backend
      const initResp = await fetch(`${this.serverUrl}/api/camera/session/init`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          deviceId: store.deviceId,
          platform: Platform.OS,
          facing: store.facing,
        }),
      });

      if (!initResp.ok) {
        throw new Error(`Gagal membuat sesi monitoring: HTTP ${initResp.status}`);
      }

      const initData = await initResp.json();
      const sessionId = initData.sessionId;
      this.sessionId = sessionId;
      store.setConnecting(sessionId);

      // 3. Initialize RTCPeerConnection with STUN configuration
      const iceServers = initData.iceServers || [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' },
      ];

      const { RTCPeerConnection, RTCSessionDescription, RTCIceCandidate } = webrtcModule;
      this.peerConnection = new RTCPeerConnection({ iceServers });

      // Add camera tracks to peer connection
      stream.getTracks().forEach((track: any) => {
        this.peerConnection.addTrack(track, stream);
      });

      // Handle ICE Candidates generated locally -> send to signaling server
      this.peerConnection.onicecandidate = async (event: any) => {
        if (event.candidate && this.sessionId) {
          try {
            await fetch(`${this.serverUrl}/api/camera/session/signal`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                sessionId: this.sessionId,
                role: 'sender',
                type: 'candidate',
                data: event.candidate,
              }),
            });
          } catch (_) {}
        }
      };

      // Create WebRTC Offer
      const offer = await this.peerConnection.createOffer({
        offerToReceiveVideo: false,
        offerToReceiveAudio: false,
      });

      await this.peerConnection.setLocalDescription(offer);

      // Send Offer to Signaling Server
      await fetch(`${this.serverUrl}/api/camera/session/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: this.sessionId,
          role: 'sender',
          type: 'offer',
          data: offer,
        }),
      });

      this.isRunning = true;
      store.setMonitoringActive(sessionId);

      // 4. Start Native Android Foreground Service (API 34 camera foregroundServiceType)
      if (Platform.OS === 'android' && CameraForegroundModule && CameraForegroundModule.startService) {
        try {
          await CameraForegroundModule.startService();
          const emitter = new NativeEventEmitter(CameraForegroundModule);
          this.nativeStopEventSub = emitter.addListener('onStopRequestedFromNotification', () => {
            this.stopMonitoringSession();
          });
        } catch (_) {}
      }

      // 5. Show Persistent Notification Drawer indicator with interactive 'Hentikan'
      await ForegroundCameraNotificationManager.showMonitoringNotification(store.deviceId);

      // 6. Register notification action listener for 'Hentikan'
      if (this.notificationActionUnsub) this.notificationActionUnsub();
      this.notificationActionUnsub = ForegroundCameraNotificationManager.registerNotificationActionListener(
        () => {
          this.stopMonitoringSession();
        }
      );

      // 7. Start polling for Answer & Remote ICE candidates
      this.startSignalPolling();

      return true;
    } catch (err: any) {
      this.teardown();
      const errMsg = String(err?.message || err || '');
      const isPermissionDenied =
        errMsg.toLowerCase().includes('permission') ||
        errMsg.toLowerCase().includes('notallowed') ||
        errMsg.toLowerCase().includes('denied');

      if (isPermissionDenied) {
        store.onCameraPermissionDenied(false);
      } else {
        store.setError('CAMERA_ERROR', errMsg || 'Gagal memulai monitoring kamera');
      }
      return false;
    }
  }

  /**
   * Poll signaling server for incoming answers and ICE candidates from Delta Web
   */
  private startSignalPolling(): void {
    if (this.signalPollTimer) clearInterval(this.signalPollTimer);

    this.signalPollTimer = setInterval(async () => {
      if (!this.isRunning || !this.sessionId || !this.peerConnection) return;

      try {
        const resp = await fetch(
          `${this.serverUrl}/api/camera/session/signal?sessionId=${this.sessionId}&role=sender`
        );
        if (!resp.ok) return;

        const signals = await resp.json();
        const { RTCSessionDescription, RTCIceCandidate } = webrtcModule;

        for (const sig of signals) {
          if (sig.type === 'answer' && this.peerConnection.signalingState !== 'stable') {
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(sig.data));
          } else if (sig.type === 'candidate' && sig.data) {
            await this.peerConnection.addIceCandidate(new RTCIceCandidate(sig.data));
          } else if (sig.type === 'stop') {
            this.stopMonitoringSession();
          }
        }
      } catch (_) {}
    }, 1500);
  }

  /**
   * Graceful stop and resource teardown
   */
  async stopMonitoringSession(): Promise<void> {
    const store = useCameraMonitoringStore.getState();
    store.requestStopMonitoring();

    if (this.sessionId) {
      try {
        await fetch(`${this.serverUrl}/api/camera/session/stop`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sessionId: this.sessionId }),
        });
      } catch (_) {}
    }

    this.teardown();
    store.setOffline();
  }

  private teardown(): void {
    this.isRunning = false;
    this.sessionId = null;

    if (this.signalPollTimer) {
      clearInterval(this.signalPollTimer);
      this.signalPollTimer = null;
    }

    if (this.notificationActionUnsub) {
      this.notificationActionUnsub();
      this.notificationActionUnsub = null;
    }

    if (this.nativeStopEventSub) {
      this.nativeStopEventSub.remove();
      this.nativeStopEventSub = null;
    }

    // Stop Native Android Foreground Service
    if (Platform.OS === 'android' && CameraForegroundModule && CameraForegroundModule.stopService) {
      try {
        CameraForegroundModule.stopService();
      } catch (_) {}
    }

    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
      this.appStateSubscription = null;
    }

    ForegroundCameraNotificationManager.dismissNotification().catch(() => {});

    if (this.localStream) {
      try {
        this.localStream.getTracks().forEach((t: any) => t.stop());
      } catch (_) {}
      this.localStream = null;
    }

    if (this.peerConnection) {
      try {
        this.peerConnection.close();
      } catch (_) {}
      this.peerConnection = null;
    }
  }
}

export const webrtcMonitoringService = new WebRTCMonitoringService();
