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
import { useSettingsStore, ThemeMode } from '../../src/store/useSettingsStore';
import { useSkillsStore } from '../../src/store/useSkillsStore';
import { useConnectionStore } from '../../src/store/useConnectionStore';
import { test9RouterPing } from '../../src/services/api/systemApi';
import { AntigravityAccount } from '../../src/types/cloud';
import { useThemeColors } from '../../src/theme/theme';

const CLOUD_MODEL_PRESETS = [
  { name: 'gemini-1.5-pro', description: 'Google Gemini 1.5 Pro (Deep Cybersecurity Reasoning)', tag: 'PRO' },
  { name: 'gemini-2.0-flash', description: 'Google Gemini 2.0 Flash (Next-Gen Ultra Fast)', tag: 'FAST' },
  { name: 'gemini-1.5-flash', description: 'Google Gemini 1.5 Flash (High Stability & Free Quota)', tag: 'FREE' },
  { name: 'ag/gemini-3.7-flash-high', description: 'Antigravity Gemini 3.7 Flash High Router', tag: 'ROUTER' },
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
  const [showRouterModal, setShowRouterModal] = useState(false);
  const [isTestingPing, setIsTestingPing] = useState(false);

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
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }
    Alert.alert('Tersimpan', 'Konfigurasi host jaringan berhasil diperbarui.');
  };

  const handleTestPing = async () => {
    setIsTestingPing(true);
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    }
    try {
      const res = await test9RouterPing(inputRouterHostUrl || undefined);
      if (res.success) {
        Alert.alert('9Router Online', `Terhubung ke: ${res.url}\nLatency: ${res.latencyMs} ms\nModels: ${res.modelsCount}`);
      } else {
        Alert.alert('Koneksi Gagal', res.error || '9Router tidak merespon pada port 20128');
      }
    } catch (e: any) {
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
          {/* SECTION 1: KONEKSI & MODE */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            KONEKSI & MODE OPERASI
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {/* Mode Cloud / Direct */}
            <View style={styles.rowItem}>
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#262626' : '#E5E5E5' }]}>
                  <Ionicons name="cloud-outline" size={17} color={colors.textPrimary} />
                </View>
                <View>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Mode Cloud / 9Router</Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    {connectionMode === 'cloud' ? 'Langsung via Google AI & 9Router' : 'Terhubung ke Local CLI Backend'}
                  </Text>
                </View>
              </View>
              <Switch
                value={connectionMode === 'cloud'}
                onValueChange={(val) => setConnectionMode(val ? 'cloud' : 'local')}
                trackColor={{ false: isDark ? '#262626' : '#E5E5E5', true: colors.textPrimary }}
                thumbColor={isDark ? '#000000' : '#FFFFFF'}
              />
            </View>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Server Backend Host */}
            <View style={styles.inputRow}>
              <View style={styles.inputLabelRow}>
                <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Host Backend Server</Text>
                <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>IP Delta CLI / FastAPI (Port 8080)</Text>
              </View>
              <TextInput
                value={inputServerUrl}
                onChangeText={setInputServerUrl}
                placeholder="http://192.168.1.6:8080"
                placeholderTextColor={colors.textMuted}
                style={[styles.textInput, { color: colors.textPrimary, borderColor: colors.border, backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA' }]}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Custom 9Router Host IP */}
            <View style={styles.inputRow}>
              <View style={styles.inputLabelRow}>
                <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Custom 9Router IP (Port 20128)</Text>
                <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>Loopback / PRoot / Laptop Gateway</Text>
              </View>
              <TextInput
                value={inputRouterHostUrl}
                onChangeText={setInputRouterHostUrl}
                placeholder="http://192.168.1.6:20128"
                placeholderTextColor={colors.textMuted}
                style={[styles.textInput, { color: colors.textPrimary, borderColor: colors.border, backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA' }]}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Action Buttons Row */}
            <View style={styles.btnRow}>
              <TouchableOpacity
                onPress={handleTestPing}
                disabled={isTestingPing}
                style={[styles.secondaryActionBtn, { borderColor: colors.border, backgroundColor: isDark ? '#1F1F1F' : '#F0F0F0' }]}
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
                <Ionicons name="checkmark" size={15} color={colors.bgPrimary} />
                <Text style={[styles.btnText, { color: colors.bgPrimary }]}>Simpan Host</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* SECTION 2: AKUN & MODEL AI */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            AKUN & MODEL AI
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {/* Active Account Row */}
            <TouchableOpacity
              onPress={() => setShowAccountModal(true)}
              style={styles.clickableRow}
              activeOpacity={0.7}
            >
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#262626' : '#E5E5E5' }]}>
                  <Ionicons name="key-outline" size={17} color={colors.textPrimary} />
                </View>
                <View>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>
                    {activeAccount ? activeAccount.name : 'Hubungkan Akun AI'}
                  </Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    {activeAccount?.apiKey ? 'API Key Terhubung' : 'Google AI Studio / Antigravity'}
                  </Text>
                </View>
              </View>
              <View style={styles.rowRightChevron}>
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
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#262626' : '#E5E5E5' }]}>
                  <Ionicons name="construct-outline" size={17} color={colors.textPrimary} />
                </View>
                <View>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>
                    Skill Coding & Desain Delta
                  </Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>
                    {activeSkillsCount} skill aktif (UI/UX Pro, Clean Arch, dll.)
                  </Text>
                </View>
              </View>
              <View style={styles.rowRightChevron}>
                <Feather name="chevron-right" size={16} color={colors.textMuted} />
              </View>
            </TouchableOpacity>

            <View style={[styles.divider, { backgroundColor: colors.border }]} />

            {/* Model Presets List (iOS Radio List Table) */}
            <View style={styles.presetSectionWrapper}>
              <Text style={[styles.rowTitleSmall, { color: colors.textSecondary }]}>
                PRESET MODEL DEFAULT
              </Text>

              <View style={styles.presetList}>
                {CLOUD_MODEL_PRESETS.map((preset, index) => {
                  const isSelected = cloudModel === preset.name;
                  const isLast = index === CLOUD_MODEL_PRESETS.length - 1;

                  return (
                    <View key={preset.name}>
                      <TouchableOpacity
                        onPress={() => handleSelectModel(preset.name)}
                        style={[
                          styles.presetRow,
                          isSelected && {
                            backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
                          },
                        ]}
                        activeOpacity={0.65}
                      >
                        <View style={styles.presetLeftContent}>
                          <View style={styles.presetNameRow}>
                            <Text
                              style={[
                                styles.presetNameText,
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
                                styles.tagPill,
                                {
                                  backgroundColor: isDark ? '#262626' : '#E5E5E5',
                                },
                              ]}
                            >
                              <Text style={[styles.tagPillText, { color: colors.textPrimary }]}>
                                {preset.tag}
                              </Text>
                            </View>
                          </View>
                          <Text style={[styles.presetDescText, { color: colors.textMuted }]}>
                            {preset.description}
                          </Text>
                        </View>

                        {/* Right Checkmark */}
                        <View style={styles.checkmarkWrapper}>
                          {isSelected && (
                            <Ionicons name="checkmark-sharp" size={18} color={colors.textPrimary} />
                          )}
                        </View>
                      </TouchableOpacity>

                      {!isLast && (
                        <View style={[styles.presetDivider, { backgroundColor: colors.border }]} />
                      )}
                    </View>
                  );
                })}
              </View>
            </View>
          </View>

          {/* SECTION 3: PREFERENSI SISTEM */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            PREFERENSI SISTEM
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            {/* Theme Selector */}
            <View style={styles.rowItem}>
              <View style={styles.rowLeft}>
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#262626' : '#E5E5E5' }]}>
                  <Ionicons name={isDark ? 'moon-outline' : 'sunny-outline'} size={17} color={colors.textPrimary} />
                </View>
                <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Tema Tampilan</Text>
              </View>

              <View style={styles.themeSelectorGroup}>
                {(['dark', 'light', 'system'] as ThemeMode[]).map((t) => {
                  const isCur = theme === t;
                  return (
                    <TouchableOpacity
                      key={t}
                      onPress={() => setTheme(t)}
                      style={[
                        styles.themeTab,
                        {
                          backgroundColor: isCur ? (isDark ? '#262626' : '#FFFFFF') : 'transparent',
                        },
                      ]}
                    >
                      <Text
                        style={[
                          styles.themeTabText,
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
                <View style={[styles.iconBox, { backgroundColor: isDark ? '#262626' : '#E5E5E5' }]}>
                  <Ionicons name="hardware-chip-outline" size={17} color={colors.textPrimary} />
                </View>
                <View>
                  <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Haptic Feedback</Text>
                  <Text style={[styles.rowSubtitle, { color: colors.textSecondary }]}>Getaran responsif pada tombol</Text>
                </View>
              </View>
              <Switch
                value={hapticEnabled}
                onValueChange={setHapticEnabled}
                trackColor={{ false: isDark ? '#262626' : '#E5E5E5', true: colors.textPrimary }}
                thumbColor={isDark ? '#000000' : '#FFFFFF'}
              />
            </View>
          </View>

          {/* SECTION 4: TENTANG DELTA */}
          <Text style={[styles.sectionHeader, { color: colors.textMuted }]}>
            TENTANG DELTA
          </Text>

          <View style={[styles.groupCard, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            <View style={styles.rowItem}>
              <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Versi Aplikasi</Text>
              <Text style={[styles.rowValue, { color: colors.textMuted }]}>1.0.0 (Build 2026)</Text>
            </View>
            <View style={[styles.divider, { backgroundColor: colors.border }]} />
            <View style={styles.rowItem}>
              <Text style={[styles.rowTitle, { color: colors.textPrimary }]}>Arsitektur Engine</Text>
              <Text style={[styles.rowValue, { color: colors.textMuted }]}>Delta Hybrid CLI & 9Router</Text>
            </View>
          </View>
        </ScrollView>

        {/* Account Manager Modal */}
        <AccountManagerModal
          visible={showAccountModal}
          onClose={() => setShowAccountModal(false)}
          onSave={handleSaveAccount}
          editingAccount={activeAccount}
        />

        {/* Skills Manager Modal */}
        <SkillsManagerModal
          visible={showSkillsModal}
          onClose={() => setShowSkillsModal(false)}
        />

        {/* Router Alert Modal */}
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
    paddingBottom: 90,
  },
  sectionHeader: {
    fontSize: 11.5,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
    marginTop: 14,
    paddingHorizontal: 4,
  },
  groupCard: {
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
  },
  rowItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  clickableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  rowRightChevron: {
    marginLeft: 8,
  },
  iconBox: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowTitle: {
    fontSize: 14.5,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  rowTitleSmall: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.4,
    marginBottom: 8,
    paddingHorizontal: 14,
  },
  rowSubtitle: {
    fontSize: 11.5,
    marginTop: 1,
  },
  rowValue: {
    fontSize: 13,
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 58,
  },
  inputRow: {
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  inputLabelRow: {
    marginBottom: 6,
  },
  textInput: {
    height: 38,
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 10,
    fontSize: 13,
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
    height: 36,
    borderRadius: 8,
    gap: 4,
  },
  secondaryActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 36,
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
  },
  btnText: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  presetSectionWrapper: {
    paddingTop: 10,
  },
  presetList: {
    overflow: 'hidden',
  },
  presetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  presetLeftContent: {
    flex: 1,
    marginRight: 10,
  },
  presetNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  presetNameText: {
    fontSize: 13.5,
    letterSpacing: -0.2,
  },
  tagPill: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 4,
  },
  tagPillText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.4,
  },
  presetDescText: {
    fontSize: 11.5,
    marginTop: 2,
    lineHeight: 16,
  },
  checkmarkWrapper: {
    width: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  presetDivider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 14,
  },
  themeSelectorGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 8,
    padding: 2,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(128, 128, 128, 0.2)',
  },
  themeTab: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
  },
  themeTabText: {
    fontSize: 12,
  },
});
