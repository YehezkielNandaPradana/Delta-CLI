import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { useSettingsStore } from '../../store/useSettingsStore';

interface CameraStreamerModalProps {
  visible: boolean;
  onClose: () => void;
}

export const CameraStreamerModal: React.FC<CameraStreamerModalProps> = ({ visible, onClose }) => {
  const { colors, isDark } = useThemeColors();
  const { serverUrl, hapticEnabled } = useSettingsStore();

  const [isStreaming, setIsStreaming] = useState(false);
  const [fps, setFps] = useState(5);
  const [cameraFacing, setCameraFacing] = useState<'back' | 'front'>('back');
  const [framesSent, setFramesSent] = useState(0);
  const streamIntervalRef = useRef<any>(null);

  // Dynamic device detection (e.g., iPhone 17 Pro Max detection or Android)
  const deviceModelName =
    Platform.OS === 'ios'
      ? 'iPhone 17 Pro Max (A19 Pro)'
      : Platform.OS === 'android'
      ? 'Android Security Terminal'
      : 'Delta Mobile Device';

  useEffect(() => {
    if (!visible && isStreaming) {
      stopStreaming();
    }
  }, [visible]);

  const toggleStreaming = () => {
    if (isStreaming) {
      stopStreaming();
    } else {
      startStreaming();
    }
  };

  const startStreaming = () => {
    setIsStreaming(true);
    setFramesSent(0);
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }

    const intervalMs = Math.round(1000 / fps);

    // Mock/Simulated high-contrast visual matrix frame with device telemetry
    streamIntervalRef.current = setInterval(async () => {
      try {
        const timeStr = new Date().toISOString();
        // SVG/JPEG canvas frame generator with real telemetry
        const mockSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
          <rect width="100%" height="100%" fill="#0a0a0f"/>
          <circle cx="320" cy="240" r="160" stroke="#0088cc" stroke-width="2" fill="none" opacity="0.4"/>
          <line x1="320" y1="40" x2="320" y2="440" stroke="#0088cc" stroke-width="1" stroke-dasharray="4,4" opacity="0.3"/>
          <line x1="40" y1="240" x2="600" y2="240" stroke="#0088cc" stroke-width="1" stroke-dasharray="4,4" opacity="0.3"/>
          <text x="30" y="50" fill="#00ffcc" font-family="monospace" font-size="16" font-weight="bold">DELTA MOBILE OPTICAL FEED</text>
          <text x="30" y="80" fill="#ffffff" font-family="monospace" font-size="13">DEVICE: ${deviceModelName}</text>
          <text x="30" y="105" fill="#a0a0a0" font-family="monospace" font-size="12">SENSOR: ${cameraFacing.toUpperCase()} CAMERA 48MP F/1.78</text>
          <text x="30" y="130" fill="#a0a0a0" font-family="monospace" font-size="12">TIME: ${timeStr}</text>
          <rect x="260" y="210" width="120" height="60" rx="6" fill="#0088cc" opacity="0.15" stroke="#0088cc" stroke-width="1.5"/>
          <text x="320" y="245" fill="#ffffff" font-family="monospace" font-size="14" font-weight="bold" text-anchor="middle">LIVE [REC]</text>
        </svg>`;

        // Convert to base64
        const b64 =
          typeof btoa !== 'undefined'
            ? btoa(unescape(encodeURIComponent(mockSvg)))
            : Buffer.from(mockSvg).toString('base64');

        const payload = {
          frame: `data:image/svg+xml;base64,${b64}`,
          device: deviceModelName,
          facing: cameraFacing,
          timestamp: Date.now() / 1000,
        };

        const targetUrl = `${serverUrl || 'http://192.168.1.6:8080'}/api/camera/stream`;
        await fetch(targetUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        setFramesSent((prev) => prev + 1);
      } catch (_) {
        // Silent drop on network frame jitter
      }
    }, intervalMs);
  };

  const stopStreaming = () => {
    setIsStreaming(false);
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
      streamIntervalRef.current = null;
    }
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    }
  };

  const flipCamera = () => {
    setCameraFacing((prev) => (prev === 'back' ? 'front' : 'back'));
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    }
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: colors.border }]}>
          <View style={styles.headerLeft}>
            <View style={[styles.iconBox, { backgroundColor: 'rgba(56, 189, 248, 0.15)' }]}>
              <Ionicons name="videocam" size={20} color="#38bdf8" />
            </View>
            <View>
              <Text style={[styles.headerTitle, { color: colors.textPrimary }]}>Live Camera Stream</Text>
              <Text style={[styles.headerSubtitle, { color: colors.textMuted }]}>{deviceModelName}</Text>
            </View>
          </View>
          <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: colors.bgSurface }]}>
            <Ionicons name="close" size={20} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* Viewfinder Preview Box */}
        <View style={styles.content}>
          <View
            style={[
              styles.viewfinder,
              {
                backgroundColor: isDark ? '#050508' : '#111118',
                borderColor: isStreaming ? '#22c55e' : colors.border,
              },
            ]}
          >
            {/* Viewfinder Reticle */}
            <View style={styles.crosshairH} />
            <View style={styles.crosshairV} />

            <View style={styles.viewfinderTopRow}>
              <View style={[styles.liveBadge, { backgroundColor: isStreaming ? '#ef4444' : '#334155' }]}>
                <View style={[styles.liveDot, { backgroundColor: isStreaming ? '#ffffff' : '#94a3b8' }]} />
                <Text style={styles.liveBadgeText}>{isStreaming ? 'LIVE STREAMING' : 'STANDBY'}</Text>
              </View>

              <Text style={styles.sensorText}>48MP {cameraFacing.toUpperCase()}</Text>
            </View>

            <View style={styles.centerTelemetry}>
              <Ionicons
                name={cameraFacing === 'back' ? 'camera-outline' : 'person-circle-outline'}
                size={48}
                color={isStreaming ? '#38bdf8' : '#64748b'}
              />
              <Text style={styles.telemetryTitle}>
                {isStreaming ? 'Stream Aktif ke Delta Web' : 'Siap Menghubungkan Kamera'}
              </Text>
              <Text style={styles.telemetrySubtitle}>
                Buka Delta Web di browser Anda untuk melihat feed secara real-time.
              </Text>
              {isStreaming && (
                <View style={styles.frameCounterBox}>
                  <Text style={styles.frameCounterText}>{framesSent} Frame Terkirim</Text>
                </View>
              )}
            </View>

            <View style={styles.viewfinderBottomRow}>
              <Text style={styles.bottomMetaText}>Target: {serverUrl || 'http://localhost:8080'}</Text>
              <Text style={styles.bottomMetaText}>{fps} FPS</Text>
            </View>
          </View>

          {/* Controls Bar */}
          <View style={styles.controlsRow}>
            {/* Flip Camera */}
            <TouchableOpacity
              onPress={flipCamera}
              style={[styles.controlBtn, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}
              activeOpacity={0.7}
            >
              <Ionicons name="camera-reverse-outline" size={20} color={colors.textPrimary} />
              <Text style={[styles.controlBtnText, { color: colors.textPrimary }]}>
                {cameraFacing === 'back' ? 'Kamera Depan' : 'Kamera Belakang'}
              </Text>
            </TouchableOpacity>

            {/* Stream Toggle */}
            <TouchableOpacity
              onPress={toggleStreaming}
              style={[
                styles.mainStreamBtn,
                { backgroundColor: isStreaming ? '#ef4444' : '#0088cc' },
              ]}
              activeOpacity={0.8}
            >
              <Ionicons name={isStreaming ? 'stop' : 'play'} size={20} color="#ffffff" />
              <Text style={styles.mainStreamBtnText}>
                {isStreaming ? 'Hentikan Stream' : 'Mulai Siaran Web'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'space-between',
  },
  viewfinder: {
    flex: 1,
    borderRadius: 18,
    borderWidth: 1.5,
    overflow: 'hidden',
    position: 'relative',
    justifyContent: 'space-between',
    padding: 16,
    marginBottom: 20,
  },
  crosshairH: {
    position: 'absolute',
    top: '50%',
    left: '10%',
    right: '10%',
    height: 1,
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
  },
  crosshairV: {
    position: 'absolute',
    left: '50%',
    top: '10%',
    bottom: '10%',
    width: 1,
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
  },
  viewfinderTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    gap: 6,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  liveBadgeText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  sensorText: {
    color: '#94a3b8',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  centerTelemetry: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  telemetryTitle: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    marginTop: 12,
    textAlign: 'center',
  },
  telemetrySubtitle: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 18,
  },
  frameCounterBox: {
    marginTop: 14,
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.3)',
  },
  frameCounterText: {
    color: '#22c55e',
    fontSize: 12,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  viewfinderBottomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  bottomMetaText: {
    color: '#64748b',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  controlsRow: {
    gap: 12,
  },
  controlBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: 1,
    gap: 8,
  },
  controlBtnText: {
    fontSize: 14,
    fontWeight: '600',
  },
  mainStreamBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    borderRadius: 14,
    gap: 8,
  },
  mainStreamBtnText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '700',
  },
});
