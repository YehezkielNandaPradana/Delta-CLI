import React from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Linking,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useCameraMonitoringStore } from '../../store/useCameraMonitoringStore';
import { webrtcMonitoringService } from '../../services/camera/webrtcMonitoringService';
import { useThemeColors } from '../../theme/theme';

export const CameraMonitoringPermissionDialog: React.FC = () => {
  const { colors, isDark } = useThemeColors();
  const {
    isDialogVisible,
    errorReason,
    errorMessage,
    status,
    grantUserConsent,
    denyUserConsent,
    requestStartMonitoring,
    dismissDialog,
  } = useCameraMonitoringStore();

  const isPermissionError =
    status === 'ERROR' &&
    (errorReason === 'PERMISSION_DENIED' || errorReason === 'PERMISSION_PERMANENTLY_DENIED');

  const visible = isDialogVisible || isPermissionError;

  if (!visible) return null;

  const handleOpenSettings = () => {
    if (Platform.OS === 'android' || Platform.OS === 'ios') {
      Linking.openSettings();
    }
    dismissDialog();
  };

  return (
    <Modal
      transparent
      animationType="fade"
      visible={visible}
      onRequestClose={denyUserConsent}
    >
      <View style={styles.overlay}>
        <View
          style={[
            styles.card,
            {
              backgroundColor: isDark ? '#121217' : '#ffffff',
              borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
            },
          ]}
        >
          {/* Header Icon */}
          <View
            style={[
              styles.iconWrapper,
              {
                backgroundColor: isPermissionError
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(56, 189, 248, 0.15)',
              },
            ]}
          >
            <Ionicons
              name={isPermissionError ? 'alert-circle-outline' : 'videocam-outline'}
              size={28}
              color={isPermissionError ? '#ef4444' : '#38bdf8'}
            />
          </View>

          {/* Title */}
          <Text style={[styles.title, { color: colors.textPrimary }]}>
            {isPermissionError ? 'Izin Kamera Diperlukan' : 'Camera Monitoring'}
          </Text>

          {/* Content Description */}
          {isPermissionError ? (
            <View style={styles.body}>
              <Text style={[styles.desc, { color: colors.textSecondary }]}>
                {errorMessage ||
                  'Delta membutuhkan akses kamera untuk menjalankan Camera Monitoring.'}
              </Text>
              <View style={styles.buttonRow}>
                <TouchableOpacity
                  style={[styles.btnSecondary, { borderColor: colors.border }]}
                  onPress={dismissDialog}
                >
                  <Text style={[styles.btnSecondaryText, { color: colors.textSecondary }]}>
                    Batal
                  </Text>
                </TouchableOpacity>
                {errorReason === 'PERMISSION_PERMANENTLY_DENIED' ? (
                  <TouchableOpacity
                    style={[styles.btnPrimary, { backgroundColor: '#38bdf8' }]}
                    onPress={handleOpenSettings}
                  >
                    <Text style={styles.btnPrimaryText}>Buka Pengaturan</Text>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity
                    style={[styles.btnPrimary, { backgroundColor: '#38bdf8' }]}
                    onPress={requestStartMonitoring}
                  >
                    <Text style={styles.btnPrimaryText}>Coba Lagi</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          ) : (
            <View style={styles.body}>
              <Text style={[styles.desc, { color: colors.textPrimary, fontWeight: '600' }]}>
                Izinkan Delta melakukan monitoring kamera perangkat ini?
              </Text>

              <Text style={[styles.subDesc, { color: colors.textMuted }]}>
                Kamera akan dapat dilihat dari Delta Web setelah monitoring diaktifkan.
              </Text>

              {/* Bullet Points */}
              <View style={styles.bulletList}>
                <View style={styles.bulletItem}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
                    Kamu dapat menghentikannya kapan saja
                  </Text>
                </View>
                <View style={styles.bulletItem}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
                    Monitoring hanya aktif setelah kamu mengizinkan
                  </Text>
                </View>
                <View style={styles.bulletItem}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
                    Status kamera akan terlihat jelas saat aktif
                  </Text>
                </View>
              </View>

              {/* Action Buttons */}
              <View style={styles.buttonRow}>
                <TouchableOpacity
                  style={[styles.btnSecondary, { borderColor: colors.border }]}
                  onPress={denyUserConsent}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.btnSecondaryText, { color: colors.textSecondary }]}>
                    Batal
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.btnPrimary, { backgroundColor: '#0284c7' }]}
                  onPress={() => {
                    grantUserConsent();
                    webrtcMonitoringService.startMonitoringSession();
                  }}
                  activeOpacity={0.8}
                >
                  <Text style={styles.btnPrimaryText}>Izinkan</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 380,
    borderRadius: 20,
    borderWidth: 1,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  iconWrapper: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: -0.3,
    marginBottom: 12,
    textAlign: 'center',
  },
  body: {
    width: '100%',
  },
  desc: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 8,
  },
  subDesc: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 16,
  },
  bulletList: {
    marginVertical: 12,
    gap: 8,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 12,
    padding: 12,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  bulletDot: {
    color: '#38bdf8',
    fontSize: 14,
    lineHeight: 18,
  },
  bulletText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
    width: '100%',
  },
  btnSecondary: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnSecondaryText: {
    fontSize: 14,
    fontWeight: '600',
  },
  btnPrimary: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnPrimaryText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
});
