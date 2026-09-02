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
    createSession();
    onClose();
  };

  const handleSelectSession = (sessionId: string) => {
    switchSession(sessionId);
    onClose();
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
                    Riwayat percakapan Delta
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

              {/* Sessions List */}
              <ScrollView
                style={styles.sessionsList}
                contentContainerStyle={styles.sessionsContent}
                showsVerticalScrollIndicator={false}
              >
                {sessions.map((session) => {
                  const isActive = session.id === currentSessionId;
                  const messageCount = session.messages?.length || 0;

                  return (
                    <TouchableOpacity
                      key={session.id}
                      onPress={() => handleSelectSession(session.id)}
                      style={[
                        styles.sessionCard,
                        {
                          backgroundColor: isActive
                            ? (isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)')
                            : colors.bgSurface,
                          borderColor: isActive ? colors.accent : colors.border,
                          borderLeftWidth: isActive ? 3 : 1,
                          borderLeftColor: isActive ? colors.accent : colors.border,
                        },
                      ]}
                      activeOpacity={0.7}
                    >
                      <View style={styles.sessionCardContent}>
                        <View style={styles.sessionTitleRow}>
                          <Ionicons
                            name={isActive ? 'chatbubble-ellipses' : 'chatbubble-outline'}
                            size={14}
                            color={isActive ? colors.accent : colors.textSecondary}
                            style={{ marginRight: 6, marginTop: 2 }}
                          />
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

                        <View style={styles.sessionMetaRow}>
                          <Text style={[styles.metaText, { color: colors.textMuted }]}>
                            {formatTimestamp(session.updatedAt)} • {messageCount} pesan
                          </Text>
                        </View>
                      </View>

                      {sessions.length > 1 && (
                        <TouchableOpacity
                          onPress={() => deleteSession(session.id)}
                          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                          style={styles.deleteBtn}
                        >
                          <Ionicons name="trash-outline" size={14} color={colors.textMuted} />
                        </TouchableOpacity>
                      )}
                    </TouchableOpacity>
                  );
                })}
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
    color: '#090A0C',
    fontSize: 12.5,
    fontWeight: '700',
  },
  sessionsList: {
    paddingHorizontal: 14,
  },
  sessionsContent: {
    paddingTop: 4,
    paddingBottom: 12,
    gap: 8,
  },
  sessionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  sessionCardContent: {
    flex: 1,
    marginRight: 8,
  },
  sessionTitleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  sessionTitle: {
    fontSize: 14,
    flex: 1,
  },
  sessionMetaRow: {
    marginTop: 4,
    marginLeft: 20,
  },
  metaText: {
    fontSize: 11,
  },
  deleteBtn: {
    padding: 4,
  },
});