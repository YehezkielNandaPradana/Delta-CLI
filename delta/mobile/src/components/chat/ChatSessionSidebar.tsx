import React from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TouchableWithoutFeedback,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { useChatStore } from '../../store/useChatStore';
import { BlurBackdrop } from '../common/BlurBackdrop';
import { formatTimestamp } from '../../utils/formatters';

interface ChatSessionSidebarProps {
  visible: boolean;
  onClose: () => void;
}

export const ChatSessionSidebar: React.FC<ChatSessionSidebarProps> = ({
  visible,
  onClose,
}) => {
  const { colors, isDark } = useThemeColors();
  const {
    sessions,
    currentSessionId,
    createSession,
    switchSession,
    deleteSession,
  } = useChatStore();

  const handleNewChat = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    createSession();
    onClose();
  };

  const handleSelectSession = (sessionId: string) => {
    Haptics.selectionAsync().catch(() => {});
    switchSession(sessionId);
    onClose();
  };

  const handleDeleteSession = (sessionId: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    deleteSession(sessionId);
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.overlay}>
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
              <View style={styles.grabberWrapper}>
                <View
                  style={[
                    styles.grabber,
                    { backgroundColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)' },
                  ]}
                />
              </View>

              {/* Sheet Header */}
              <View style={styles.headerRow}>
                <View>
                  <Text style={[styles.headerTitle, { color: colors.textPrimary }]}>
                    Sesi Obrolan
                  </Text>
                  <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
                    Riwayat percakapan Delta ({sessions.length} sesi)
                  </Text>
                </View>

                <TouchableOpacity
                  onPress={handleNewChat}
                  style={[
                    styles.newChatBtn,
                    {
                      backgroundColor: colors.textPrimary,
                    },
                  ]}
                  activeOpacity={0.8}
                >
                  <Ionicons name="add" size={16} color={colors.bgPrimary} />
                  <Text style={[styles.newChatBtnText, { color: colors.bgPrimary }]}>Baru</Text>
                </TouchableOpacity>
              </View>

              {/* iOS Grouped Inset Sessions Table */}
              <ScrollView
                style={styles.sessionsList}
                contentContainerStyle={styles.sessionsContent}
                showsVerticalScrollIndicator={false}
              >
                <View
                  style={[
                    styles.groupedTable,
                    {
                      backgroundColor: colors.bgSurface,
                      borderColor: colors.border,
                    },
                  ]}
                >
                  {sessions.map((session, index) => {
                    const isActive = session.id === currentSessionId;
                    const messageCount = session.messages?.length || 0;
                    const isLast = index === sessions.length - 1;

                    return (
                      <View key={session.id}>
                        <TouchableOpacity
                          onPress={() => handleSelectSession(session.id)}
                          style={[
                            styles.sessionRow,
                            isActive && {
                              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
                            },
                          ]}
                          activeOpacity={0.65}
                        >
                          {/* Left Icon Box */}
                          <View
                            style={[
                              styles.iconBox,
                              {
                                backgroundColor: isActive
                                  ? (isDark ? '#333333' : '#E0E0E0')
                                  : (isDark ? '#262626' : '#EAEAEA'),
                              },
                            ]}
                          >
                            <Ionicons
                              name={isActive ? 'chatbubble-ellipses' : 'chatbubble-outline'}
                              size={15}
                              color={isActive ? colors.textPrimary : colors.textSecondary}
                            />
                          </View>

                          {/* Center Text Info */}
                          <View style={styles.sessionCardContent}>
                            <View style={styles.sessionTitleRow}>
                              <Text
                                style={[
                                  styles.sessionTitle,
                                  {
                                    color: colors.textPrimary,
                                    fontWeight: isActive ? '700' : '500',
                                  },
                                ]}
                                numberOfLines={1}
                              >
                                {session.title || 'Obrolan Baru'}
                              </Text>
                            </View>

                            <Text style={[styles.metaText, { color: colors.textMuted }]}>
                              {formatTimestamp(session.updatedAt)} • {messageCount} pesan
                            </Text>
                          </View>

                          {/* Right Controls: Delete & Active Indicator */}
                          <View style={styles.rightControls}>
                            {isActive && (
                              <Ionicons
                                name="checkmark-sharp"
                                size={17}
                                color={colors.textPrimary}
                                style={{ marginRight: 6 }}
                              />
                            )}

                            {sessions.length > 1 && (
                              <TouchableOpacity
                                onPress={() => handleDeleteSession(session.id)}
                                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                                style={styles.deleteBtn}
                              >
                                <Ionicons name="trash-outline" size={14} color={colors.textMuted} />
                              </TouchableOpacity>
                            )}
                          </View>
                        </TouchableOpacity>

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
              </ScrollView>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
    justifyContent: 'flex-start',
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    paddingHorizontal: 16,
  },
  sheetContainer: {
    borderRadius: 22,
    borderWidth: 1,
    maxHeight: '80%',
    paddingBottom: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.25,
        shadowRadius: 16,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  grabberWrapper: {
    alignItems: 'center',
    paddingTop: 10,
    paddingBottom: 4,
  },
  grabber: {
    width: 36,
    height: 4,
    borderRadius: 2,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    paddingVertical: 12,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  newChatBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    gap: 4,
  },
  newChatBtnText: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  sessionsList: {
    paddingHorizontal: 16,
  },
  sessionsContent: {
    paddingTop: 4,
    paddingBottom: 12,
  },
  groupedTable: {
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
  },
  sessionRow: {
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
  sessionCardContent: {
    flex: 1,
    marginRight: 8,
  },
  sessionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sessionTitle: {
    fontSize: 13.5,
    letterSpacing: -0.2,
  },
  metaText: {
    fontSize: 10.5,
    marginTop: 2,
  },
  rightControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  deleteBtn: {
    padding: 3,
  },
  tableDivider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 58,
  },
});
