import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  TouchableWithoutFeedback,
  Platform,
} from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { AIModel } from '../../types/system';
import { getModels, selectModel } from '../../services/api/systemApi';
import { useSettingsStore } from '../../store/useSettingsStore';

// Fallback curated 9Router presets when server is starting up or returning empty
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
    name: 'deepseek/deepseek-v4-pro',
    description: 'DeepSeek V4 Pro - reasoning & code',
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
    name: 'openai/gpt-4o',
    description: 'OpenAI GPT-4o via 9Router',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'xai/grok-4',
    description: 'xAI Grok 4 via 9Router Gateway',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'qwen/qwen3-coder-plus',
    description: 'Qwen3 Coder Plus via 9Router',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'AntigravityCombo',
    description: 'Antigravity Multi-provider Hybrid Combo',
    provider: '9router',
    is_current: false,
  },
  {
    name: 'KiloCombo',
    description: 'KiloCombo High-speed Coding Router',
    provider: '9router',
    is_current: false,
  },
];

interface ModelPickerSheetProps {
  visible: boolean;
  onClose: () => void;
}

export const ModelPickerSheet: React.FC<ModelPickerSheetProps> = ({ visible, onClose }) => {
  const { colors, isDark } = useThemeColors();
  const { activeModel, setActiveModel, connectionMode, cloudModel, setCloudModel } = useSettingsStore();

  const [models, setModels] = useState<AIModel[]>(DEFAULT_9ROUTER_PRESETS);
  const [loading, setLoading] = useState(false);
  const [switching, setSwitching] = useState<string | null>(null);
  const [tab, setTab] = useState<'9router' | 'all'>('9router');

  useEffect(() => {
    if (visible) {
      loadModels();
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
      // Offline fallback: update locally
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

  const routerModels = models.filter(
    (m) =>
      m.provider === '9router' ||
      m.name.includes('/') ||
      m.name.toLowerCase().includes('combo') ||
      m.name.toLowerCase().includes('gemini') ||
      m.name.toLowerCase().includes('deepseek')
  );
  const displayedModels = tab === '9router' ? routerModels : models;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.backdrop}>
          <TouchableWithoutFeedback>
            <View
              style={[
                styles.sheetContainer,
                {
                  backgroundColor: colors.bgSecondary,
                  borderColor: colors.cardBorder,
                  borderTopColor: colors.cardSpecular,
                  shadowColor: isDark ? '#000000' : '#1e3a8a',
                },
              ]}
            >
              {/* Top Drag Indicator */}
              <View style={styles.header}>
                <View style={[styles.dragBar, { backgroundColor: colors.cardBorder }]} />
                <View style={styles.titleRow}>
                  <View style={styles.titleWithIcon}>
                    <Ionicons name="sparkles" size={16} color={colors.accentGreen} />
                    <Text style={[styles.title, { color: colors.textPrimary }]}>
                      Switch AI Model
                    </Text>
                  </View>
                  <TouchableOpacity
                    onPress={onClose}
                    style={[styles.closeBtn, { backgroundColor: colors.bgSurface }]}
                    accessibilityLabel="Close Model Picker"
                  >
                    <Feather name="x" size={16} color={colors.textMuted} />
                  </TouchableOpacity>
                </View>

                {/* Tabs */}
                <View style={styles.tabsRow}>
                  <TouchableOpacity
                    style={[
                      styles.tabBtn,
                      tab === '9router' && {
                        backgroundColor: colors.accentGreenSubtle,
                        borderColor: colors.accentGreen,
                      },
                    ]}
                    onPress={() => setTab('9router')}
                  >
                    <Text
                      style={[
                        styles.tabBtnText,
                        { color: tab === '9router' ? colors.accentGreen : colors.textMuted },
                      ]}
                    >
                      9Router ({routerModels.length})
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.tabBtn,
                      tab === 'all' && {
                        backgroundColor: colors.accentGreenSubtle,
                        borderColor: colors.accentGreen,
                      },
                    ]}
                    onPress={() => setTab('all')}
                  >
                    <Text
                      style={[
                        styles.tabBtnText,
                        { color: tab === 'all' ? colors.accentGreen : colors.textMuted },
                      ]}
                    >
                      All Models ({models.length})
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Models List */}
              {loading && models.length === 0 ? (
                <View style={styles.loadingBox}>
                  <ActivityIndicator size="small" color={colors.accentGreen} />
                  <Text style={[styles.loadingText, { color: colors.textMuted }]}>
                    Fetching available models...
                  </Text>
                </View>
              ) : (
                <ScrollView
                  style={styles.modelList}
                  contentContainerStyle={styles.modelListContent}
                  showsVerticalScrollIndicator={false}
                >
                  {displayedModels.map((m) => {
                    const isSelected =
                      m.name === activeModel ||
                      m.name.toLowerCase() === activeModel.toLowerCase() ||
                      m.is_current;
                    const isBusy = switching === m.name;

                    return (
                      <TouchableOpacity
                        key={m.name}
                        style={[
                          styles.modelCard,
                          {
                            backgroundColor: isSelected
                              ? colors.accentGreenSubtle
                              : colors.cardBg,
                            borderColor: isSelected
                              ? colors.accentGreen
                              : colors.cardBorder,
                          },
                        ]}
                        onPress={() => handleSelect(m.name)}
                        activeOpacity={0.7}
                        disabled={isBusy}
                      >
                        <View style={styles.modelCardLeft}>
                          <View style={styles.modelNameRow}>
                            <Text
                              style={[
                                styles.modelNameText,
                                {
                                  color: isSelected
                                    ? colors.accentGreen
                                    : colors.textPrimary,
                                  fontWeight: isSelected ? '700' : '600',
                                },
                              ]}
                              numberOfLines={1}
                            >
                              {m.name}
                            </Text>
                            {m.provider === '9router' && (
                              <View
                                style={[
                                  styles.providerBadge,
                                  { backgroundColor: colors.accentCyanSubtle },
                                ]}
                              >
                                <Text
                                  style={[
                                    styles.providerBadgeText,
                                    { color: colors.accentCyan },
                                  ]}
                                >
                                  9ROUTER
                                </Text>
                              </View>
                            )}
                          </View>
                          <Text
                            style={[styles.modelDescText, { color: colors.textMuted }]}
                            numberOfLines={1}
                          >
                            {m.description || `Provider: ${m.provider}`}
                          </Text>
                        </View>

                        {isBusy ? (
                          <ActivityIndicator size="small" color={colors.accentGreen} />
                        ) : isSelected ? (
                          <View
                            style={[
                              styles.checkBadge,
                              { backgroundColor: colors.accentGreen },
                            ]}
                          >
                            <Feather
                              name="check"
                              size={12}
                              color={isDark ? '#000000' : '#ffffff'}
                            />
                          </View>
                        ) : null}
                      </TouchableOpacity>
                    );
                  })}
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
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    borderWidth: 1,
    borderTopWidth: 1.5,
    maxHeight: '65%',
    minHeight: 380,
    paddingBottom: 28,
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: -6 },
        shadowOpacity: 0.25,
        shadowRadius: 16,
      },
      android: {
        elevation: 12,
      },
      web: {
        boxShadow: '0 -8px 32px rgba(0, 0, 0, 0.24)',
      } as any,
    }),
  },
  header: {
    paddingHorizontal: 18,
    paddingTop: 10,
    paddingBottom: 12,
  },
  dragBar: {
    width: 40,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  titleWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  closeBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  tabBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  tabBtnText: {
    fontSize: 12,
    fontWeight: '700',
  },
  loadingBox: {
    paddingVertical: 50,
    alignItems: 'center',
    gap: 10,
  },
  loadingText: {
    fontSize: 12,
    fontWeight: '500',
  },
  modelList: {
    flex: 1,
  },
  modelListContent: {
    paddingHorizontal: 18,
    paddingBottom: 16,
    gap: 8,
  },
  modelCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 16,
    borderWidth: 1,
  },
  modelCardLeft: {
    flex: 1,
    marginRight: 10,
  },
  modelNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  modelNameText: {
    fontSize: 13.5,
  },
  providerBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  providerBadgeText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.4,
  },
  modelDescText: {
    fontSize: 11.5,
    marginTop: 3,
  },
  checkBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
