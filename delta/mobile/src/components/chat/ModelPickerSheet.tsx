import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  TouchableWithoutFeedback,
  TextInput,
  Platform,
} from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { AIModel } from '../../types/system';
import { getModels, selectModel } from '../../services/api/systemApi';
import { useSettingsStore } from '../../store/useSettingsStore';
import { useThemeColors } from '../../theme/theme';
import { BlurBackdrop } from '../common/BlurBackdrop';

const DEFAULT_9ROUTER_PRESETS: AIModel[] = [
  {
    name: 'ag/gemini-3.7-flash-high',
    description: 'Gemini 3.7 Flash High via Antigravity in 9Router',
    provider: '9router',
    is_current: true,
  },
  {
    name: 'ag/gemini-3.8-flash-high',
    description: 'Gemini 3.8 Flash High - Ultra-Fast 2026 Reasoning Engine',
    provider: '9router',
    is_current: false,
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
    description: 'DeepSeek V4 Flash - fast, efficient & agile coder',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'deepseek/deepseek-v4-pro',
    description: 'DeepSeek V4 Pro - high-precision reasoning & pentest',
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
    name: 'anthropic/claude-3-7-sonnet',
    description: 'Claude 3.7 Sonnet - hybrid thinking & coding',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'openai/gpt-4o',
    description: 'OpenAI GPT-4o multimodal flagship model',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'openai/gpt-4o-mini',
    description: 'OpenAI GPT-4o Mini lightweight via 9Router',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'AntigravityCombo',
    description: 'Antigravity Multi-provider Hybrid Automatic Fallback',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'gemini-1.5-pro',
    description: 'Google AI Studio Gemini 1.5 Pro direct cloud connection',
    provider: 'google',
    is_current: false,
  },
  {
    name: 'gemini-1.5-flash',
    description: 'Google AI Studio Gemini 1.5 Flash fast & high quota',
    provider: 'google',
    is_current: false,
  },
];

type FilterCategory = 'all' | '9router' | 'gemini' | 'deepseek' | 'claude' | 'openai' | 'antigravity';

const FILTER_TABS: { id: FilterCategory; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { id: 'all', label: 'Semua', icon: 'apps-outline' },
  { id: '9router', label: '9Router', icon: 'git-network-outline' },
  { id: 'antigravity', label: 'Antigravity', icon: 'planet-outline' },
  { id: 'gemini', label: 'Gemini', icon: 'logo-google' },
  { id: 'deepseek', label: 'DeepSeek', icon: 'flash-outline' },
  { id: 'claude', label: 'Claude', icon: 'sparkles-outline' },
  { id: 'openai', label: 'OpenAI', icon: 'hardware-chip-outline' },
];

interface ModelPickerSheetProps {
  visible: boolean;
  onClose: () => void;
}

export const ModelPickerSheet: React.FC<ModelPickerSheetProps> = ({ visible, onClose }) => {
  const { colors, isDark } = useThemeColors();
  const { activeModel, setActiveModel, connectionMode, cloudModel, setCloudModel, hapticEnabled } = useSettingsStore();

  const [models, setModels] = useState<AIModel[]>(DEFAULT_9ROUTER_PRESETS);
  const [loading, setLoading] = useState(false);
  const [switching, setSwitching] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<FilterCategory>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (visible) {
      loadModels();
      setSearchQuery('');
    }
  }, [visible]);

  const loadModels = async () => {
    setLoading(true);
    try {
      const res = await getModels();
      if (res.status === 'ok' && res.models && res.models.length > 0) {
        setModels(res.models);
      } else {
        setModels(DEFAULT_9ROUTER_PRESETS);
      }
    } catch (e) {
      setModels(DEFAULT_9ROUTER_PRESETS);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (modelName: string) => {
    if (hapticEnabled) {
      Haptics.selectionAsync().catch(() => {});
    }
    setSwitching(modelName);
    try {
      if (connectionMode === 'cloud') {
        await setCloudModel(modelName);
        onClose();
        return;
      }
      const res = await selectModel(modelName);
      if (res.status === 'ok') {
        await setActiveModel(modelName);
        setTimeout(() => {
          onClose();
        }, 150);
      } else {
        await setActiveModel(modelName);
        onClose();
      }
    } catch (err: any) {
      if (connectionMode === 'cloud') {
        await setCloudModel(modelName);
      } else {
        await setActiveModel(modelName);
      }
      onClose();
    } finally {
      setSwitching(null);
    }
  };

  const currentModelName = connectionMode === 'cloud' ? cloudModel : activeModel;

  const matchesCategory = (m: AIModel, cat: FilterCategory): boolean => {
    if (cat === 'all') return true;
    const nameLower = m.name.toLowerCase();
    const provLower = (m.provider || '').toLowerCase();

    if (cat === '9router') {
      return (
        provLower.includes('9router') ||
        nameLower.includes('/') ||
        nameLower.includes('combo')
      );
    }
    if (cat === 'antigravity') {
      return (
        nameLower.startsWith('ag/') ||
        nameLower.includes('antigravity') ||
        provLower.includes('antigravity')
      );
    }
    if (cat === 'gemini') {
      return nameLower.includes('gemini') || nameLower.includes('google');
    }
    if (cat === 'deepseek') {
      return nameLower.includes('deepseek');
    }
    if (cat === 'claude') {
      return nameLower.includes('claude') || nameLower.includes('anthropic');
    }
    if (cat === 'openai') {
      return nameLower.includes('gpt') || nameLower.includes('openai');
    }
    return true;
  };

  const filteredModels = useMemo(() => {
    return models.filter((m) => {
      if (!matchesCategory(m, activeTab)) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const nameLower = m.name.toLowerCase();
        const descLower = (m.description || '').toLowerCase();
        const provLower = (m.provider || '').toLowerCase();
        return nameLower.includes(q) || descLower.includes(q) || provLower.includes(q);
      }
      return true;
    });
  }, [models, activeTab, searchQuery]);

  const getTabCount = (cat: FilterCategory) => {
    return models.filter((m) => matchesCategory(m, cat)).length;
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.backdrop}>
          <BlurBackdrop intensity={45} />
          <TouchableWithoutFeedback>
            <View
              style={[
                styles.sheetContainer,
                {
                  backgroundColor: colors.bgSecondary,
                  borderColor: colors.border,
                },
              ]}
            >
              {/* iOS Grabber */}
              <View style={styles.header}>
                <View
                  style={[
                    styles.dragBar,
                    { backgroundColor: isDark ? 'rgba(255, 255, 255, 0.25)' : 'rgba(0, 0, 0, 0.2)' },
                  ]}
                />
                <View style={styles.titleRow}>
                  <View style={styles.titleWithIcon}>
                    <View style={[styles.sparkleBox, { backgroundColor: isDark ? '#262626' : '#EAEAEA' }]}>
                      <Ionicons name="sparkles" size={15} color={colors.textPrimary} />
                    </View>
                    <View>
                      <Text style={[styles.title, { color: colors.textPrimary }]}>
                        Switch AI Model
                      </Text>
                      <Text style={[styles.subtitle, { color: colors.textMuted }]}>
                        {models.length} model terdaftar di sistem
                      </Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    onPress={onClose}
                    style={[
                      styles.closeBtn,
                      {
                        backgroundColor: colors.bgSurface,
                        borderColor: colors.border,
                      },
                    ]}
                    accessibilityLabel="Close Model Picker"
                  >
                    <Feather name="x" size={15} color={colors.textSecondary} />
                  </TouchableOpacity>
                </View>

                {/* Search Bar */}
                <View
                  style={[
                    styles.searchBar,
                    {
                      backgroundColor: isDark ? '#141414' : '#EFEFF0',
                      borderColor: colors.border,
                    },
                  ]}
                >
                  <Ionicons name="search-outline" size={14} color={colors.textMuted} style={styles.searchIcon} />
                  <TextInput
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                    placeholder="Cari model AI (gemini, claude, deepseek)..."
                    placeholderTextColor={colors.textMuted}
                    style={[styles.searchInput, { color: colors.textPrimary }]}
                    autoCapitalize="none"
                    autoCorrect={false}
                  />
                  {searchQuery.length > 0 && (
                    <TouchableOpacity
                      onPress={() => setSearchQuery('')}
                      hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                    >
                      <Ionicons name="close-circle-sharp" size={16} color={colors.textMuted} />
                    </TouchableOpacity>
                  )}
                </View>

                {/* Horizontal Category Chips */}
                <ScrollView
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.filterPillsContainer}
                >
                  {FILTER_TABS.map((tabItem) => {
                    const isTabActive = activeTab === tabItem.id;
                    const count = getTabCount(tabItem.id);
                    return (
                      <TouchableOpacity
                        key={tabItem.id}
                        onPress={() => {
                          if (hapticEnabled) Haptics.selectionAsync().catch(() => {});
                          setActiveTab(tabItem.id);
                        }}
                        style={[
                          styles.filterPill,
                          {
                            backgroundColor: isTabActive
                              ? (isDark ? '#2E2E2E' : '#FFFFFF')
                              : (isDark ? '#181818' : '#F2F2F4'),
                            borderColor: isTabActive ? colors.textPrimary : colors.border,
                          },
                        ]}
                        activeOpacity={0.7}
                      >
                        <Ionicons
                          name={tabItem.icon}
                          size={12}
                          color={isTabActive ? colors.textPrimary : colors.textMuted}
                        />
                        <Text
                          style={[
                            styles.filterPillText,
                            {
                              color: isTabActive ? colors.textPrimary : colors.textMuted,
                              fontWeight: isTabActive ? '700' : '500',
                            },
                          ]}
                        >
                          {tabItem.label} ({count})
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </ScrollView>
              </View>

              {/* Models List */}
              {loading && models.length === 0 ? (
                <View style={styles.loadingBox}>
                  <ActivityIndicator size="small" color={colors.textPrimary} />
                  <Text style={[styles.loadingText, { color: colors.textMuted }]}>
                    Memuat daftar model...
                  </Text>
                </View>
              ) : (
                <ScrollView
                  style={styles.modelList}
                  contentContainerStyle={styles.modelListContent}
                  showsVerticalScrollIndicator={true}
                >
                  {filteredModels.length === 0 ? (
                    <View style={styles.emptyBox}>
                      <Ionicons name="file-tray-outline" size={32} color={colors.textMuted} />
                      <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
                        Tidak ada model yang cocok
                      </Text>
                      <Text style={[styles.emptySubtext, { color: colors.textMuted }]}>
                        Coba kata kunci lain atau pilih tab filter berbeda.
                      </Text>
                    </View>
                  ) : (
                    <View
                      style={[
                        styles.groupedTable,
                        {
                          backgroundColor: colors.bgSurface,
                          borderColor: colors.border,
                        },
                      ]}
                    >
                      {filteredModels.map((m, idx) => {
                        const isSelected =
                          m.name === currentModelName ||
                          m.name.toLowerCase() === currentModelName.toLowerCase() ||
                          m.is_current;
                        const isBusy = switching === m.name;
                        const isLast = idx === filteredModels.length - 1;

                        return (
                          <View key={m.name}>
                            <TouchableOpacity
                              style={[
                                styles.tableRow,
                                isSelected && {
                                  backgroundColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.04)',
                                },
                              ]}
                              onPress={() => handleSelect(m.name)}
                              activeOpacity={0.65}
                            >
                              <View style={styles.modelCardLeft}>
                                <View style={styles.modelNameRow}>
                                  <Text
                                    style={[
                                      styles.modelNameText,
                                      {
                                        color: colors.textPrimary,
                                        fontWeight: isSelected ? '700' : '500',
                                      },
                                    ]}
                                    numberOfLines={1}
                                  >
                                    {m.name}
                                  </Text>
                                  {m.provider && (
                                    <View
                                      style={[
                                        styles.providerBadge,
                                        {
                                          backgroundColor: isDark ? '#262626' : '#E5E5E5',
                                        },
                                      ]}
                                    >
                                      <Text style={[styles.providerBadgeText, { color: colors.textPrimary }]}>
                                        {m.provider.toUpperCase()}
                                      </Text>
                                    </View>
                                  )}
                                </View>
                                <Text
                                  style={[styles.modelDescText, { color: colors.textMuted }]}
                                  numberOfLines={2}
                                >
                                  {m.description || 'General Purpose Model'}
                                </Text>
                              </View>

                              {/* Selection Status Checkmark */}
                              <View style={styles.checkmarkWrapper}>
                                {isBusy ? (
                                  <ActivityIndicator size="small" color={colors.textPrimary} />
                                ) : isSelected ? (
                                  <View style={[styles.selectedCheckCircle, { backgroundColor: colors.textPrimary }]}>
                                    <Ionicons name="checkmark-sharp" size={13} color={colors.bgPrimary} />
                                  </View>
                                ) : (
                                  <View style={[styles.unselectedCircle, { borderColor: colors.border }]} />
                                )}
                              </View>
                            </TouchableOpacity>

                            {!isLast && (
                              <View style={[styles.tableDivider, { backgroundColor: colors.border }]} />
                            )}
                          </View>
                        );
                      })}
                    </View>
                  )}
                </ScrollView>
              )}
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
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    width: '100%',
    height: Platform.OS === 'ios' ? '82%' : '85%',
    borderTopLeftRadius: 26,
    borderTopRightRadius: 26,
    borderWidth: 1,
    borderBottomWidth: 0,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.28,
        shadowRadius: 18,
      },
      android: {
        elevation: 16,
      },
    }),
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 8,
  },
  dragBar: {
    width: 36,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 10,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  titleWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sparkleBox: {
    width: 30,
    height: 30,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 17,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 11,
    marginTop: 1,
  },
  closeBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 38,
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 10,
    marginBottom: 10,
  },
  searchIcon: {
    marginRight: 6,
  },
  searchInput: {
    flex: 1,
    fontSize: 12.5,
    paddingVertical: 0,
  },
  filterPillsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingBottom: 4,
  },
  filterPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
  },
  filterPillText: {
    fontSize: 11.5,
    letterSpacing: -0.2,
  },
  loadingBox: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 10,
  },
  loadingText: {
    fontSize: 12,
    fontWeight: '500',
  },
  emptyBox: {
    paddingVertical: 50,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  emptyText: {
    fontSize: 13.5,
    fontWeight: '700',
  },
  emptySubtext: {
    fontSize: 11.5,
  },
  modelList: {
    flex: 1,
  },
  modelListContent: {
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: Platform.OS === 'ios' ? 44 : 36,
  },
  groupedTable: {
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  modelCardLeft: {
    flex: 1,
    marginRight: 10,
  },
  modelNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  modelNameText: {
    fontSize: 13.5,
    letterSpacing: -0.2,
    flexShrink: 1,
  },
  providerBadge: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 4,
  },
  providerBadgeText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.4,
  },
  modelDescText: {
    fontSize: 11.5,
    marginTop: 2,
    lineHeight: 16,
  },
  checkmarkWrapper: {
    width: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectedCheckCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  unselectedCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
  },
  tableDivider: {
    height: StyleSheet.hairlineWidth,
  },
});
