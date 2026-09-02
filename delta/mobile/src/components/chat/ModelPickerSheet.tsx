import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  TouchableWithoutFeedback,
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

  const routerModels = models.filter(
    (m) =>
      m.provider === '9router' ||
      m.name.includes('/') ||
      m.name.toLowerCase().includes('combo') ||
      m.name.toLowerCase().includes('gemini') ||
      m.name.toLowerCase().includes('deepseek')
  );
  const displayedModels = tab === '9router' ? routerModels : models;
  const currentModelName = connectionMode === 'cloud' ? cloudModel : activeModel;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
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
                    { backgroundColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)' },
                  ]}
                />
                <View style={styles.titleRow}>
                  <View style={styles.titleWithIcon}>
                    <Ionicons name="sparkles" size={16} color={colors.textPrimary} />
                    <Text style={[styles.title, { color: colors.textPrimary }]}>
                      Switch AI Model
                    </Text>
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

                {/* iOS Style Segmented Filter Control */}
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
                    style={[
                      styles.segmentTab,
                      tab === '9router' && [
                        styles.segmentTabActive,
                        { backgroundColor: isDark ? '#262626' : '#FFFFFF' },
                      ],
                    ]}
                    onPress={() => {
                      if (hapticEnabled) Haptics.selectionAsync().catch(() => {});
                      setTab('9router');
                    }}
                    activeOpacity={0.8}
                  >
                    <Text
                      style={[
                        styles.segmentLabel,
                        {
                          color: tab === '9router' ? colors.textPrimary : colors.textMuted,
                          fontWeight: tab === '9router' ? '700' : '500',
                        },
                      ]}
                    >
                      9Router ({routerModels.length})
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[
                      styles.segmentTab,
                      tab === 'all' && [
                        styles.segmentTabActive,
                        { backgroundColor: isDark ? '#262626' : '#FFFFFF' },
                      ],
                    ]}
                    onPress={() => {
                      if (hapticEnabled) Haptics.selectionAsync().catch(() => {});
                      setTab('all');
                    }}
                    activeOpacity={0.8}
                  >
                    <Text
                      style={[
                        styles.segmentLabel,
                        {
                          color: tab === 'all' ? colors.textPrimary : colors.textMuted,
                          fontWeight: tab === 'all' ? '700' : '500',
                        },
                      ]}
                    >
                      Semua Model ({models.length})
                    </Text>
                  </TouchableOpacity>
                </View>
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
                  showsVerticalScrollIndicator={false}
                >
                  {/* iOS Grouped Table Inset */}
                  <View
                    style={[
                      styles.groupedTable,
                      {
                        backgroundColor: colors.bgSurface,
                        borderColor: colors.border,
                      },
                    ]}
                  >
                    {displayedModels.map((m, idx) => {
                      const isSelected =
                        m.name === currentModelName ||
                        m.name.toLowerCase() === currentModelName.toLowerCase() ||
                        m.is_current;
                      const isBusy = switching === m.name;
                      const isLast = idx === displayedModels.length - 1;

                      return (
                        <View key={m.name}>
                          <TouchableOpacity
                            style={[
                              styles.tableRow,
                              isSelected && {
                                backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
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
                                numberOfLines={1}
                              >
                                {m.description || 'General Purpose Model'}
                              </Text>
                            </View>

                            {/* Selection Status Checkmark */}
                            <View style={styles.checkmarkWrapper}>
                              {isBusy ? (
                                <ActivityIndicator size="small" color={colors.textPrimary} />
                              ) : isSelected ? (
                                <Ionicons name="checkmark-sharp" size={18} color={colors.textPrimary} />
                              ) : null}
                            </View>
                          </TouchableOpacity>

                          {!isLast && (
                            <View style={[styles.tableDivider, { backgroundColor: colors.border }]} />
                          )}
                        </View>
                      );
                    })}
                  </View>
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
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    borderWidth: 1,
    borderBottomWidth: 0,
    maxHeight: '80%',
    paddingBottom: Platform.OS === 'ios' ? 34 : 20,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.25,
        shadowRadius: 16,
      },
      android: {
        elevation: 12,
      },
    }),
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 10,
  },
  dragBar: {
    width: 36,
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
    fontSize: 17,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  closeBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  segmentedControl: {
    flexDirection: 'row',
    borderRadius: 10,
    borderWidth: 1,
    padding: 3,
  },
  segmentTab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 6,
    borderRadius: 7,
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
    fontSize: 12,
    letterSpacing: -0.2,
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
    paddingHorizontal: 16,
    paddingTop: 4,
    paddingBottom: 16,
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
  tableDivider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 14,
  },
});
