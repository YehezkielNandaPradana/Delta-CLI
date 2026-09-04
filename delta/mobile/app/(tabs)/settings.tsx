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
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { Header } from '../../src/components/common/Header';
import { PageTransition } from '../../src/components/common/PageTransition';
import { RouterAlertModal } from '../../src/components/chat/RouterAlertModal';
import { AccountManagerModal } from '../../src/components/settings/AccountManagerModal';
import { SkillsManagerModal } from '../../src/components/settings/SkillsManagerModal';
import { HermesTelegramModal } from '../../src/components/settings/HermesTelegramModal';
import { useSettingsStore, ThemeMode } from '../../src/store/useSettingsStore';
import { useSkillsStore } from '../../src/store/useSkillsStore';
import { test9RouterPing } from '../../src/services/api/systemApi';
import { AntigravityAccount } from '../../src/types/cloud';
import { useThemeColors } from '../../src/theme/theme';

const CLOUD_MODEL_PRESETS = [
  { name: 'ag/gemini-3.7-flash-high', description: 'Antigravity Dynamic Router Pipeline', tag: 'ROUTER' },
  { name: 'ag/gemini-3.8-flash-high', description: 'Next-Gen Ultra Fast 3.8 Reasoning', tag: 'TURBO' },
  { name: 'gemini-1.5-pro', description: 'Deep Cybersecurity Reasoning & Analysis', tag: 'PRO' },
  { name: 'gemini-1.5-flash', description: 'High Stability & Generous Quota', tag: 'FREE' },
];

export default function SettingsScreen() {
  const { colors, isDark } = useThemeColors();
  const {
    serverUrl,
    routerHostUrl,
    hapticEnabled,
    theme,
    connectionMode,
    cloudModel,
    setServerUrl,
    setRouterHostUrl,
    setHapticEnabled,
    setTheme,
    setConnectionMode,
    setCloudModel,
    addAccount,
    updateAccount,
    getActiveAccount,
  } = useSettingsStore();

  const [inputServerUrl, setInputServerUrl] = useState(serverUrl);
  const [inputRouterHostUrl, setInputRouterHostUrl] = useState(routerHostUrl);
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [showSkillsModal, setShowSkillsModal] = useState(false);
  const [showTelegramModal, setShowTelegramModal] = useState(false);
  const [showRouterModal, setShowRouterModal] = useState(false);
  const [isTestingPing, setIsTestingPing] = useState(false);
  const [pingResult, setPingResult] = useState<{ success: boolean; latency?: number; text?: string } | null>(null);

  const { skills } = useSkillsStore();
  const activeSkillsCount = skills.filter((s) => s.isActive).length;

  useEffect(() => {
    setInputServerUrl(serverUrl);
    setInputRouterHostUrl(routerHostUrl);
  }, [serverUrl, routerHostUrl]);

  const activeAccount = getActiveAccount();

  const handleSaveHost = async () => {
    await setServerUrl(inputServerUrl);
    await setRouterHostUrl(inputRouterHostUrl);
    if (activeAccount) {
      await updateAccount(activeAccount.id, { baseUrl: inputRouterHostUrl });
    }
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }
    Alert.alert('Tersimpan', 'Konfigurasi 9Router tunnel & host berhasil diperbarui.');
  };

  const handleTestPing = async () => {
    setIsTestingPing(true);
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    }
    try {
      const res = await test9RouterPing(inputRouterHostUrl || undefined, activeAccount?.apiKey);
      if (res.success) {
        setPingResult({ success: true, latency: res.latencyMs, text: `${res.latencyMs} ms` });
        Alert.alert('9Router Online', `Terhubung ke: ${res.url}\nLatency: ${res.latencyMs} ms\nModels: ${res.modelsCount}`);
      } else {
        setPingResult({ success: false, text: 'Offline' });
        Alert.alert('Koneksi Gagal', res.error || '9Router tunnel tidak merespon.');
      }
    } catch (e: any) {
      setPingResult({ success: false, text: 'Error' });
      Alert.alert('Ping Error', e.message);
    } finally {
      setIsTestingPing(false);
    }
  };

  const handleSelectModel = (modelName: string) => {
    if (hapticEnabled) {
      Haptics.selectionAsync().catch(() => {});
    }
    setCloudModel(modelName);
  };

  const handleSaveAccount = async (accData: Omit<AntigravityAccount, 'id'>, editId?: string) => {
    if (editId) {
      await updateAccount(editId, accData);
    } else {
      await addAccount(accData);
    }
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]} edges={['top']}>
      <PageTransition style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header title="Settings" subtitle="Konfigurasi & Preferensi Sistem" />

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.contentContainer}
          showsVerticalScrollIndicator={false}
        >
          {/* OVERVIEW HERO STATUS CARD */}
          <View style={[styles.heroStatusCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            <View style={styles.heroStatusItem}>
              <Text style={[styles.heroStatusLabel, { color: colors.textMuted }]}>MODE</Text>
              <View style={styles.heroStatusValueRow}>
                <View
                  style={[
                    styles.statusDot,
                    {
                      backgroundColor:
                        connectionMode === 'telegram'
                          ? '#0088cc'
                          : connectionMode === 'cloud'
                          ? '#22C55E'
                          : '#3B82F6',
                    },
                  ]}
                />
                <Text style={[styles.heroStatusValue, { color: colors.textPrimary }]}>
                  {connectionMode === 'telegram'
                    ? 'Hermes Telegram'
                    : connectionMode === 'cloud'
                    ? 'Cloud Router'
                    : 'CLI Local'}
                </Text>
              </View>
            </View>

            <View style={[styles.heroDivider, { backgroundColor: colors.border }]} />

            <View style={styles.heroStatusItem}>
              <Text style={[styles.heroStatusLabel, { color: colors.textMuted }]}>ACTIVE MODEL</Text>
              <Text
                style={[styles.heroStatusValue, { color: colors.textPrimary }]}
                numberOfLines={1}
                ellipsizeMode="tail"
              >
                {cloudModel.replace('ag/', '')}
              </Text>
            </View>

            <View style={[styles.heroDivider, { backgroundColor: colors.border }]} />

            <View style={styles.heroStatusItem}>
              <Text style={[styles.heroStatusLabel, { color: colors.textMuted }]}>AKUN AI</Text>
              <Text
                style={[styles.heroStatusValue, { color: activeAccount ? colors.textPrimary : colors.textMuted }]}
                numberOfLines={1}
              >
                {activeAccount ? activeAccount.name : 'Unlinked'}
              </Text>
            </View>
          </View>

          {/* SECTION 1: KONEKSI EKSKLUSIF */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            PILIHAN KONEKSI ENGINE (HANYA SATU AKTIF)
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {/* OPSI 1: Telegram Hermes Bot */}
            <TouchableOpacity
              onPress={() => setConnectionMode('telegram')}
              style={[
                styles.clickableRow,
                connectionMode === 'telegram' && {
                  backgroundColor: isDark ? 'rgba(0, 136, 204, 0.1)' : 'rgba(0, 136, 204, 0.06)',
                },
              ]}
              activeOpacity={0.7}
            >
              <View style={styles.rowLeft}>
                <View
                  style={[
                    styles.iconBox,
                    { backgroundColor: connectionMode === 'telegram' ? '#0088cc' : (isDark ? '#1C1C1E' : '#F2F2F7') },
                  ]}
                >
                  <Ionicons
                    name="paper-plane"
                    size={17}
                    color={connectionMode === 'telegram' ? '#ffffff' : '#0088cc'}
                  />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary, fontWeight: connectionMode === 'telegram' ? '700' : '600' }]}>
                    Hermes Bot Telegram
                  </Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    Eksklusif ke Bot Telegram Anda (Nonaktifkan server lain)
                  </Text>
                </View>
              </View>
              <Ionicons
                name={connectionMode === 'telegram' ? 'radio-button-on' : 'radio-button-off'}
                size={20}
                color={connectionMode === 'telegram' ? '#0088cc' : colors.textMuted}
              />
            </TouchableOpacity>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* OPSI 2: Mode Cloud / 9Router */}
            <TouchableOpacity
              onPress={() => setConnectionMode('cloud')}
              style={[
                styles.clickableRow,
                connectionMode === 'cloud' && {
                  backgroundColor: isDark ? 'rgba(34, 197, 94, 0.1)' : 'rgba(34, 197, 94, 0.06)',
                },
              ]}
              activeOpacity={0.7}
            >
              <View style={styles.rowLeft}>
                <View
                  style={[
                    styles.iconBox,
                    { backgroundColor: connectionMode === 'cloud' ? '#22C55E' : (isDark ? '#1C1C1E' : '#F2F2F7') },
                  ]}
                >
                  <Ionicons
                    name="cloud-outline"
                    size={17}
                    color={connectionMode === 'cloud' ? '#ffffff' : colors.textPrimary}
                  />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary, fontWeight: connectionMode === 'cloud' ? '700' : '600' }]}>
                    Cloud Router / 9Router
                  </Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    Langsung via Google AI & Router Gateway
                  </Text>
                </View>
              </View>
              <Ionicons
                name={connectionMode === 'cloud' ? 'radio-button-on' : 'radio-button-off'}
                size={20}
                color={connectionMode === 'cloud' ? '#22C55E' : colors.textMuted}
              />
            </TouchableOpacity>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* OPSI 3: CLI Local Server */}
            <TouchableOpacity
              onPress={() => setConnectionMode('local')}
              style={[
                styles.clickableRow,
                connectionMode === 'local' && {
                  backgroundColor: isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.06)',
                },
              ]}
              activeOpacity={0.7}
            >
              <View style={styles.rowLeft}>
                <View
                  style={[
                    styles.iconBox,
                    { backgroundColor: connectionMode === 'local' ? '#3B82F6' : (isDark ? '#1C1C1E' : '#F2F2F7') },
                  ]}
                >
                  <Ionicons
                    name="server-outline"
                    size={17}
                    color={connectionMode === 'local' ? '#ffffff' : colors.textPrimary}
                  />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary, fontWeight: connectionMode === 'local' ? '700' : '600' }]}>
                    Local CLI Backend
                  </Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    Terhubung ke Host Local Server Delta
                  </Text>
                </View>
              </View>
              <Ionicons
                name={connectionMode === 'local' ? 'radio-button-on' : 'radio-button-off'}
                size={20}
                color={connectionMode === 'local' ? '#3B82F6' : colors.textMuted}
              />
            </TouchableOpacity>
          </View>

          {/* DETAIL KONEKSI SESUAI MODE YANG AKTIF */}
          {connectionMode === 'telegram' ? (
            <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border, marginTop: 12 }]}>
              <TouchableOpacity
                onPress={() => setShowTelegramModal(true)}
                style={styles.clickableRow}
                activeOpacity={0.7}
              >
                <View style={styles.rowLeft}>
                  <View style={[styles.iconBox, { backgroundColor: 'rgba(0, 136, 204, 0.15)' }]}>
                    <Ionicons name="settings-outline" size={17} color="#0088cc" />
                  </View>
                  <View style={styles.rowTextCol}>
                    <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>
                      Pengaturan Token & Chat ID Hermes
                    </Text>
                    <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                      {useSettingsStore.getState().telegramBotToken ? 'Bot terhubung & siap digunakan' : 'Klik untuk isi Bot Token'}
                    </Text>
                  </View>
                </View>
                <Feather name="chevron-right" size={16} color={colors.textMuted} />
              </TouchableOpacity>
            </View>
          ) : (
            <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border, marginTop: 12 }]}>
              {/* Server Backend Host */}
              <View style={styles.formRow}>
                <View style={styles.formRowHeader}>
                  <View style={styles.formLabelGroup}>
                    <View style={[styles.iconBoxMini, { backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7' }]}>
                      <Ionicons name="server-outline" size={13} color={colors.textPrimary} />
                    </View>
                    <Text style={[styles.formLabelTitle, { color: colors.textPrimary }]}>Host Backend Server</Text>
                  </View>
                  <Text style={[styles.badgePort, { color: colors.textMuted }]}>PORT 8080</Text>
                </View>
                <TextInput
                  value={inputServerUrl}
                  onChangeText={setInputServerUrl}
                  placeholder="http://192.168.1.6:8080"
                  placeholderTextColor={colors.textMuted}
                  style={[
                    styles.textInputModern,
                    {
                      color: colors.textPrimary,
                      borderColor: colors.border,
                      backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA',
                    },
                  ]}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              <View style={[styles.divider, { backgroundColor: colors.border }]} />

              {/* Custom 9Router Host IP / Tunnel */}
              <View style={styles.formRow}>
                <View style={styles.formRowHeader}>
                  <View style={styles.formLabelGroup}>
                    <View style={[styles.iconBoxMini, { backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7' }]}>
                      <Ionicons name="git-network-outline" size={13} color={colors.textPrimary} />
                    </View>
                    <Text style={[styles.formLabelTitle, { color: colors.textPrimary }]}>9Router Host / Tunnel URL</Text>
                  </View>
                  <View style={styles.portPingRow}>
                    {pingResult && (
                      <View
                        style={[
                          styles.pingBadge,
                          {
                            backgroundColor: pingResult.success
                              ? isDark
                                ? 'rgba(34, 197, 94, 0.15)'
                                : '#DCFCE7'
                              : isDark
                              ? 'rgba(239, 68, 68, 0.15)'
                              : '#FEE2E2',
                          },
                        ]}
                      >
                        <Text
                          style={[
                            styles.pingBadgeText,
                            { color: pingResult.success ? '#22C55E' : '#EF4444' },
                          ]}
                        >
                          {pingResult.text}
                        </Text>
                      </View>
                    )}
                    <Text style={[styles.badgePort, { color: colors.textMuted }]}>TUNNEL/20128</Text>
                  </View>
                </View>
                <TextInput
                  value={inputRouterHostUrl}
                  onChangeText={setInputRouterHostUrl}
                  placeholder="https://rurpq7a.abc-tunnel.us/v1"
                  placeholderTextColor={colors.textMuted}
                  style={[
                    styles.textInputModern,
                    {
                      color: colors.textPrimary,
                      borderColor: colors.border,
                      backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA',
                    },
                  ]}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              <View style={[styles.divider, { backgroundColor: colors.border }]} />

              {/* Integrated Action Buttons */}
              <View style={styles.btnRow}>
                <TouchableOpacity
                  onPress={handleTestPing}
                  disabled={isTestingPing}
                  style={[
                    styles.secondaryActionBtn,
                    {
                      borderColor: colors.border,
                      backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7',
                    },
                  ]}
                  activeOpacity={0.7}
                >
                  {isTestingPing ? (
                    <ActivityIndicator size="small" color={colors.textPrimary} />
                  ) : (
                    <>
                      <Ionicons name="flash-outline" size={14} color={colors.textPrimary} />
                      <Text style={[styles.btnText, { color: colors.textPrimary }]}>Test Ping</Text>
                    </>
                  )}
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={handleSaveHost}
                  style={[styles.primaryActionBtn, { backgroundColor: colors.textPrimary }]}
                  activeOpacity={0.8}
                >
                  <Ionicons name="checkmark-sharp" size={15} color={colors.bgPrimary} />
                  <Text style={[styles.btnText, { color: colors.bgPrimary }]}>Simpan Perubahan</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* SECTION 2: AKUN & EKSTENSI */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            AKUN & EKSTENSI
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {/* Active Account Row */}
            <TouchableOpacity
              onPress={() => setShowAccountModal(true)}
              style={styles.clickableRow}
              activeOpacity={0.7}
            >
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7' }]}>
                  <Ionicons name="key-outline" size={17} color={colors.textPrimary} />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>
                    {activeAccount ? activeAccount.name : 'Hubungkan Akun AI'}
                  </Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    {activeAccount?.apiKey ? 'API Key Terdaftar & Siap Pakai' : 'Google AI Studio / Custom Provider'}
                  </Text>
                </View>
              </View>
              <View style={styles.trailingGroup}>
                <View
                  style={[
                    styles.statusPill,
                    {
                      backgroundColor: activeAccount
                        ? isDark
                          ? 'rgba(34, 197, 94, 0.15)'
                          : '#DCFCE7'
                        : isDark
                        ? 'rgba(255, 255, 255, 0.08)'
                        : '#F2F2F7',
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.statusPillText,
                      { color: activeAccount ? '#22C55E' : colors.textMuted },
                    ]}
                  >
                    {activeAccount ? 'Terhubung' : 'Setup'}
                  </Text>
                </View>
                <Feather name="chevron-right" size={16} color={colors.textMuted} />
              </View>
            </TouchableOpacity>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Coding Skills Manager Row */}
            <TouchableOpacity
              onPress={() => setShowSkillsModal(true)}
              style={styles.clickableRow}
              activeOpacity={0.7}
            >
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7' }]}>
                  <Ionicons name="construct-outline" size={17} color={colors.textPrimary} />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>
                    Skill Coding & Desain Delta
                  </Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    UI/UX Pro, Clean Arch & Prompting Superpowers
                  </Text>
                </View>
              </View>
              <View style={styles.trailingGroup}>
                <View
                  style={[
                    styles.statusPill,
                    { backgroundColor: isDark ? '#2C2C2E' : '#E5E5EA' },
                  ]}
                >
                  <Text style={[styles.statusPillText, { color: colors.textPrimary }]}>
                    {activeSkillsCount} Aktif
                  </Text>
                </View>
                <Feather name="chevron-right" size={16} color={colors.textMuted} />
              </View>
            </TouchableOpacity>
          </View>

          {/* SECTION 3: MODEL AI DEFAULT */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            DEFAULT INTELLIGENCE MODEL
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {CLOUD_MODEL_PRESETS.map((preset, index) => {
              const isSelected = cloudModel === preset.name;
              const isLast = index === CLOUD_MODEL_PRESETS.length - 1;

              return (
                <View key={preset.name}>
                  <TouchableOpacity
                    onPress={() => handleSelectModel(preset.name)}
                    style={[
                      styles.presetItemRow,
                      isSelected && {
                        backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
                      },
                    ]}
                    activeOpacity={0.65}
                  >
                    <View style={styles.presetLeftWrapper}>
                      <View style={styles.presetHeaderLine}>
                        <Text
                          style={[
                            styles.presetCodeText,
                            {
                              color: colors.textPrimary,
                              fontWeight: isSelected ? '700' : '500',
                            },
                          ]}
                        >
                          {preset.name}
                        </Text>
                        <View
                          style={[
                            styles.presetTagBadge,
                            {
                              backgroundColor: isDark ? '#262626' : '#E5E5E5',
                            },
                          ]}
                        >
                          <Text style={[styles.presetTagText, { color: colors.textPrimary }]}>
                            {preset.tag}
                          </Text>
                        </View>
                      </View>
                      <Text style={[styles.presetSummaryText, { color: colors.textMuted }]}>
                        {preset.description}
                      </Text>
                    </View>

                    <View style={styles.radioCheckContainer}>
                      {isSelected ? (
                        <View style={[styles.checkCircleActive, { backgroundColor: colors.textPrimary }]}>
                          <Ionicons name="checkmark-sharp" size={13} color={colors.bgPrimary} />
                        </View>
                      ) : (
                        <View style={[styles.checkCircleInactive, { borderColor: colors.border }]} />
                      )}
                    </View>
                  </TouchableOpacity>

                  {!isLast && <View style={[styles.divider, { backgroundColor: colors.border }]} />}
                </View>
              );
            })}
          </View>

          {/* SECTION 4: PREFERENSI SISTEM */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            PREFERENSI SISTEM
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {/* Theme Selector */}
            <View style={styles.rowItem}>
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7' }]}>
                  <Ionicons name={isDark ? 'moon-outline' : 'sunny-outline'} size={17} color={colors.textPrimary} />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Tema Tampilan</Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>Palet warna sistem</Text>
                </View>
              </View>

              <View
                style={[
                  styles.themeSelectorCapsule,
                  {
                    backgroundColor: isDark ? '#1C1C1E' : '#E5E5EA',
                  },
                ]}
              >
                {(['dark', 'light', 'system'] as ThemeMode[]).map((t) => {
                  const isCur = theme === t;
                  return (
                    <TouchableOpacity
                      key={t}
                      onPress={() => setTheme(t)}
                      style={[
                        styles.themeOptionPill,
                        isCur && {
                          backgroundColor: isDark ? '#2C2C2E' : '#FFFFFF',
                          shadowColor: '#000',
                          shadowOffset: { width: 0, height: 1 },
                          shadowOpacity: 0.12,
                          shadowRadius: 2,
                          elevation: 2,
                        },
                      ]}
                      activeOpacity={0.8}
                    >
                      <Text
                        style={[
                          styles.themeOptionText,
                          {
                            color: isCur ? colors.textPrimary : colors.textMuted,
                            fontWeight: isCur ? '700' : '500',
                          },
                        ]}
                      >
                        {t === 'dark' ? 'Dark' : t === 'light' ? 'Light' : 'Auto'}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Haptic Feedback */}
            <View style={styles.rowItem}>
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7' }]}>
                  <Ionicons name="hardware-chip-outline" size={17} color={colors.textPrimary} />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Haptic Feedback</Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    Respon getaran taktil pada tombol
                  </Text>
                </View>
              </View>
              <Switch
                value={hapticEnabled}
                onValueChange={setHapticEnabled}
                trackColor={{ false: isDark ? '#2C2C2E' : '#E5E5EA', true: colors.textPrimary }}
                thumbColor={isDark ? '#000000' : '#FFFFFF'}
              />
            </View>
          </View>

          {/* SECTION 5: TENTANG & DIAGNOSTIK */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            TENTANG & DIAGNOSTIK
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {/* Router Diagnostics Trigger */}
            <TouchableOpacity
              onPress={() => setShowRouterModal(true)}
              style={styles.clickableRow}
              activeOpacity={0.7}
            >
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#1C1C1E' : '#F2F2F7' }]}>
                  <Ionicons name="pulse-outline" size={17} color={colors.textPrimary} />
                </View>
                <View style={styles.rowTextCol}>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Pusat Diagnostik 9Router</Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    Cek status gateway, port 20128 & re-start
                  </Text>
                </View>
              </View>
              <Feather name="chevron-right" size={16} color={colors.textMuted} />
            </TouchableOpacity>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Version */}
            <View style={styles.rowItem}>
              <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Versi Aplikasi</Text>
              <Text style={[styles.rowValueMuted, { color: colors.textMuted }]}>1.0.0 (Build 2026)</Text>
            </View>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Architecture */}
            <View style={styles.rowItem}>
              <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Arsitektur Engine</Text>
              <Text style={[styles.rowValueMuted, { color: colors.textMuted }]}>Delta Hybrid CLI & 9Router</Text>
            </View>
          </View>
        </ScrollView>

        {/* Modals */}
        <AccountManagerModal
          visible={showAccountModal}
          onClose={() => setShowAccountModal(false)}
          onSave={handleSaveAccount}
          editingAccount={activeAccount}
        />

        <SkillsManagerModal
          visible={showSkillsModal}
          onClose={() => setShowSkillsModal(false)}
        />

        <HermesTelegramModal
          visible={showTelegramModal}
          onClose={() => setShowTelegramModal(false)}
        />

        <RouterAlertModal
          visible={showRouterModal}
          onClose={() => setShowRouterModal(false)}
        />
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
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 96,
  },
  heroStatusCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 8,
  },
  heroStatusItem: {
    flex: 1,
    alignItems: 'center',
  },
  heroStatusLabel: {
    fontSize: 9.5,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 3,
  },
  heroStatusValueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  heroStatusValue: {
    fontSize: 12,
    fontWeight: '700',
  },
  heroDivider: {
    width: 1,
    height: 24,
  },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 6,
    marginTop: 18,
    paddingHorizontal: 6,
  },
  groupCard: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: 'hidden',
  },
  rowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 13,
  },
  clickableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 13,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
    marginRight: 8,
  },
  rowTextCol: {
    flex: 1,
  },
  iconBox: {
    width: 34,
    height: 34,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBoxMini: {
    width: 22,
    height: 22,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowTitle: {
    fontSize: 14.5,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  rowSubtitle: {
    fontSize: 11.5,
    marginTop: 1.5,
    lineHeight: 15,
  },
  rowValueMuted: {
    fontSize: 13,
    fontWeight: '500',
  },
  trailingGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusPillText: {
    fontSize: 10.5,
    fontWeight: '700',
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 60,
  },
  formRow: {
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  formRowHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 7,
  },
  formLabelGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  formLabelTitle: {
    fontSize: 13,
    fontWeight: '600',
  },
  portPingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  badgePort: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.4,
  },
  pingBadge: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 4,
  },
  pingBadgeText: {
    fontSize: 9.5,
    fontWeight: '700',
  },
  textInputModern: {
    height: 38,
    borderRadius: 9,
    borderWidth: 1,
    paddingHorizontal: 12,
    fontSize: 12.5,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  btnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  primaryActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 38,
    borderRadius: 9,
    gap: 5,
  },
  secondaryActionBtn: {
    width: 105,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 38,
    borderRadius: 9,
    borderWidth: 1,
    gap: 5,
  },
  btnText: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  presetItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  presetLeftWrapper: {
    flex: 1,
    marginRight: 10,
  },
  presetHeaderLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  presetCodeText: {
    fontSize: 13,
    letterSpacing: -0.2,
  },
  presetTagBadge: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 4,
  },
  presetTagText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.4,
  },
  presetSummaryText: {
    fontSize: 11,
    marginTop: 2,
    lineHeight: 15,
  },
  radioCheckContainer: {
    width: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkCircleActive: {
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkCircleInactive: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
  },
  themeSelectorCapsule: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 8,
    padding: 2,
  },
  themeOptionPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  themeOptionText: {
    fontSize: 11.5,
  },
});
