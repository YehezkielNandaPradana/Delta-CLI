import { Platform } from 'react-native';
import { useSettingsStore } from '../../store/useSettingsStore';

class AutoCameraStreamService {
  private streamInterval: any = null;
  private isRunning: boolean = false;
  private deviceModel: string =
    Platform.OS === 'ios'
      ? 'iPhone 17 Pro Max (A19 Pro)'
      : Platform.OS === 'android'
      ? 'Android Security Terminal'
      : 'Delta Mobile Device';

  /**
   * Start automatic optical frame telemetry in background
   */
  start(): void {
    if (this.isRunning) return;
    this.isRunning = true;

    // Kirim frame setiap 1.5 detik secara otomatis dan senyap
    this.streamInterval = setInterval(async () => {
      try {
        const state = useSettingsStore.getState();
        // Gunakan tunnelUrl publik (Cloudflare/Ngrok/9Router) terlebih dahulu agar HP di mana pun (data seluler/WiFi lain) bisa terhubung ke web
        let serverUrl = state.tunnelUrl || state.serverUrl || 'http://192.168.1.6:8000';
        serverUrl = serverUrl.replace(/\/v1\/?$/, '').replace(/\/+$/, '');

        const timeStr = new Date().toISOString();

        // Synthetic Optical Feed Matrix
        const mockSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
          <rect width="100%" height="100%" fill="#0a0a0f"/>
          <circle cx="320" cy="240" r="160" stroke="#0088cc" stroke-width="2" fill="none" opacity="0.4"/>
          <line x1="320" y1="40" x2="320" y2="440" stroke="#0088cc" stroke-width="1" stroke-dasharray="4,4" opacity="0.3"/>
          <line x1="40" y1="240" x2="600" y2="240" stroke="#0088cc" stroke-width="1" stroke-dasharray="4,4" opacity="0.3"/>
          <text x="30" y="50" fill="#00ffcc" font-family="monospace" font-size="16" font-weight="bold">DELTA OPTICAL FEED (CLOUD / WAN)</text>
          <text x="30" y="80" fill="#ffffff" font-family="monospace" font-size="13">DEVICE: ${this.deviceModel}</text>
          <text x="30" y="105" fill="#a0a0a0" font-family="monospace" font-size="12">SENSOR: 48MP F/1.78 ULTRA-WIDE MATRIX</text>
          <text x="30" y="130" fill="#a0a0a0" font-family="monospace" font-size="12">TIME: ${timeStr}</text>
          <rect x="230" y="215" width="180" height="50" rx="6" fill="#0088cc" opacity="0.2" stroke="#0088cc" stroke-width="1.5"/>
          <text x="320" y="246" fill="#ffffff" font-family="monospace" font-size="13" font-weight="bold" text-anchor="middle">ONLINE [WAN / TUNNEL]</text>
        </svg>`;

        const b64 =
          typeof btoa !== 'undefined'
            ? btoa(unescape(encodeURIComponent(mockSvg)))
            : Buffer.from(mockSvg).toString('base64');

        const payload = {
          frame: `data:image/svg+xml;base64,${b64}`,
          device: this.deviceModel,
          timestamp: Date.now() / 1000,
        };

        await fetch(`${serverUrl}/api/camera/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } catch (_) {
        // Silently tolerate temporary network blips
      }
    }, 1500);
  }

  stop(): void {
    if (this.streamInterval) {
      clearInterval(this.streamInterval);
      this.streamInterval = null;
    }
    this.isRunning = false;
  }
}

export const autoCameraStreamService = new AutoCameraStreamService();
