import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  ActivityIndicator,
  Clipboard,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Header } from '../../src/components/common/Header';
import { PageTransition } from '../../src/components/common/PageTransition';
import { useThemeColors } from '../../src/theme/theme';
import { useSettingsStore } from '../../src/store/useSettingsStore';
import { useConnectionStore } from '../../src/store/useConnectionStore';
import {
  getTunnelStatus,
  getTunnelLogs,
  startTunnel,
  stopTunnel,
  test9RouterPing,
  TunnelLogEntry,
} from '../../src/services/api/systemApi';

interface ModelRouteConfig {
  id: string;
  name: string;
  provider: string;
  targetEndpoint: string;
  active: boolean;
  priority: number;
  tokensUsed: number;
  icon: keyof typeof Ionicons.glyphMap;
}

const INITIAL_ROUTES: ModelRouteConfig[] = [
  {
    id: 'r1',
    name: 'AntigravityCombo',
    provider: 'Antigravity Cloud',
    targetEndpoint: 'https://api.antigravity.ai/v1',
    active: true,
    priority: 1,
    tokensUsed: 14250,
    icon: 'git-network-outline',
  },
  {
    id: 'r2',
    name: 'ag/gemini-3.7-flash-high',
    provider: 'Antigravity / Google',
    targetEndpoint: 'https://generativelanguage.googleapis.com',
    active: true,
    priority: 2,
    tokensUsed: 48910,
    icon: 'sparkles-outline',
  },
  {
    id: 'r3',
    name: 'gemini-1.5-flash',
    provider: 'Google AI Studio',
    targetEndpoint: 'https://generativelanguage.googleapis.com',
    active: true,
    priority: 3,
    tokensUsed: 8200,
    icon: 'logo-google',
  },
  {
    id: 'r4',
    name: 'deepseek-v4-flash',
    provider: 'OpenCode Zen',
    targetEndpoint: 'https://opencode.ai/zen/v1',
    active: false,
    priority: 4,
    tokensUsed: 0,
    icon: 'code-slash-outline',
  },
];

export default function RouterDashboardScreen() {
  const { colors, isDark } = useThemeColors();
  const { setTunnelUrl, hapticEnabled } = useSettingsStore();

  const [activeTab, setActiveTab] = useState<'router' | 'tunnel'>('router');
  const [routes, setRoutes] = useState<ModelRouteConfig[]>(INITIAL_ROUTES);
  const [pingData, setPingData] = useState<{
    latencyMs: number;
    modelsCount: number;
    isChecking: boolean;
    error?: string;
  }>({
    latencyMs: 12,
    modelsCount: 43,
    isChecking: false,
  });

  const [tunnelStatus, setTunnelStatus] = useState<{
    running: boolean;
    url?: string;
    loading: boolean;
  }>({
    running: false,
    loading: false,
  });
  const [tunnelLogs, setTunnelLogs] = useState<TunnelLogEntry[]>([]);

  useEffect(() => {
    checkPing();
    refreshTunnel();
  }, []);

  const checkPing = async () => {
    setPingData((prev) => ({ ...prev, isChecking: true }));
    try {
      const res = await test9RouterPing();
      setPingData({
        latencyMs: res.latencyMs || 0,
        modelsCount: res.modelsCount || 0,
        isChecking: false,
        error: res.success ? undefined : res.error,
      });
    } catch (_) {
      setPingData((prev) => ({ ...prev, isChecking: false }));
    }
  };

  const refreshTunnel = async () => {
    try {
      const status = await getTunnelStatus();
      setTunnelStatus({
        running: status.running,
        url: status.url || undefined,
        loading: false,
      });
      if (status.url) {
        setTunnelUrl(status.url);
      }
      const logsRes = await getTunnelLogs();
      if (logsRes.logs) {
        setTunnelLogs(logsRes.logs);
      }
    } catch (_) {}
  };

  const handleToggleRoute = (id: string) => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    }
    setRoutes((prev) =>
      prev.map((r) => (r.id === id ? { ...r, active: !r.active } : r))
    );
  };

  const handleToggleTunnel = async (value: boolean) => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    }
    setTunnelStatus((prev) => ({ ...prev, loading: true }));
    try {
      if (value) {
        const res = await startTunnel();
        if (res.running && res.url) {
          await refreshTunnel();
          Alert.alert('Tunnel Aktif', `URL: ${res.url}`);
        } else {
          Alert.alert('Gagal Memulai Tunnel', res.message || 'Error');
        }
      } else {
        await stopTunnel();
        setTunnelStatus({ running: false, loading: false });
      }
    } catch (e: any) {
      Alert.alert('Error Tunnel', e.message);
    } finally {
      setTunnelStatus((prev) => ({ ...prev, loading: false }));
    }
  };

  const handleCopyUrl = (url?: string) => {
    if (!url) return;
    Clipboard.setString(url);
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }
    Alert.alert('Disalin', 'URL Tunnel berhasil disalin ke clipboard.');
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]} edges={['top']}>
      <PageTransition style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header title="Router" subtitle="9Router & Gateway Telemetry" />

        {/* iOS Segmented Control Tab */}
        <View style={styles.segmentWrapper}>
          <View
            style={[
              styles.segmentedControl,
              {
                backgroundColor: isDark ? '#141414' : '#EFEFF0',
                borderColor: colors.border,
              },
            ]}
          >
            <TouchableOpacity
              onPress={() => {
                if (hapticEnabled) Haptics.selectionAsync().catch(() => {});
                setActiveTab('router');
              }}
              style={[
                styles.segmentTab,
                activeTab === 'router' && [
                  styles.segmentTabActive,
                  { backgroundColor: isDark ? '#262626' : '#FFFFFF' },
                ],
              ]}
              activeOpacity={0.8}
            >
              <Ionicons
                name="git-network-outline"
                size={14}
                color={activeTab === 'router' ? colors.textPrimary : colors.textMuted}
                style={{ marginRight: 5 }}
              />
              <Text
                style={[
                  styles.segmentLabel,
                  {
                    color: activeTab === 'router' ? colors.textPrimary : colors.textMuted,
                    fontWeight: activeTab === 'router' ? '700' : '500',
                  },
                ]}
              >
                9Router Gateway
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => {
                if (hapticEnabled) Haptics.selectionAsync().catch(() => {});
                setActiveTab('tunnel');
              }}
              style={[
                styles.segmentTab,
                activeTab === 'tunnel' && [
                  styles.segmentTabActive,
                  { backgroundColor: isDark ? '#262626' : '#FFFFFF' },
                ],
              ]}
              activeOpacity={0.8}
            >
              <Ionicons
                name="globe-outline"
                size={14}
                color={activeTab === 'tunnel' ? colors.textPrimary : colors.textMuted}
                style={{ marginRight: 5 }}
              />
              <Text
                style={[
                  styles.segmentLabel,
                  {
                    color: activeTab === 'tunnel' ? colors.textPrimary : colors.textMuted,
                    fontWeight: activeTab === 'tunnel' ? '700' : '500',
                  },
                ]}
              >
                Cloudflare Tunnel
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.contentContainer}
          showsVerticalScrollIndicator={false}
        >
          {activeTab === 'router' ? (
            /* 9ROUTER GATEWAY VIEW */
            <>
              {/* Status HUD Inset */}
              <View
                style={[
                  styles.hudCard,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
              >
                <View style={styles.hudTopRow}>
                  <View>
                    <Text style={[styles.hudTitle, { color: colors.textPrimary }]}>
                      Local AI Gateway
                    </Text>
                    <Text style={[styles.hudSubtitle, { color: colors.textSecondary }]}>
                      Port 20128 • PRoot / Termux / Laptop
                    </Text>
                  </View>

                  <TouchableOpacity
                    onPress={checkPing}
                    style={[
                      styles.pingRefreshBtn,
                      {
                        backgroundColor: isDark ? '#262626' : '#EFEFF0',
                        borderColor: colors.border,
                      },
                    ]}
                    activeOpacity={0.7}
                  >
                    {pingData.isChecking ? (
                      <ActivityIndicator size="small" color={colors.textPrimary} />
                    ) : (
                      <>
                        <Ionicons name="refresh" size={13} color={colors.textPrimary} />
                        <Text style={[styles.pingBtnText, { color: colors.textPrimary }]}>
                          Test Ping
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                </View>

                {/* Metrics 3-Col Bar */}
                <View style={[styles.metricGrid, { borderTopColor: colors.border }]}>
                  <View style={styles.metricItem}>
                    <Text style={[styles.metricVal, { color: colors.textPrimary }]}>
                      {pingData.latencyMs} ms
                    </Text>
                    <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                      Latency
                    </Text>
                  </View>

                  <View style={[styles.metricDivider, { backgroundColor: colors.border }]} />

                  <View style={styles.metricItem}>
                    <Text style={[styles.metricVal, { color: colors.textPrimary }]}>
                      {pingData.modelsCount}
                    </Text>
                    <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                      Available Models
                    </Text>
                  </View>

                  <View style={[styles.metricDivider, { backgroundColor: colors.border }]} />

                  <View style={styles.metricItem}>
                    <View style={styles.statusPillSmall}>
                      <View
                        style={[
                          styles.dot,
                          { backgroundColor: pingData.error ? colors.error : colors.textPrimary },
                        ]}
                      />
                      <Text style={[styles.metricValSmall, { color: colors.textPrimary }]}>
                        {pingData.error ? 'Offline' : 'Online'}
                      </Text>
                    </View>
                    <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                      Status
                    </Text>
                  </View>
                </View>
              </View>

              {/* Section Header */}
              <View style={styles.sectionHeaderRow}>
                <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
                  RUTE MODEL AKTIF
                </Text>
                <Text style={[styles.sectionSubtitle, { color: colors.textMuted }]}>
                  {routes.filter((r) => r.active).length} AKTIF
                </Text>
              </View>

              {/* iOS Grouped Table Inset (Unified Routes Table) */}
              <View
                style={[
                  styles.groupedTable,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
              >
                {routes.map((item, index) => {
                  const isLast = index === routes.length - 1;

                  return (
                    <View key={item.id}>
                      <View style={styles.tableRow}>
                        {/* Provider Icon Box */}
                        <View
                          style={[
                            styles.routeIconBox,
                            {
                              backgroundColor: isDark ? '#262626' : '#E5E5E5',
                            },
                          ]}
                        >
                          <Ionicons
                            name={item.icon}
                            size={16}
                            color={item.active ? colors.textPrimary : colors.textMuted}
                          />
                        </View>

                        {/* Route Info Body */}
                        <View style={styles.routeBody}>
                          <View style={styles.routeNameRow}>
                            <Text
                              style={[
                                styles.routeName,
                                {
                                  color: colors.textPrimary,
                                  fontWeight: item.active ? '700' : '500',
                                },
                              ]}
                              numberOfLines={1}
                            >
                              {item.name}
                            </Text>
                          </View>

                          <Text
                            style={[styles.routeEndpoint, { color: colors.textMuted }]}
                            numberOfLines={1}
                          >
                            {item.provider} • {item.targetEndpoint.replace('https://', '')}
                          </Text>

                          <Text style={[styles.tokenCount, { color: colors.textSecondary }]}>
                            {item.tokensUsed.toLocaleString()} tokens
                          </Text>
                        </View>

                        {/* Switch Native */}
                        <Switch
                          value={item.active}
                          onValueChange={() => handleToggleRoute(item.id)}
                          trackColor={{ false: isDark ? '#262626' : '#E5E5E5', true: colors.textPrimary }}
                          thumbColor={isDark ? '#000000' : '#FFFFFF'}
                        />
                      </View>

                      {!isLast && (
                        <View
                          style={[
                            styles.tableDivider,
                            { backgroundColor: colors.border },
                          ]}
                        />
                      )}
                    </View>
                  );
                })}
              </View>
            </>
          ) : (
            /* CLOUDFLARE TUNNEL VIEW */
            <>
              {/* Tunnel HUD */}
              <View
                style={[
                  styles.hudCard,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
              >
                <View style={styles.hudTopRow}>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.hudTitle, { color: colors.textPrimary }]}>
                      Cloudflare Tunnel
                    </Text>
                    <Text style={[styles.hudSubtitle, { color: colors.textSecondary }]}>
                      Ekspos Delta CLI ke Public HTTPS
                    </Text>
                  </View>

                  <Switch
                    value={tunnelStatus.running}
                    onValueChange={handleToggleTunnel}
                    disabled={tunnelStatus.loading}
                    trackColor={{ false: isDark ? '#262626' : '#E5E5E5', true: colors.textPrimary }}
                    thumbColor={isDark ? '#000000' : '#FFFFFF'}
                  />
                </View>

                {tunnelStatus.url ? (
                  <View style={[styles.urlBox, { backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA', borderColor: colors.border }]}>
                    <Text style={[styles.urlText, { color: colors.textPrimary }]} numberOfLines={1}>
                      {tunnelStatus.url}
                    </Text>
                    <TouchableOpacity
                      onPress={() => handleCopyUrl(tunnelStatus.url)}
                      style={[styles.copyIconBtn, { backgroundColor: colors.bgSurface }]}
                    >
                      <Feather name="copy" size={13} color={colors.textPrimary} />
                    </TouchableOpacity>
                  </View>
                ) : null}
              </View>

              {/* Tunnel Logs */}
              <View style={styles.sectionHeaderRow}>
                <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
                  LOG AKTIVITAS TUNNEL
                </Text>
                <TouchableOpacity onPress={refreshTunnel}>
                  <Ionicons name="reload-outline" size={15} color={colors.textMuted} />
                </TouchableOpacity>
              </View>

              <View
                style={[
                  styles.logsTerminalCard,
                  {
                    backgroundColor: colors.codeBg,
                    borderColor: colors.codeBorder,
                  },
                ]}
              >
                {tunnelLogs.length === 0 ? (
                  <Text style={[styles.emptyLogs, { color: colors.textMuted }]}>
                    Tidak ada log tunnel saat ini.
                  </Text>
                ) : (
                  tunnelLogs.slice(-10).map((log, index) => (
                    <View key={index} style={styles.logRow}>
                      <Text style={[styles.logTime, { color: colors.textMuted }]}>
                        {log.timestamp}
                      </Text>
                      <Text
                        style={[
                          styles.logMessage,
                          {
                            color: log.level === 'error' ? colors.error : colors.textPrimary,
                          },
                        ]}
                      >
                        {log.message}
                      </Text>
                    </View>
                  ))
                )}
              </View>
            </>
          )}
        </ScrollView>
      </PageTransition>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  segmentWrapper: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  segmentedControl: {
    flexDirection: 'row',
    borderRadius: 12,
    borderWidth: 1,
    padding: 3,
  },
  segmentTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 7,
    borderRadius: 9,
  },
  segmentTabActive: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.12,
        shadowRadius: 2,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  segmentLabel: {
    fontSize: 12.5,
    letterSpacing: -0.2,
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: 90,
  },
  hudCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  hudTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  hudTitle: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  hudSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  pingRefreshBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    borderWidth: 1,
    gap: 4,
  },
  pingBtnText: {
    fontSize: 11.5,
    fontWeight: '700',
  },
  metricGrid: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  metricItem: {
    flex: 1,
    alignItems: 'center',
  },
  metricDivider: {
    width: StyleSheet.hairlineWidth,
    height: 24,
  },
  metricVal: {
    fontSize: 14,
    fontWeight: '800',
    marginBottom: 2,
  },
  metricValSmall: {
    fontSize: 12,
    fontWeight: '700',
    marginLeft: 4,
  },
  metricLabel: {
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statusPillSmall: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
    marginTop: 4,
    paddingHorizontal: 4,
  },
  sectionTitle: {
    fontSize: 11.5,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  sectionSubtitle: {
    fontSize: 11,
    fontWeight: '600',
  },
  groupedTable: {
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
    marginBottom: 16,
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  routeIconBox: {
    width: 34,
    height: 34,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  routeBody: {
    flex: 1,
    marginRight: 10,
  },
  routeNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  routeName: {
    fontSize: 14,
    letterSpacing: -0.2,
  },
  routeEndpoint: {
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginTop: 2,
  },
  tokenCount: {
    fontSize: 10.5,
    marginTop: 2,
  },
  tableDivider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 60,
  },
  urlBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 6,
  },
  urlText: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    flex: 1,
    marginRight: 8,
  },
  copyIconBtn: {
    padding: 5,
    borderRadius: 6,
  },
  logsTerminalCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    minHeight: 180,
  },
  emptyLogs: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 30,
  },
  logRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  logTime: {
    fontSize: 10.5,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginRight: 8,
  },
  logMessage: {
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    flex: 1,
  },
});
