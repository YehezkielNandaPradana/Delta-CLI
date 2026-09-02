import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { Header } from '../../src/components/common/Header';
import { PageTransition } from '../../src/components/common/PageTransition';
import {
  getConversationHistory,
  clearConversationHistory,
  deleteHistoryItem,
} from '../../src/services/api/sessionApi';
import { useChatStore } from '../../src/store/useChatStore';
import { useSettingsStore } from '../../src/store/useSettingsStore';
import { useThemeColors } from '../../src/theme/theme';
import { formatTimestamp } from '../../src/utils/formatters';

interface CombinedHistoryItem {
  id: string;
  title: string;
  preview: string;
  source: 'session' | 'server';
  timestamp: number;
  messageCount?: number;
  rawSessionId?: string;
  serverHistoryId?: number;
}

export default function HistoryScreen() {
  const { colors, isDark } = useThemeColors();
  const { hapticEnabled } = useSettingsStore();
  const { sessions, currentSessionId, switchSession, deleteSession, loadSessions } = useChatStore();

  const [combinedItems, setCombinedItems] = useState<CombinedHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAndCombineHistory = async (showIndicator = true) => {
    if (showIndicator) setLoading(true);
    await loadSessions();

    const localList: CombinedHistoryItem[] = sessions.map((s) => {
      const lastMsg = s.messages && s.messages.length > 0 ? s.messages[s.messages.length - 1].text : 'Belum ada pesan';
      return {
        id: `local_${s.id}`,
        title: s.title || 'Obrolan Baru',
        preview: lastMsg.slice(0, 100).replace(/\n/g, ' '),
        source: 'session',
        timestamp: s.updatedAt || s.createdAt || Date.now(),
        messageCount: s.messages?.length || 0,
        rawSessionId: s.id,
      };
    });

    let serverList: CombinedHistoryItem[] = [];
    try {
      const res = await getConversationHistory(50);
      if (res.status === 'ok' && Array.isArray(res.history)) {
        serverList = res.history.map((h) => ({
          id: `server_${h.id}`,
          title: h.user_input || h.command || 'Perintah Terminal',
          preview: (h.ai_response || h.result || 'Respon berhasil').slice(0, 100).replace(/\n/g, ' '),
          source: 'server',
          timestamp: typeof h.timestamp === 'number' ? h.timestamp : Date.now(),
          serverHistoryId: typeof h.id === 'number' ? h.id : undefined,
        }));
      }
    } catch (_) {}

    const merged = [...localList, ...serverList].sort((a, b) => b.timestamp - a.timestamp);
    setCombinedItems(merged);
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchAndCombineHistory();
  }, [sessions.length]);

  const handleSelect = (item: CombinedHistoryItem) => {
    if (hapticEnabled) {
      Haptics.selectionAsync().catch(() => {});
    }

    if (item.source === 'session' && item.rawSessionId) {
      switchSession(item.rawSessionId);
    }
    router.navigate('/');
  };

  const handleDeleteItem = (item: CombinedHistoryItem) => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    }

    Alert.alert(
      'Hapus Sesi',
      `Hapus "${item.title}" dari riwayat?`,
      [
        { text: 'Batal', style: 'cancel' },
        {
          text: 'Hapus',
          style: 'destructive',
          onPress: async () => {
            if (item.source === 'session' && item.rawSessionId) {
              await deleteSession(item.rawSessionId);
            } else if (item.source === 'server' && item.serverHistoryId) {
              try {
                await deleteHistoryItem(item.serverHistoryId);
              } catch (_) {}
            }
            setCombinedItems((prev) => prev.filter((i) => i.id !== item.id));
            if (hapticEnabled) {
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
            }
          },
        },
      ]
    );
  };

  const handleClearAll = () => {
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    }

    Alert.alert(
      'Hapus Semua Riwayat',
      'Apakah Anda yakin ingin mengosongkan seluruh riwayat percakapan?',
      [
        { text: 'Batal', style: 'cancel' },
        {
          text: 'Hapus Semua',
          style: 'destructive',
          onPress: async () => {
            try {
              await clearConversationHistory();
            } catch (_) {}
            setCombinedItems([]);
            if (hapticEnabled) {
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]} edges={['top']}>
      <PageTransition style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header
          title="History"
          countBadge={combinedItems.length}
          subtitle="Riwayat Sesi Percakapan"
        />

        {/* Section Header Action Strip */}
        <View style={styles.sectionHeaderRow}>
          <Text style={[styles.sectionTitle, { color: colors.textMuted }]}>
            DAFTAR SESI OBROLAN
          </Text>

          {combinedItems.length > 0 && (
            <TouchableOpacity
              onPress={handleClearAll}
              style={[
                styles.clearAllBtn,
                {
                  backgroundColor: isDark ? 'rgba(239, 68, 68, 0.12)' : 'rgba(220, 38, 38, 0.08)',
                  borderColor: colors.border,
                },
              ]}
              activeOpacity={0.7}
            >
              <Feather name="trash-2" size={11} color={colors.error} />
              <Text style={[styles.clearAllText, { color: colors.error }]}>
                Hapus Semua
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Unified iOS Grouped Inset Table List */}
        <FlatList
          data={combinedItems}
          keyExtractor={(item) => item.id}
          onRefresh={() => {
            setRefreshing(true);
            fetchAndCombineHistory(false);
          }}
          refreshing={refreshing}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View
                style={[
                  styles.emptyIconCircle,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
              >
                <Ionicons name="chatbubbles-outline" size={24} color={colors.textMuted} />
              </View>
              <Text style={[styles.emptyTitle, { color: colors.textPrimary }]}>
                Belum Ada Riwayat Sesi
              </Text>
              <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
                Setiap obrolan dan sesi perintah Delta akan tersimpan di sini.
              </Text>
            </View>
          }
          renderItem={({ item, index }) => {
            const isCurrent = item.rawSessionId === currentSessionId;
            const isLast = index === combinedItems.length - 1;

            return (
              <View
                style={[
                  styles.groupedItemWrapper,
                  index === 0 && styles.firstItem,
                  isLast && styles.lastItem,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
              >
                <TouchableOpacity
                  onPress={() => handleSelect(item)}
                  style={styles.tableRow}
                  activeOpacity={0.7}
                >
                  {/* Left Icon Box */}
                  <View
                    style={[
                      styles.iconBox,
                      {
                        backgroundColor: isCurrent
                          ? (isDark ? '#333333' : '#E0E0E0')
                          : (isDark ? '#262626' : '#EAEAEA'),
                      },
                    ]}
                  >
                    <Ionicons
                      name={item.source === 'session' ? 'chatbubble-ellipses-outline' : 'terminal-outline'}
                      size={15}
                      color={isCurrent ? colors.textPrimary : colors.textSecondary}
                    />
                  </View>

                  {/* Center Text Info */}
                  <View style={styles.bodyWrapper}>
                    <View style={styles.topTitleRow}>
                      <Text
                        style={[
                          styles.sessionTitle,
                          {
                            color: colors.textPrimary,
                            fontWeight: isCurrent ? '700' : '600',
                          },
                        ]}
                        numberOfLines={1}
                      >
                        {item.title}
                      </Text>
                      {isCurrent && (
                        <View style={[styles.currentBadge, { backgroundColor: isDark ? '#333333' : '#E0E0E0' }]}>
                          <Text style={[styles.currentBadgeText, { color: colors.textPrimary }]}>AKTIF</Text>
                        </View>
                      )}
                    </View>

                    {item.preview ? (
                      <Text
                        style={[styles.previewText, { color: colors.textSecondary }]}
                        numberOfLines={1}
                      >
                        {item.preview}
                      </Text>
                    ) : null}

                    <Text style={[styles.metaTime, { color: colors.textMuted }]}>
                      {formatTimestamp(item.timestamp)}
                      {item.messageCount !== undefined ? ` • ${item.messageCount} pesan` : ''}
                    </Text>
                  </View>

                  {/* Delete Button */}
                  <TouchableOpacity
                    onPress={() => handleDeleteItem(item)}
                    hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                    style={styles.deleteBtn}
                  >
                    <Ionicons name="trash-outline" size={14} color={colors.textMuted} />
                  </TouchableOpacity>
                </TouchableOpacity>

                {!isLast && (
                  <View style={[styles.tableDivider, { backgroundColor: colors.border }]} />
                )}
              </View>
            );
          }}
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
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 6,
  },
  sectionTitle: {
    fontSize: 11.5,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  clearAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
  },
  clearAllText: {
    fontSize: 10.5,
    fontWeight: '600',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 4,
    paddingBottom: 90,
  },
  groupedItemWrapper: {
    borderLeftWidth: 1,
    borderRightWidth: 1,
    overflow: 'hidden',
  },
  firstItem: {
    borderTopLeftRadius: 14,
    borderTopRightRadius: 14,
    borderTopWidth: 1,
  },
  lastItem: {
    borderBottomLeftRadius: 14,
    borderBottomRightRadius: 14,
    borderBottomWidth: 1,
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  iconBox: {
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  bodyWrapper: {
    flex: 1,
    marginRight: 8,
  },
  topTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sessionTitle: {
    fontSize: 14,
    letterSpacing: -0.2,
    flex: 1,
  },
  currentBadge: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 4,
  },
  currentBadgeText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.4,
  },
  previewText: {
    fontSize: 12,
    marginTop: 2,
  },
  metaTime: {
    fontSize: 10.5,
    marginTop: 2,
  },
  deleteBtn: {
    padding: 4,
  },
  tableDivider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 58,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
    paddingHorizontal: 32,
  },
  emptyIconCircle: {
    width: 54,
    height: 54,
    borderRadius: 27,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
    letterSpacing: -0.2,
  },
  emptySubtitle: {
    fontSize: 12.5,
    textAlign: 'center',
    lineHeight: 18,
  },
});
