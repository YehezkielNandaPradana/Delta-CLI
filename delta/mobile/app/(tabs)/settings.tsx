import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Switch,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, Feather } from '@expo/vector-icons';
import { Header } from '../../src/components/common/Header';
import { LiquidGlassCard } from '../../src/components/common/LiquidGlassCard';
import { RouterAlertModal } from '../../src/components/chat/RouterAlertModal';
import { AccountManagerModal } from '../../src/components/settings/AccountManagerModal';
import { useSettingsStore, ThemeMode } from '../../src/store/useSettingsStore';
import { useConnectionStore } from '../../src/store/useConnectionStore';
import { getModels, selectModel, getSystemStatus, getRouterStatus } from '../../src/services/api/systemApi';
import { sseClient } from '../../src/services/realtime/sseClient';
import { AIModel } from '../../src/types/system';
import { AntigravityAccount, ConnectionMode } from '../../src/types/cloud';
import { useThemeColors } from '../../src/theme/theme';

const CLOUD_MODEL_PRESETS: { name: string; description: string }[] = [
  {
    name: 'gemini-1.5-flash',
    description: 'Google Gemini 1.5 Flash (Most Stable & High Availability)',
  },
  {
    name: 'gemini-1.5-pro',
    description: 'Google Gemini 1.5 Pro (Deep Reasoning & Analysis)',
  },
  {
    name: 'gemini-3.6-flash',
    description: 'Google Gemini 3.6 Flash',
  },
];

const DEFAULT_9ROUTER_PRESETS: AIModel[] = [
  {
    name: 'ag/gemini-3.7-flash-high',
    description: 'Gemini 3.7 Flash High via Antigravity in 9Router',
    provider: '9router',
    is_current: true,
  },
  {
    name: 'google/gemini-3.7-flash',
    description: 'Google Gemini 3.7 Flash via Antigravity in 9Router',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'antigravity/gemini-3.7-flash',
    description: 'Direct Gemini 3.7 Flash Antigravity Route',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'deepseek/deepseek-v4-flash',
    description: 'DeepSeek V4 Flash - fast & efficient',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'anthropic/claude-sonnet-4-20250514',
    description: 'Claude Sonnet 4 via 9Router Gateway',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'openai/gpt-4o-mini',
    description: 'OpenAI GPT-4o Mini via 9Router',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'AntigravityCombo',
    description: 'Antigravity Multi-provider Hybrid Combo',
    provider: '9router',
    is_current: false,
  },
];

export default function SettingsScreen() {
  const { colors, isDark } = useThemeColors();
  const {
    serverUrl,
    activeModel,
    hapticEnabled,
    theme,
    connectionMode,
    accounts,
    activeAccountId,
    cloudModel,
    setServerUrl,
    setActiveModel,
    setHapticEnabled,
    setTheme,
    setConnectionMode,
    setCloudModel,
    addAccount,
    updateAccount,
    deleteAccount,
    setActiveAccount,
    getActiveAccount,
  } = useSettingsStore();
  const { status, workingDirectory, isRouterRunning, setIsRouterRunning } = useConnectionStore();

  const [inputUrl, setInputUrl] = useState(serverUrl);
  const [models, setModels] = useState<AIModel[]>(DEFAULT_9ROUTER_PRESETS);
  const [loadingModels, setLoadingModels] = useState(false);
  const [switchingModel, setSwitchingModel] = useState<string | null>(null);
  const [selectedProviderFilter, setSelectedProviderFilter] = useState<string>('9router');
  const [customModelInput, setCustomModelInput] = useState('');
  const [testingConnection, setTestingConnection] = useState(false);
  const [showRouterModal, setShowRouterModal] = useState(false);

  // Account Modal State
  const [accountModalVisible, setAccountModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<AntigravityAccount | null>(null);

  useEffect(() => {
    setInputUrl(serverUrl);
  }, [serverUrl]);

  const loadModelsList = async () => {
    if (connectionMode === 'cloud') return;
    setLoadingModels(true);
    try {
      const res = await getModels();
      if (res.status === 'ok' && res.models && res.models.length > 0) {
        setModels(res.models);
        if (res.current_model) {
          setActiveModel(res.current_model);
        }
      } else {
        setModels(DEFAULT_9ROUTER_PRESETS);
      }
    } catch (e) {
      setModels(DEFAULT_9ROUTER_PRESETS);
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    loadModelsList();
  }, [serverUrl, connectionMode]);

  const handleSaveUrl = async () => {
    await setServerUrl(inputUrl);
    sseClient.restart();
    Alert.alert('Saved', 'Server URL updated and reconnecting.');
  };

  const handleSelectModel = async (modelName: string) => {
    if (connectionMode === 'cloud') {
      await setCloudModel(modelName);
      Alert.alert('Cloud Model Set', `Active cloud model: ${modelName}`);
      return;
    }

    setSwitchingModel(modelName);
    try {
      const res = await selectModel(modelName);
      if (res.status === 'ok') {
        await setActiveModel(modelName);
        Alert.alert('Model Switched', `Active model is now ${modelName}`);
        loadModelsList();
      } else {
        await setActiveModel(modelName);
        Alert.alert('Model Switched', `Selected model: ${modelName}`);
      }
    } catch (err: any) {
      await setActiveModel(modelName);
      Alert.alert('Model Updated', `Active model set to ${modelName}`);
    } finally {
      setSwitchingModel(null);
    }
  };

  const handleApplyCustomModel = async () => {
    const trimmed = customModelInput.trim();
    if (!trimmed) return;
    await handleSelectModel(trimmed);
    setCustomModelInput('');
  };

  const handleSaveAccount = async (
    accData: Omit<AntigravityAccount, 'id'>,
    editId?: string
  ) => {
    if (editId) {
      await updateAccount(editId, accData);
      Alert.alert('Success', 'Akun berhasil diperbarui.');
    } else {
      await addAccount(accData);
      Alert.alert('Success', 'Akun Antigravity berhasil ditambahkan.');
    }
  };

  const handleDeleteAccount = (acc: AntigravityAccount) => {
    Alert.alert('Hapus Akun', `Yakin ingin menghapus akun "${acc.name}"?`, [
      { text: 'Batal', style: 'cancel' },
      {
        text: 'Hapus',
        style: 'destructive',
        onPress: async () => {
          await deleteAccount(acc.id);
        },
      },
    ]);
  };

  const themeOptions: { mode: ThemeMode; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
    { mode: 'dark', label: 'Dark', icon: 'moon' },
    { mode: 'light', label: 'Light', icon: 'sunny' },
    { mode: 'system', label: 'System', icon: 'phone-portrait-outline' },
  ];

  const currentActiveAccount = getActiveAccount();

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]} edges={['top']}>
      <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header
          title="DELTA"
          subtitle="Connection & AI Configuration"
          onRouterWarningPress={() => setShowRouterModal(true)}
        />

        <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
          {/* CONNECTION MODE TOGGLE */}
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
              CONNECTION ARCHITECTURE
            </Text>
            <View style={styles.connectionToggleRow}>
              <TouchableOpacity
                style={[
                  styles.connectionPill,
                  {
                    backgroundColor:
                      connectionMode === 'cloud' ? colors.accentGreenSubtle : colors.cardBg,
                    borderColor:
                      connectionMode === 'cloud' ? colors.accentGreen : colors.cardBorder,
                  },
                ]}
                onPress={() => setConnectionMode('cloud')}
                activeOpacity={0.8}
              >
                <Ionicons
                  name="cloud-outline"
                  size={18}
                  color={connectionMode === 'cloud' ? colors.accentGreen : colors.textMuted}
                />
                <View>
                  <Text
                    style={[
                      styles.connectionPillTitle,
                      {
                        color:
                          connectionMode === 'cloud' ? colors.accentGreen : colors.textPrimary,
                      },
                    ]}
                  >
                    Direct Cloud (Internet)
                  </Text>
                  <Text style={[styles.connectionPillDesc, { color: colors.textMuted }]}>
                    Antigravity API · No Server Needed
                  </Text>
                </View>
              </TouchableOpacity>

              <TouchableOpacity
                style={[
                  styles.connectionPill,
                  {
                    backgroundColor:
                      connectionMode === 'local' ? colors.accentCyanSubtle : colors.cardBg,
                    borderColor:
                      connectionMode === 'local' ? colors.accentCyan : colors.cardBorder,
                  },
                ]}
                onPress={() => setConnectionMode('local')}
                activeOpacity={0.8}
              >
                <Ionicons
                  name="laptop-outline"
                  size={18}
                  color={connectionMode === 'local' ? colors.accentCyan : colors.textMuted}
                />
                <View>
                  <Text
                    style={[
                      styles.connectionPillTitle,
                      {
                        color:
                          connectionMode === 'local' ? colors.accentCyan : colors.textPrimary,
                      },
                    ]}
                  >
                    Local Delta Server
                  </Text>
                  <Text style={[styles.connectionPillDesc, { color: colors.textMuted }]}>
                    FastAPI + Local 9Router
                  </Text>
                </View>
              </TouchableOpacity>
            </View>
          </View>

          {/* CLOUD MODE: ANTIGRAVITY ACCOUNTS & MODELS */}
          {connectionMode === 'cloud' ? (
            <>
              {/* ANTIGRAVITY ACCOUNTS MANAGEMENT */}
              <View style={styles.section}>
                <View style={styles.sectionHeaderRow}>
                  <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
                    ANTIGRAVITY ACCOUNTS ({accounts.length})
                  </Text>
                  <TouchableOpacity
                    onPress={() => {
                      setEditingAccount(null);
                      setAccountModalVisible(true);
                    }}
                    style={[styles.addAccountHeaderBtn, { backgroundColor: colors.accentGreenSubtle }]}
                  >
                    <Feather name="plus" size={13} color={colors.accentGreen} />
                    <Text style={[styles.addAccountHeaderText, { color: colors.accentGreen }]}>
                      Tambah Akun
                    </Text>
                  </TouchableOpacity>
                </View>

                <LiquidGlassCard style={styles.glassCard}>
                  {accounts.map((acc) => {
                    const isActive = acc.id === activeAccountId;
                    const maskedKey = acc.apiKey
                      ? `${acc.apiKey.slice(0, 4)}••••••••${acc.apiKey.slice(-4)}`
                      : 'Belum ada API Key';

                    return (
                      <TouchableOpacity
                        key={acc.id}
                        style={[
                          styles.accountItem,
                          {
                            backgroundColor: isActive
                              ? colors.accentGreenSubtle
                              : colors.bgSecondary,
                            borderColor: isActive ? colors.accentGreen : colors.cardBorder,
                          },
                        ]}
                        onPress={() => setActiveAccount(acc.id)}
                        activeOpacity={0.7}
                      >
                        <View style={styles.accountItemLeft}>
                          <View style={styles.accountHeaderRow}>
                            <Text
                              style={[
                                styles.accountName,
                                { color: isActive ? colors.accentGreen : colors.textPrimary },
                              ]}
                            >
                              {acc.name}
                            </Text>
                            {isActive && (
                              <View
                                style={[
                                  styles.activeBadge,
                                  { backgroundColor: colors.accentGreen },
                                ]}
                              >
                                <Text
                                  style={[
                                    styles.activeBadgeText,
                                    { color: isDark ? '#000000' : '#ffffff' },
                                  ]}
                                >
                                  AKTIF
                                </Text>
                              </View>
                            )}
                          </View>
                          <Text style={[styles.accountKeyText, { color: colors.textMuted }]}>
                            Key: {maskedKey}
                          </Text>
                          <Text
                            style={[styles.accountUrlText, { color: colors.textDim }]}
                            numberOfLines={1}
                          >
                            URL: {acc.baseUrl ? acc.baseUrl : 'Google Gemini Official API (Default)'}
                          </Text>
                        </View>

                        <View style={styles.accountActions}>
                          <TouchableOpacity
                            onPress={() => {
                              setEditingAccount(acc);
                              setAccountModalVisible(true);
                            }}
                            style={styles.actionIconBtn}
                          >
                            <Feather name="edit-2" size={15} color={colors.accentCyan} />
                          </TouchableOpacity>
                          {accounts.length > 1 && (
                            <TouchableOpacity
                              onPress={() => handleDeleteAccount(acc)}
                              style={styles.actionIconBtn}
                            >
                              <Feather name="trash-2" size={15} color={colors.accentRed} />
                            </TouchableOpacity>
                          )}
                        </View>
                      </TouchableOpacity>
                    );
                  })}
                </LiquidGlassCard>
              </View>

              {/* CLOUD MODEL SELECTION */}
              <View style={styles.section}>
                <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
                  ANTIGRAVITY CLOUD MODEL
                </Text>
                <LiquidGlassCard style={styles.glassCard}>
                  {CLOUD_MODEL_PRESETS.map((m) => {
                    const isSelected = (cloudModel || 'ag/gemini-3.7-flash-high') === m.name;
                    return (
                      <TouchableOpacity
                        key={m.name}
                        style={[
                          styles.modelItem,
                          {
                            backgroundColor: isSelected
                              ? colors.accentGreenSubtle
                              : colors.bgSecondary,
                            borderColor: isSelected ? colors.accentGreen : colors.cardBorder,
                          },
                        ]}
                        onPress={() => handleSelectModel(m.name)}
                        activeOpacity={0.7}
                      >
                        <View style={styles.modelInfo}>
                          <Text
                            style={[
                              styles.modelName,
                              { color: isSelected ? colors.accentGreen : colors.textPrimary },
                            ]}
                          >
                            {m.name}
                          </Text>
                          <Text style={[styles.modelDesc, { color: colors.textMuted }]}>
                            {m.description}
                          </Text>
                        </View>
                        {isSelected ? (
                          <View
                            style={[
                              styles.activeCheckCircle,
                              { backgroundColor: colors.accentGreen },
                            ]}
                          >
                            <Feather name="check" size={13} color={isDark ? '#000000' : '#ffffff'} />
                          </View>
                        ) : (
                          <Feather name="chevron-right" size={16} color={colors.textDim} />
                        )}
                      </TouchableOpacity>
                    );
                  })}

                  {/* Custom Model Input */}
                  <View style={[styles.customModelSection, { borderTopColor: colors.cardBorder }]}>
                    <Text style={[styles.label, { color: colors.textSecondary }]}>
                      Custom Cloud Model ID
                    </Text>
                    <View style={styles.inputRow}>
                      <TextInput
                        style={[
                          styles.textInput,
                          {
                            backgroundColor: colors.codeBg,
                            borderColor: colors.codeBorder,
                            color: colors.textPrimary,
                          },
                        ]}
                        value={customModelInput}
                        onChangeText={setCustomModelInput}
                        placeholder="Contoh: gemini-3.7-flash-high"
                        placeholderTextColor={colors.textMuted}
                        autoCapitalize="none"
                        autoCorrect={false}
                      />
                      <TouchableOpacity
                        style={[styles.saveBtn, { backgroundColor: colors.accentGreen }]}
                        onPress={handleApplyCustomModel}
                        activeOpacity={0.7}
                      >
                        <Text
                          style={[styles.saveBtnText, { color: isDark ? '#000000' : '#ffffff' }]}
                        >
                          Terapkan
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                </LiquidGlassCard>
              </View>
            </>
          ) : (
            /* LOCAL MODE SECTIONS */
            <>
              {/* 9ROUTER DIAGNOSTICS */}
              <View style={styles.section}>
                <View style={styles.sectionHeaderRow}>
                  <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
                    9ROUTER GATEWAY DIAGNOSTICS
                  </Text>
                  <TouchableOpacity
                    onPress={async () => {
                      try {
                        const r = await getRouterStatus();
                        setIsRouterRunning(r.running);
                        Alert.alert(
                          '9Router Status',
                          r.running ? 'Active on port 20128' : 'Offline / Inactive'
                        );
                      } catch (e: any) {
                        Alert.alert('9Router Check Failed', e.message);
                      }
                    }}
                    style={styles.refreshBtn}
                  >
                    <Feather name="refresh-cw" size={13} color={colors.accentGreen} />
                  </TouchableOpacity>
                </View>

                <LiquidGlassCard style={styles.glassCard}>
                  <View style={styles.statusRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.switchLabel, { color: colors.textPrimary }]}>
                        Local 9Router Proxy (Port 20128)
                      </Text>
                      <Text style={[styles.switchDesc, { color: colors.textMuted }]}>
                        {isRouterRunning
                          ? 'Online and accepting AI requests'
                          : 'Offline — click below to configure'}
                      </Text>
                    </View>
                    <View style={styles.statusPillBadge}>
                      <View
                        style={[
                          styles.statusDot,
                          {
                            backgroundColor: isRouterRunning
                              ? colors.accentGreen
                              : colors.accentYellow,
                          },
                        ]}
                      />
                      <Text
                        style={[
                          styles.statusValue,
                          {
                            color: isRouterRunning
                              ? colors.accentGreen
                              : colors.accentYellow,
                          },
                        ]}
                      >
                        {isRouterRunning ? 'Online' : 'Inactive'}
                      </Text>
                    </View>
                  </View>

                  {!isRouterRunning && (
                    <TouchableOpacity
                      style={[
                        styles.testBtn,
                        {
                          backgroundColor: colors.accentYellowSubtle,
                          borderColor: colors.accentYellow,
                          marginTop: 10,
                        },
                      ]}
                      onPress={() => setShowRouterModal(true)}
                      activeOpacity={0.8}
                    >
                      <Ionicons name="flash-outline" size={14} color={colors.accentYellow} />
                      <Text
                        style={[
                          styles.testBtnText,
                          { color: colors.accentYellow, fontWeight: '700' },
                        ]}
                      >
                        Open 9Router Activation Center
                      </Text>
                    </TouchableOpacity>
                  )}
                </LiquidGlassCard>
              </View>

              {/* LOCAL SERVER CONNECTION */}
              <View style={styles.section}>
                <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
                  LOCAL SERVER CONNECTION
                </Text>
                <LiquidGlassCard style={styles.glassCard}>
                  <Text style={[styles.label, { color: colors.textSecondary }]}>
                    Host / API URL
                  </Text>
                  <View style={styles.inputRow}>
                    <TextInput
                      style={[
                        styles.textInput,
                        {
                          backgroundColor: colors.codeBg,
                          borderColor: colors.codeBorder,
                          color: colors.textPrimary,
                        },
                      ]}
                      value={inputUrl}
                      onChangeText={setInputUrl}
                      placeholder="http://10.0.2.2:8080"
                      placeholderTextColor={colors.textMuted}
                      autoCapitalize="none"
                      autoCorrect={false}
                    />
                    <TouchableOpacity
                      style={[styles.saveBtn, { backgroundColor: colors.accentGreen }]}
                      onPress={handleSaveUrl}
                      activeOpacity={0.7}
                    >
                      <Text
                        style={[styles.saveBtnText, { color: isDark ? '#000000' : '#ffffff' }]}
                      >
                        Save
                      </Text>
                    </TouchableOpacity>
                  </View>
                </LiquidGlassCard>
              </View>
            </>
          )}

          {/* THEME SELECTION */}
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
              APPEARANCE & THEME
            </Text>
            <View style={styles.themeSelectorRow}>
              {themeOptions.map((opt) => {
                const isSelected = theme === opt.mode;
                return (
                  <TouchableOpacity
                    key={opt.mode}
                    style={[
                      styles.themeCard,
                      {
                        backgroundColor: colors.cardBg,
                        borderColor: isSelected ? colors.accentGreen : colors.cardBorder,
                      },
                    ]}
                    onPress={() => setTheme(opt.mode)}
                    activeOpacity={0.8}
                  >
                    <Ionicons
                      name={opt.icon}
                      size={20}
                      color={isSelected ? colors.accentGreen : colors.textMuted}
                    />
                    <Text
                      style={[
                        styles.themeLabel,
                        {
                          color: isSelected ? colors.accentGreen : colors.textSecondary,
                          fontWeight: isSelected ? '700' : '500',
                        },
                      ]}
                    >
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {/* PREFERENCES */}
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
              PREFERENCES
            </Text>
            <LiquidGlassCard style={styles.glassCard}>
              <View style={styles.switchRow}>
                <View>
                  <Text style={[styles.switchLabel, { color: colors.textPrimary }]}>
                    Haptic Feedback
                  </Text>
                  <Text style={[styles.switchDesc, { color: colors.textMuted }]}>
                    Tactile vibration on events and responses
                  </Text>
                </View>
                <Switch
                  value={hapticEnabled}
                  onValueChange={setHapticEnabled}
                  trackColor={{
                    false: colors.bgSecondary,
                    true: colors.accentGreenSubtle,
                  }}
                  thumbColor={hapticEnabled ? colors.accentGreen : colors.textMuted}
                />
              </View>
            </LiquidGlassCard>
          </View>

          {/* ABOUT & TELEMETRY */}
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
              WORKSPACE & TELEMETRY
            </Text>
            <LiquidGlassCard style={styles.glassCard}>
              <View style={styles.aboutRow}>
                <Text style={[styles.aboutLabel, { color: colors.textMuted }]}>Mode Koneksi</Text>
                <Text style={[styles.aboutVal, { color: colors.accentGreen }]}>
                  {connectionMode === 'cloud' ? 'Direct Cloud (Internet)' : 'Local Server'}
                </Text>
              </View>
              <View style={styles.aboutRow}>
                <Text style={[styles.aboutLabel, { color: colors.textMuted }]}>
                  Akun Antigravity
                </Text>
                <Text style={[styles.aboutVal, { color: colors.textPrimary }]}>
                  {currentActiveAccount?.name || 'Default'}
                </Text>
              </View>
              <View style={styles.aboutRow}>
                <Text style={[styles.aboutLabel, { color: colors.textMuted }]}>Model Aktif</Text>
                <Text style={[styles.aboutVal, { color: colors.accentGreen }]}>
                  {connectionMode === 'cloud' ? cloudModel : activeModel}
                </Text>
              </View>
            </LiquidGlassCard>
          </View>
        </ScrollView>

        <AccountManagerModal
          visible={accountModalVisible}
          onClose={() => {
            setAccountModalVisible(false);
            setEditingAccount(null);
          }}
          onSave={handleSaveAccount}
          editingAccount={editingAccount}
        />

        <RouterAlertModal
          visible={showRouterModal}
          onClose={() => setShowRouterModal(false)}
          onStartSuccess={() => {
            setIsRouterRunning(true);
            loadModelsList();
          }}
        />
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
  content: {
    padding: 16,
    paddingBottom: 110,
  },
  section: {
    marginBottom: 20,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  sectionTitle: {
    fontSize: 10.5,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  refreshBtn: {
    padding: 4,
  },
  addAccountHeaderBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  addAccountHeaderText: {
    fontSize: 11,
    fontWeight: '700',
  },
  connectionToggleRow: {
    gap: 8,
  },
  connectionPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  connectionPillTitle: {
    fontSize: 13,
    fontWeight: '700',
  },
  connectionPillDesc: {
    fontSize: 11,
    marginTop: 2,
  },
  glassCard: {
    padding: 16,
    borderRadius: 18,
  },
  accountItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
  },
  accountItemLeft: {
    flex: 1,
    marginRight: 8,
  },
  accountHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  accountName: {
    fontSize: 13.5,
    fontWeight: '700',
  },
  activeBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  activeBadgeText: {
    fontSize: 8.5,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  accountKeyText: {
    fontSize: 11.5,
    marginTop: 2,
    fontFamily: 'monospace',
  },
  accountUrlText: {
    fontSize: 10.5,
    marginTop: 2,
  },
  accountActions: {
    flexDirection: 'row',
    gap: 6,
  },
  actionIconBtn: {
    padding: 6,
  },
  themeSelectorRow: {
    flexDirection: 'row',
    gap: 10,
  },
  themeCard: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  themeLabel: {
    fontSize: 12,
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  textInput: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    fontSize: 13,
  },
  saveBtn: {
    height: 44,
    paddingHorizontal: 18,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveBtnText: {
    fontWeight: '800',
    fontSize: 13,
  },
  testBtn: {
    marginTop: 14,
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  testBtnText: {
    fontWeight: '700',
    fontSize: 13,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusPillBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3.5,
    borderRadius: 8,
    borderWidth: 1,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  statusValue: {
    fontSize: 10.5,
    fontWeight: '800',
    letterSpacing: 0.5,
    fontFamily: 'monospace',
  },
  modelItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 14,
    marginBottom: 8,
    borderWidth: 1,
  },
  modelInfo: {
    flex: 1,
    marginRight: 10,
  },
  modelName: {
    fontSize: 13.5,
    fontWeight: '700',
  },
  modelDesc: {
    fontSize: 11.5,
    marginTop: 3,
    lineHeight: 16,
  },
  activeCheckCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  customModelSection: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: 1,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchLabel: {
    fontSize: 13.5,
    fontWeight: '700',
  },
  switchDesc: {
    fontSize: 11.5,
    marginTop: 2,
  },
  aboutRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  aboutLabel: {
    fontSize: 12,
  },
  aboutVal: {
    fontSize: 12,
    fontWeight: '600',
  },
});
