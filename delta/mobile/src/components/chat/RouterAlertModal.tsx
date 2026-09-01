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
                <TouchableOpacity
                  onPress={onClose}
                  hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                  accessibilityRole="button"
                  accessibilityLabel="Close dialog"
                >
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
                  accessibilityRole="button"
                  accessibilityLabel="Start 9Router Gateway"
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
                    accessibilityRole="button"
                    accessibilityLabel="Check Again"
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
                    accessibilityRole="button"
                    accessibilityLabel="Close"
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
    borderRadius: 8,
    borderWidth: 1,
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
    width: 40,
    height: 40,
    borderRadius: 4,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  headerTextWrap: {
    flex: 1,
  },
  title: {
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  subtitle: {
    fontSize: 11,
    marginTop: 2,
  },
  diagnosticBox: {
    borderRadius: 6,
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
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: 1,
  },
  statusText: {
    fontSize: 9.5,
    fontWeight: '800',
    letterSpacing: 0.4,
    fontFamily: 'monospace',
  },
  actions: {
    gap: 10,
  },
  primaryBtn: {
    height: 40,
    borderRadius: 4,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  primaryBtnText: {
    color: '#000',
    fontSize: 12.5,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  secondaryRow: {
    flexDirection: 'row',
    gap: 10,
  },
  secondaryBtn: {
    flex: 1,
    height: 36,
    borderRadius: 4,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  secondaryBtnText: {
    fontSize: 11.5,
    fontWeight: '600',
  },
});
