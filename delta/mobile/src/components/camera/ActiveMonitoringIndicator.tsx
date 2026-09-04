import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useCameraMonitoringStore } from '../../store/useCameraMonitoringStore';
import { webrtcMonitoringService } from '../../services/camera/webrtcMonitoringService';

export const ActiveMonitoringIndicator: React.FC = () => {
  const { status, activeSince, requestStopMonitoring } = useCameraMonitoringStore();
  const [elapsedSec, setElapsedSec] = useState(0);

  const isLive = status === 'MONITORING' || status === 'CONNECTING';

  useEffect(() => {
    if (!isLive || !activeSince) {
      setElapsedSec(0);
      return;
    }

    const interval = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - activeSince) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [isLive, activeSince]);

  if (!isLive) return null;

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <View style={styles.container}>
      <View style={styles.banner}>
        {/* Pulsing indicator dot */}
        <View style={styles.liveIndicator}>
          <View style={[styles.dot, status === 'CONNECTING' ? styles.connectingDot : styles.activeDot]} />
          <Text style={styles.label}>
            {status === 'CONNECTING' ? 'Menghubungkan Kamera...' : 'Camera Monitoring Active'}
          </Text>
        </View>

        {/* Duration counter */}
        {status === 'MONITORING' && (
          <Text style={styles.duration}>{formatTime(elapsedSec)}</Text>
        )}

        {/* Explicit Stop Action */}
        <TouchableOpacity
          style={styles.stopButton}
          onPress={() => {
            webrtcMonitoringService.stopMonitoringSession();
          }}
          activeOpacity={0.8}
        >
          <Ionicons name="stop-circle" size={16} color="#ffffff" />
          <Text style={styles.stopButtonText}>Hentikan</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 50 : 35,
    left: 16,
    right: 16,
    zIndex: 9999,
    alignItems: 'center',
  },
  banner: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: '#0f172a',
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#38bdf8',
    paddingHorizontal: 14,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#0284c7',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 8,
  },
  liveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  activeDot: {
    backgroundColor: '#ef4444',
  },
  connectingDot: {
    backgroundColor: '#f59e0b',
  },
  label: {
    color: '#f8fafc',
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
  duration: {
    color: '#94a3b8',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginRight: 10,
  },
  stopButton: {
    backgroundColor: '#dc2626',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 4,
  },
  stopButtonText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '700',
  },
});
