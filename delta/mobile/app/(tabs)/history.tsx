import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Feather, Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { Header } from '../../src/components/common/Header';
import {
  getConversationHistory,
  clearConversationHistory,
  deleteHistoryItem,
} from '../../src/services/api/sessionApi';
import { ConversationHistoryItem } from '../../src/types/chat';
import { useChatStore } from '../../src/store/useChatStore';
import { useSettingsStore } from '../../src/store/useSettingsStore';
import { useThemeColors } from '../../src/theme/theme';
import { LiquidGlassCard } from '../../src/components/common/LiquidGlassCard';
import { formatTimestamp, formatDate, truncateText } from '../../src/utils/formatters';

// Skeleton Shimmer Loading Card
const SkeletonCard = () => {
  const { colors, isDark } = useThemeColors();
  const shimmerAnim = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, {
          toValue: 0.8,
          duration: 750,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0.3,
          duration: 750,
          useNativeDriver: true,
        }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);

  const blockBg = isDark ? 'rgba(255, 255, 255, 0.07)' : 'rgba(0, 0, 0, 0.06)';

  return (
    <LiquidGlassCard style={styles.card}>
      <View style={styles.cardHeader}>
        <Animated.View
          style={[styles.skeletonBlock, { width: 110, height: 12, backgroundColor: blockBg, opacity: shimmerAnim }]}
        />
        <Animated.View
          style={[styles.skeletonBlock, { width: 60, height: 18, borderRadius: 6, backgroundColor: blockBg, opacity: shimmerAnim }]}
        />
      </View>
      <Animated.View
        style={[styles.skeletonBlock, { width: '85%', height: 15, marginVertical: 6, backgroundColor: blockBg, opacity: shimmerAnim }]}
      />
      <Animated.View
        style={[styles.skeletonBlock, { width: '65%', height: 13, backgroundColor: blockBg, opacity: shimmerAnim }]}
      />
    </LiquidGlassCard>
  );
};

export default function HistoryScreen() {
  const { colors, isDark } = useThemeColors();
  const { hapticEnabled } = useSettingsStore();
  const { addMessage } = useChatStore();

  const [history, setHistory] = useState<ConversationHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | number | null>(null);

  const loadHistory = async (showLoadingIndicator = true) => {
    if (showLoadingIndicator) setLoading(true);
    try {
      const res = await getConversationHistory(100);
      if (res.status === 'ok' && res.history) {
        setHistory(res.history);
      }
    } catch (e) {
      console.warn('Failed to load history', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  // Delete single history session
  const handleDeleteItem = (item: ConversationHistoryItem) => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    }

    Alert.alert(
      'Hapus Sesi Percakapan',
      'Apakah Anda yakin ingin menghapus sesi percakapan ini?',
      [
        { text: 'Batal', style: 'cancel' },
        {
          text: 'Hapus',
          style: 'destructive',
          onPress: async () => {
            const itemId = item.id;
            setDeletingId(itemId);
            try {
              if (typeof itemId === 'number' || (typeof itemId === 'string' && !isNaN(Number(itemId)))) {
                await deleteHistoryItem(Number(itemId));
              }
              setHistory((prev) => prev.filter((h) => h.id !== itemId));
              if (hapticEnabled) {
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
              }
            } catch (err: any) {
              Alert.alert('Gagal Menghapus', err.message || 'Terjadi kesalahan saat menghapus sesi');
            } finally {
              setDeletingId(null);
            }
          },
        },
      ]
    );
  };

  // Clear all history sessions
  const handleClearAll = () => {
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    }

    Alert.alert(
      'Hapus Seluruh Histori',
      'Tindakan ini akan menghapus semua riwayat sesi percakapan Delta di server. Lanjutkan?',
      [
        { text: 'Batal', style: 'cancel' },
        {
          text: 'Hapus Semua',
          style: 'destructive',
          onPress: async () => {
            try {
              await clearConversationHistory();
              setHistory([]);
              if (hapticEnabled) {
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
              }
            } catch (err: any) {
              Alert.alert('Error', err.message);
            }
          },
        },
      ]
    );
  };

  const handleSelect = (item: ConversationHistoryItem) => {
    if (hapticEnabled) {
      Haptics.selectionAsync().catch(() => {});
    }
    const rawPrompt = item.user_input || item.command || '';
    const rawResponse = item.ai_response || item.result || '';

    if (rawPrompt) {
      addMessage({
        sender: 'user',
        text: rawPrompt,
        timestamp: typeof item.timestamp === 'number' ? item.timestamp : Date.now(),
      });
    }
    if (rawResponse) {
      addMessage({
        sender: 'delta',
        text: rawResponse,
        timestamp: typeof item.timestamp === 'number' ? item.timestamp : Date.now(),
      });
    }
    router.navigate('/');
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]} edges={['top']}>
      <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header title="DELTA" subtitle="Conversation History" />

        {/* TOP BAR ACTION STRIP */}
        <View style={[styles.actionStrip, { borderBottomColor: colors.cardBorder }]}>
          <View style={styles.stripLeft}>
            <Ionicons name="time-outline" size={15} color={colors.accentGreen} />
            <Text style={[styles.stripTitle, { color: colors.textPrimary }]}>
              {loading ? 'MEMUAT SESI...' : `${history.length} SESI TERSIMPAN`}
            </Text>
          </View>

          {history.length > 0 && !loading ? (
            <TouchableOpacity
              onPress={handleClearAll}
              style={[
                styles.clearAllBtn,
                {
                  backgroundColor: colors.accentRedSubtle,
                  borderColor: colors.accentRed,
                },
              ]}
              activeOpacity={0.7}
              accessibilityRole="button"
              accessibilityLabel="Hapus semua sesi"
            >
              <Feather name="trash-2" size={12} color={colors.accentRed} />
              <Text style={[styles.clearAllText, { color: colors.accentRed }]}>
                Hapus Semua
              </Text>
            </TouchableOpacity>
          ) : null}
        </View>

        {/* LIST OR SKELETON */}
        {loading && !refreshing ? (
          <View style={styles.list}>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </View>
        ) : (
          <FlatList
            data={history}
            keyExtractor={(item, index) => item.id?.toString() || index.toString()}
            onRefresh={() => {
              setRefreshing(true);
              loadHistory(false);
            }}
            refreshing={refreshing}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.list}
            ListEmptyComponent={
              <LiquidGlassCard style={styles.emptyCard}>
                <View
                  style={[
                    styles.emptyIconCircle,
                    {
                      backgroundColor: colors.bgSecondary,
                      borderColor: colors.cardBorder,
                    },
                  ]}
                >
                  <Feather name="message-square" size={26} color={colors.textMuted} />
                </View>
                <Text style={[styles.emptyTitle, { color: colors.textPrimary }]}>
                  Belum Ada Riwayat Sesi
                </Text>
                <Text style={[styles.emptySubtitle, { color: colors.textMuted }]}>
                  Setiap percakapan dan perintah yang dijalankan akan tercatat di sini secara otomatis.
                </Text>
              </LiquidGlassCard>
            }
            renderItem={({ item }) => {
              const promptText = item.user_input || item.command || 'Perintah tanpa teks';
              const responseText = item.ai_response || item.result || '';
              const isDeleting = deletingId === item.id;

              return (
                <LiquidGlassCard
                  style={isDeleting ? [styles.card, { opacity: 0.5 }] : styles.card}
                  onPress={() => handleSelect(item)}
                >
                  {/* Card Header Row */}
                  <View style={styles.cardHeader}>
                    <View style={styles.metaRow}>
                      <Ionicons name="calendar-outline" size={12} color={colors.textMuted} />
                      <Text style={[styles.cardDate, { color: colors.textMuted }]}>
                        {formatDate(item.timestamp)} · {formatTimestamp(item.timestamp)}
                      </Text>
                    </View>

                    <View style={styles.cardHeaderRight}>
                      {item.target ? (
                        <View
                          style={[
                            styles.targetBadge,
                            {
                              backgroundColor: colors.accentGreenSubtle,
                              borderColor: colors.accentGreen,
                            },
                          ]}
                        >
                          <Text style={[styles.targetText, { color: colors.accentGreen }]}>
                            {item.target}
                          </Text>
                        </View>
                      ) : null}

                      {/* Single Item Delete Button */}
                      <TouchableOpacity
                        style={[
                          styles.deleteItemBtn,
                          {
                            backgroundColor: colors.bgSurface,
                            borderColor: colors.cardBorder,
                          },
                        ]}
                        onPress={() => handleDeleteItem(item)}
                        hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                        accessibilityRole="button"
                        accessibilityLabel="Hapus sesi ini"
                      >
                        <Feather name="trash" size={12} color={colors.textMuted} />
                      </TouchableOpacity>
                    </View>
                  </View>

                  {/* Prompt Preview */}
                  <View style={styles.promptRow}>
                    <View style={[styles.userBadgeDot, { backgroundColor: colors.accentGreen }]} />
                    <Text
                      style={[styles.userPrompt, { color: colors.textPrimary }]}
                      numberOfLines={2}
                    >
                      {truncateText(promptText, 130)}
                    </Text>
                  </View>

                  {/* AI Response Preview */}
                  {responseText ? (
                    <View style={[styles.responseBox, { backgroundColor: colors.bgSurface, borderColor: colors.cardBorder }]}>
                      <Text
                        style={[styles.aiSnippet, { color: colors.textSecondary }]}
                        numberOfLines={2}
                      >
                        {truncateText(responseText, 160)}
                      </Text>
                    </View>
                  ) : null}
                </LiquidGlassCard>
              );
            }}
          />
        )}
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
  actionStrip: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  stripLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  stripTitle: {
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.8,
    fontFamily: 'monospace',
  },
  clearAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
  },
  clearAllText: {
    fontSize: 10.5,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  list: {
    padding: 16,
    paddingBottom: 110,
    gap: 12,
  },
  skeletonBlock: {
    borderRadius: 4,
  },
  card: {
    padding: 14,
    borderRadius: 18,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  cardDate: {
    fontSize: 11,
    fontWeight: '600',
    fontFamily: 'monospace',
  },
  cardHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  targetBadge: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
  },
  targetText: {
    fontSize: 9.5,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  deleteItemBtn: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  promptRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 6,
  },
  userBadgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 6,
  },
  userPrompt: {
    flex: 1,
    fontSize: 13.5,
    fontWeight: '700',
    lineHeight: 19,
  },
  responseBox: {
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 4,
  },
  aiSnippet: {
    fontSize: 12,
    lineHeight: 17,
  },
  emptyCard: {
    padding: 36,
    borderRadius: 20,
    alignItems: 'center',
    gap: 8,
    marginTop: 20,
  },
  emptyIconCircle: {
    width: 56,
    height: 56,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  emptySubtitle: {
    fontSize: 12.5,
    textAlign: 'center',
    lineHeight: 18,
    maxWidth: 280,
  },
});
