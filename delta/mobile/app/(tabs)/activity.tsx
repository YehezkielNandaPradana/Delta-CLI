import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Switch,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, Feather } from '@expo/vector-icons';
import { Header } from '../../src/components/common/Header';
import { LiquidGlassCard } from '../../src/components/common/LiquidGlassCard';
import { TelemetryLineChart, DataPoint } from '../../src/components/activity/TelemetryLineChart';
import { useThemeColors } from '../../src/theme/theme';
import { useSettingsStore } from '../../src/store/useSettingsStore';
import { useConnectionStore } from '../../src/store/useConnectionStore';

interface ModelRouteConfig {
  id: string;
  name: string;
  provider: string;
  targetEndpoint: string;
  active: boolean;
  priority: number;
  tokensUsed: number;
  costEstimate: string;
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
    costEstimate: '$0.00 (Free)',
  },
  {
    id: 'r2',
    name: 'ag/gemini-3.7-flash-high',
    provider: 'Antigravity / Google',
    targetEndpoint: 'https://generativelanguage.googleapis.com',
    active: true,
    priority: 2,
    tokensUsed: 48910,
    costEstimate: '$0.00 (Free)',
  },
  {
    id: 'r3',
    name: 'gemini-1.5-flash',
    provider: 'Google AI Studio',
    targetEndpoint: 'https://generativelanguage.googleapis.com',
    active: true,
    priority: 3,
    tokensUsed: 8200,
    costEstimate: '$0.00 (Free)',
  },
  {
    id: 'r4',
    name: 'deepseek-v4-flash',
    provider: 'OpenCode Zen',
    targetEndpoint: 'https://opencode.ai/zen/v1',
    active: false,
    priority: 4,
    tokensUsed: 0,
    costEstimate: '$0.00 (Free)',
  },
];

const TOKEN_TELEMETRY: DataPoint[] = [
  { label: '09:00', value: 120 },
  { label: '12:00', value: 450 },
  { label: '15:00', value: 890 },
  { label: '18:00', value: 1420 },
  { label: '21:00', value: 2100 },
  { label: 'NOW', value: 3400 },
];

export default function RouterDashboardScreen() {
  const { colors, isDark } = useThemeColors();
  const { cloudModel, getActiveAccount, accounts } = useSettingsStore();
  const { isRouterRunning } = useConnectionStore();

  const [routes, setRoutes] = useState<ModelRouteConfig[]>(INITIAL_ROUTES);
  const [proxyPort, setProxyPort] = useState('20128');
  const [autoFallback, setAutoFallback] = useState(true);
  const [streamEnabled, setStreamEnabled] = useState(true);
  const [maxContextTokens, setMaxContextTokens] = useState('8192');

  const totalTokens = routes.reduce((sum, r) => sum + r.tokensUsed, 0);
  const activeAccount = getActiveAccount();

  const toggleRouteActive = (id: string) => {
    setRoutes((prev) =>
      prev.map((r) => (r.id === id ? { ...r, active: !r.active } : r))
    );
  };

  const handleApplyConfig = () => {
    Alert.alert('9Router Updated', `Local gateway configuration applied on port ${proxyPort}.`);
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]} edges={['top']}>
      <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header title="DELTA" subtitle="9Router Dashboard & Telemetry" />

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.contentContainer}
          showsVerticalScrollIndicator={false}
        >
          {/* TOP 3-METRIC HUD CARDS */}
          <View style={styles.metricsRow}>
            {/* Router Core Status */}
            <View style={styles.metricCol}>
              <LiquidGlassCard style={styles.metricCard}>
                <View style={styles.metricIconRow}>
                  <Ionicons name="git-network-outline" size={16} color={colors.accentGreen} />
                  <View
                    style={[
                      styles.dotBadge,
                      { backgroundColor: isRouterRunning ? colors.accentGreen : colors.accentYellow },
                    ]}
                  />
                </View>
                <Text style={[styles.metricVal, { color: colors.textPrimary }]}>
                  {isRouterRunning ? 'Online' : 'Embedded'}
                </Text>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>9ROUTER PORT {proxyPort}</Text>
              </LiquidGlassCard>
            </View>

            {/* Total Tokens Processed */}
            <View style={styles.metricCol}>
              <LiquidGlassCard style={styles.metricCard}>
                <View style={styles.metricIconRow}>
                  <Ionicons name="hardware-chip-outline" size={16} color={colors.accentCyan} />
                  <Text style={[styles.subValue, { color: colors.accentCyan }]}>Total</Text>
                </View>
                <Text style={[styles.metricVal, { color: colors.textPrimary }]}>
                  {(totalTokens / 1000).toFixed(1)}k
                </Text>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>TOKENS MONITORED</Text>
              </LiquidGlassCard>
            </View>

            {/* Total Cost Estimate */}
            <View style={styles.metricCol}>
              <LiquidGlassCard style={styles.metricCard}>
                <View style={styles.metricIconRow}>
                  <Ionicons name="wallet-outline" size={16} color={colors.accentGreen} />
                  <Text style={[styles.subValue, { color: colors.accentGreen }]}>100%</Text>
                </View>
                <Text style={[styles.metricVal, { color: colors.textPrimary }]}>
                  $0.00
                </Text>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>ESTIMATED COST</Text>
              </LiquidGlassCard>
            </View>
          </View>

          {/* TOKEN VELOCITY TELEMETRY CHART */}
          <View style={styles.section}>
            <View style={styles.sectionHeaderRow}>
              <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
                TOKEN CONSUMPTION TELEMETRY
              </Text>
              <View style={[styles.badge, { backgroundColor: colors.accentGreenSubtle }]}>
                <Text style={[styles.badgeText, { color: colors.accentGreen }]}>REALTIME</Text>
              </View>
            </View>

            <LiquidGlassCard style={styles.chartWrapperCard}>
              <TelemetryLineChart
                title="CUMULATIVE TOKEN VELOCITY"
                subtitle="Aggregated tokens routed across active Antigravity / Gemini models"
                data={TOKEN_TELEMETRY}
                unit="tok"
                color={colors.accentGreen}
                height={140}
              />
            </LiquidGlassCard>
          </View>

          {/* ROUTE / MODEL ORCHESTRATION MANAGEMENT */}
          <View style={styles.section}>
            <View style={styles.sectionHeaderRow}>
              <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
                MODEL ROUTE MATRIX ({routes.length})
              </Text>
              <Text style={[styles.subText, { color: colors.textMuted }]}>
                Active: {cloudModel || 'AntigravityCombo'}
              </Text>
            </View>

            <LiquidGlassCard style={styles.glassCard}>
              {routes.map((r, idx) => (
                <View
                  key={r.id}
                  style={[
                    styles.routeCard,
                    {
                      backgroundColor: r.active ? colors.accentGreenSubtle : colors.bgSecondary,
                      borderColor: r.active ? colors.accentGreen : colors.cardBorder,
                    },
                  ]}
                >
                  <View style={styles.routeLeft}>
                    <View style={styles.routeHeaderRow}>
                      <Text
                        style={[
                          styles.routeName,
                          { color: r.active ? colors.accentGreen : colors.textPrimary },
                        ]}
                      >
                        {r.name}
                      </Text>
                      <View style={[styles.priorityBadge, { backgroundColor: colors.bgSurface }]}>
                        <Text style={[styles.priorityText, { color: colors.textMuted }]}>
                          P{r.priority}
                        </Text>
                      </View>
                    </View>

                    <Text style={[styles.routeMeta, { color: colors.textMuted }]}>
                      Provider: {r.provider} · {r.tokensUsed.toLocaleString()} tokens
                    </Text>
                    <Text style={[styles.routeUrl, { color: colors.textDim }]} numberOfLines={1}>
                      {r.targetEndpoint}
                    </Text>
                  </View>

                  <Switch
                    value={r.active}
                    onValueChange={() => toggleRouteActive(r.id)}
                    trackColor={{
                      false: colors.bgSecondary,
                      true: colors.accentGreenSubtle,
                    }}
                    thumbColor={r.active ? colors.accentGreen : colors.textMuted}
                  />
                </View>
              ))}
            </LiquidGlassCard>
          </View>

          {/* LOCAL GATEWAY TUNING & SETTINGS */}
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.textPrimary }]}>
              9ROUTER PARAMETER TUNING
            </Text>

            <LiquidGlassCard style={styles.glassCard}>
              <View style={styles.settingRow}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.settingLabel, { color: colors.textPrimary }]}>
                    Automatic High-Demand Failover
                  </Text>
                  <Text style={[styles.settingDesc, { color: colors.textMuted }]}>
                    Auto-switch to backup model if Google AI / Antigravity returns 503
                  </Text>
                </View>
                <Switch
                  value={autoFallback}
                  onValueChange={setAutoFallback}
                  trackColor={{ false: colors.bgSecondary, true: colors.accentGreenSubtle }}
                  thumbColor={autoFallback ? colors.accentGreen : colors.textMuted}
                />
              </View>

              <View style={[styles.settingRow, { borderTopColor: colors.cardBorder, borderTopWidth: 1 }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.settingLabel, { color: colors.textPrimary }]}>
                    Streaming Token Generation
                  </Text>
                  <Text style={[styles.settingDesc, { color: colors.textMuted }]}>
                    Stream token-by-token for ultra low latency
                  </Text>
                </View>
                <Switch
                  value={streamEnabled}
                  onValueChange={setStreamEnabled}
                  trackColor={{ false: colors.bgSecondary, true: colors.accentGreenSubtle }}
                  thumbColor={streamEnabled ? colors.accentGreen : colors.textMuted}
                />
              </View>

              <View style={[styles.settingRow, { borderTopColor: colors.cardBorder, borderTopWidth: 1 }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.settingLabel, { color: colors.textPrimary }]}>
                    Max Context Window (Tokens)
                  </Text>
                  <Text style={[styles.settingDesc, { color: colors.textMuted }]}>
                    Limits context size sent per request
                  </Text>
                </View>
                <TextInput
                  style={[
                    styles.smallInput,
                    {
                      backgroundColor: colors.codeBg,
                      borderColor: colors.codeBorder,
                      color: colors.textPrimary,
                    },
                  ]}
                  value={maxContextTokens}
                  onChangeText={setMaxContextTokens}
                  keyboardType="numeric"
                />
              </View>

              <TouchableOpacity
                style={[styles.applyBtn, { backgroundColor: colors.accentGreen }]}
                onPress={handleApplyConfig}
                activeOpacity={0.8}
              >
                <Feather name="check" size={15} color={isDark ? '#000000' : '#ffffff'} />
                <Text style={[styles.applyBtnText, { color: isDark ? '#000000' : '#ffffff' }]}>
                  Save & Apply 9Router Settings
                </Text>
              </TouchableOpacity>
            </LiquidGlassCard>
          </View>
        </ScrollView>
      </View>
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
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 110,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 20,
  },
  metricCol: {
    flex: 1,
  },
  metricCard: {
    padding: 12,
    borderRadius: 16,
    alignItems: 'flex-start',
  },
  metricIconRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: 8,
  },
  dotBadge: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  subValue: {
    fontSize: 9.5,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  metricVal: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  metricLabel: {
    fontSize: 8.5,
    fontWeight: '800',
    letterSpacing: 0.6,
    marginTop: 2,
  },
  section: {
    marginBottom: 20,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    paddingHorizontal: 4,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.1,
  },
  subText: {
    fontSize: 10.5,
    fontWeight: '600',
  },
  badge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 8.5,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  chartWrapperCard: {
    padding: 14,
    borderRadius: 18,
  },
  glassCard: {
    padding: 14,
    borderRadius: 18,
  },
  routeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
  },
  routeLeft: {
    flex: 1,
    marginRight: 10,
  },
  routeHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  routeName: {
    fontSize: 13,
    fontWeight: '700',
  },
  priorityBadge: {
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 4,
  },
  priorityText: {
    fontSize: 8.5,
    fontWeight: '800',
  },
  routeMeta: {
    fontSize: 10.5,
    marginTop: 2,
  },
  routeUrl: {
    fontSize: 9.5,
    marginTop: 1,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  settingLabel: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  settingDesc: {
    fontSize: 10.5,
    marginTop: 2,
  },
  smallInput: {
    width: 80,
    height: 36,
    borderWidth: 1,
    borderRadius: 8,
    textAlign: 'center',
    fontSize: 12,
    fontWeight: '700',
  },
  applyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    height: 42,
    borderRadius: 12,
    marginTop: 12,
  },
  applyBtnText: {
    fontSize: 12.5,
    fontWeight: '800',
  },
});
