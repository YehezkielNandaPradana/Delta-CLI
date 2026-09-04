import React from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  TouchableWithoutFeedback,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { BlurBackdrop } from '../common/BlurBackdrop';
import { ChatMessage } from '../../types/chat';

interface MessageActionSheetProps {
  visible: boolean;
  message: ChatMessage | null;
  onClose: () => void;
  onCopy: (text: string) => void;
  onSaveNote: (text: string, isUser: boolean) => void;
  onQuote: (text: string) => void;
  onForwardTelegram?: (text: string) => void;
  onDelete: (id: string) => void;
}

export const MessageActionSheet: React.FC<MessageActionSheetProps> = ({
  visible,
  message,
  onClose,
  onCopy,
  onSaveNote,
  onQuote,
  onForwardTelegram,
  onDelete,
}) => {
  const { colors, isDark } = useThemeColors();

  if (!message) return null;

  const isUser = message.sender === 'user';
  const cleanSnippet = message.text ? message.text.slice(0, 75).replace(/\n/g, ' ') : '';

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.overlay}>
          <BlurBackdrop intensity={50} />
          <TouchableWithoutFeedback>
            <View style={styles.menuContainer}>
              {/* Message Snippet Card Header */}
              <View
                style={[
                  styles.previewCard,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
              >
                <View style={styles.previewHeader}>
                  <Ionicons
                    name={isUser ? 'person-circle-outline' : 'shield-checkmark-outline'}
                    size={14}
                    color={colors.accent}
                  />
                  <Text style={[styles.previewSender, { color: colors.textSecondary }]}>
                    {isUser ? 'Pesan Anda' : 'Delta AI'}
                  </Text>
                </View>
                <Text
                  style={[styles.previewText, { color: colors.textPrimary }]}
                  numberOfLines={2}
                >
                  {cleanSnippet || 'Pesan kosong'}
                </Text>
              </View>

              {/* iOS Style Action Menu Items */}
              <View
                style={[
                  styles.actionGroup,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
              >
                {/* 1. Copy */}
                <TouchableOpacity
                  onPress={() => {
                    onCopy(message.text);
                    onClose();
                  }}
                  style={styles.actionItem}
                  activeOpacity={0.6}
                >
                  <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>
                    Salin Teks
                  </Text>
                  <Ionicons name="copy-outline" size={17} color={colors.textPrimary} />
                </TouchableOpacity>

                <View style={[styles.separator, { backgroundColor: colors.border }]} />

                {/* 2. Save Note */}
                <TouchableOpacity
                  onPress={() => {
                    onSaveNote(message.text, isUser);
                    onClose();
                  }}
                  style={styles.actionItem}
                  activeOpacity={0.6}
                >
                  <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>
                    Simpan ke Delta Note
                  </Text>
                  <Ionicons name="bookmark-outline" size={17} color={colors.accent} />
                </TouchableOpacity>

                <View style={[styles.separator, { backgroundColor: colors.border }]} />

                {/* 3. Quote / Forward */}
                <TouchableOpacity
                  onPress={() => {
                    onQuote(message.text);
                    onClose();
                  }}
                  style={styles.actionItem}
                  activeOpacity={0.6}
                >
                  <Text style={[styles.actionLabel, { color: colors.textPrimary }]}>
                    Kutip Pesan
                  </Text>
                  <Ionicons name="chatbubble-ellipses-outline" size={17} color={colors.textPrimary} />
                </TouchableOpacity>

                <View style={[styles.separator, { backgroundColor: colors.border }]} />

                {/* 3.5 Forward to Telegram */}
                {onForwardTelegram && (
                  <>
                    <TouchableOpacity
                      onPress={() => {
                        onForwardTelegram(message.text);
                        onClose();
                      }}
                      style={styles.actionItem}
                      activeOpacity={0.6}
                    >
                      <Text style={[styles.actionLabel, { color: '#0088cc' }]}>
                        Forward ke Hermes Bot
                      </Text>
                      <Ionicons name="paper-plane-outline" size={17} color="#0088cc" />
                    </TouchableOpacity>

                    <View style={[styles.separator, { backgroundColor: colors.border }]} />
                  </>
                )}

                {/* 4. Delete */}
                <TouchableOpacity
                  onPress={() => {
                    onDelete(message.id);
                    onClose();
                  }}
                  style={styles.actionItem}
                  activeOpacity={0.6}
                >
                  <Text style={[styles.actionLabel, { color: colors.error }]}>
                    Hapus Pesan
                  </Text>
                  <Ionicons name="trash-outline" size={17} color={colors.error} />
                </TouchableOpacity>
              </View>
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
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  menuContainer: {
    width: '100%',
    maxWidth: 320,
    gap: 10,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.3,
        shadowRadius: 20,
      },
      android: {
        elevation: 10,
      },
    }),
  },
  previewCard: {
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  previewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginBottom: 4,
  },
  previewSender: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  previewText: {
    fontSize: 13,
    lineHeight: 18,
  },
  actionGroup: {
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 13,
  },
  actionLabel: {
    fontSize: 14.5,
    fontWeight: '500',
    letterSpacing: -0.2,
  },
  separator: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 16,
  },
});