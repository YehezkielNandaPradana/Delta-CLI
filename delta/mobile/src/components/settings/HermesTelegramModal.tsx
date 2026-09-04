import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Switch,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { useSettingsStore } from '../../store/useSettingsStore';
import { hermesTelegramService } from '../../services/telegram/hermesTelegramService';

interface HermesTelegramModalProps {
  visible: boolean;
  onClose: () => void;
}

export const HermesTelegramModal: React.FC<HermesTelegramModalProps> = ({ visible, onClose }) => {
  const { colors, isDark } = useThemeColors();
  const {
    telegramBotToken,
    telegramChatId,
    telegramAutoForward,
    hapticEnabled,
    setTelegramBotToken,
    setTelegramChatId,
    setTelegramAutoForward,
  } = useSettingsStore();

  const [tokenInput, setTokenInput] = useState(telegramBotToken);
  const [chatIdInput, setChatIdInput] = useState(telegramChatId);
  const [autoForward, setAutoForward] = useState(telegramAutoForward);
  const [isTesting, setIsTesting] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);
  const [isDetectingId, setIsDetectingId] = useState(false);
  const [botName, setBotName] = useState<string | null>(null);

  React.useEffect(() => {
    setTokenInput(telegramBotToken);
    setChatIdInput(telegramChatId);
    setAutoForward(telegramAutoForward);
    setBotName(null);
  }, [visible, telegramBotToken, telegramChatId, telegramAutoForward]);

  const handleTestToken = async () => {
    if (!tokenInput.trim()) {
      Alert.alert('Perhatian', 'Silakan masukkan Telegram Bot Token terlebih dahulu.');
      return;
    }

    setIsTesting(true);
    if (hapticEnabled) Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      const res = await hermesTelegramService.testBot(tokenInput.trim());
      if (res.success && res.bot) {
        setBotName(`@${res.bot.username || res.bot.first_name}`);
        Alert.alert(
          'Bot Terhubung! 🤖',
          `Nama Bot: ${res.bot.first_name}\nUsername: @${res.bot.username || '-'}\nID: ${res.bot.id}`
        );
      } else {
        Alert.alert('Gagal Terhubung', res.error || 'Token bot tidak valid atau bot tidak ditemukan.');
      }
    } finally {
      setIsTesting(false);
    }
  };

  const handleDetectChatId = async () => {
    if (!tokenInput.trim()) {
      Alert.alert('Perhatian', 'Isi Bot Token terlebih dahulu.');
      return;
    }
    setIsDetectingId(true);
    if (hapticEnabled) Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      const res = await hermesTelegramService.detectChatId(tokenInput.trim());
      if (res.success && res.chatId) {
        setChatIdInput(res.chatId);
        if (hapticEnabled) Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
        Alert.alert('Chat ID Ditemukan!', `Chat ID: ${res.chatId}\nUser: @${res.fromUser}\nOtomatis diisikan ke form.`);
      } else {
        Alert.alert('Peringatan', res.error || 'Gagal mendeteksi Chat ID.');
      }
    } finally {
      setIsDetectingId(false);
    }
  };

  const handleSendTestMessage = async () => {
    if (!tokenInput.trim() || !chatIdInput.trim()) {
      Alert.alert('Perhatian', 'Mohon isi Telegram Bot Token dan Chat ID.');
      return;
    }

    setIsSendingTest(true);
    if (hapticEnabled) Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      const testMsg = `🚀 *Delta Mobile terhubung ke Hermes Bot!*\n\nTes koneksi dari aplikasi Delta Mobile berhasil. Status: Aktif.`;
      const res = await hermesTelegramService.sendMessage(testMsg, {
        token: tokenInput.trim(),
        chatId: chatIdInput.trim(),
        parseMode: 'Markdown',
      });

      if (res.success) {
        Alert.alert('Terkirim!', 'Pesan uji coba berhasil dikirim ke Telegram Chat ID Anda.');
      } else {
        Alert.alert('Gagal Kirim Pesan', res.error || 'Gagal mengirim pesan.');
      }
    } finally {
      setIsSendingTest(false);
    }
  };

  const handleSave = async () => {
    await setTelegramBotToken(tokenInput.trim());
    await setTelegramChatId(chatIdInput.trim());
    await setTelegramAutoForward(autoForward);

    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }

    Alert.alert('Tersimpan', 'Pengaturan Hermes Bot Telegram berhasil disimpan.');
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={[styles.container, { backgroundColor: colors.bgPrimary }]}
      >
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: colors.border }]}>
          <View style={styles.headerLeft}>
            <View style={[styles.iconBox, { backgroundColor: isDark ? 'rgba(0, 136, 204, 0.15)' : 'rgba(0, 136, 204, 0.1)' }]}>
              <Ionicons name="paper-plane" size={20} color="#0088cc" />
            </View>
            <View>
              <Text style={[styles.headerTitle, { color: colors.textPrimary }]}>Hermes Telegram Bot</Text>
              <Text style={[styles.headerSubtitle, { color: colors.textMuted }]}>
                Integrasi Telegram Bot API Langsung
              </Text>
            </View>
          </View>
          <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: colors.bgSurface }]}>
            <Ionicons name="close" size={20} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {/* Status Box */}
          <View
            style={[
              styles.infoCard,
              {
                backgroundColor: isDark ? 'rgba(0, 136, 204, 0.08)' : 'rgba(0, 136, 204, 0.05)',
                borderColor: isDark ? 'rgba(0, 136, 204, 0.2)' : 'rgba(0, 136, 204, 0.15)',
              },
            ]}
          >
            <Ionicons name="information-circle-outline" size={20} color="#0088cc" style={styles.infoIcon} />
            <Text style={[styles.infoText, { color: colors.textSecondary }]}>
              Hubungkan Hermes Bot Telegram Anda untuk menerima temuan audit, catatan keamanan, atau chat dua arah
              langsung dari Delta Mobile.
            </Text>
          </View>

          {/* Bot Token Input */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>TELEGRAM BOT TOKEN</Text>
            <View style={[styles.inputContainer, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
              <Ionicons name="key-outline" size={18} color={colors.textMuted} style={styles.inputIcon} />
              <TextInput
                value={tokenInput}
                onChangeText={setTokenInput}
                placeholder="Contoh: 123456789:ABCdefGhIJKlmNoPQRstuVWXyz"
                placeholderTextColor={colors.textMuted}
                style={[styles.input, { color: colors.textPrimary }]}
                autoCapitalize="none"
                autoCorrect={false}
                secureTextEntry
              />
              <TouchableOpacity
                onPress={handleTestToken}
                disabled={isTesting}
                style={[styles.inlineBtn, { backgroundColor: colors.surfaceElevated, borderColor: colors.border }]}
              >
                {isTesting ? (
                  <ActivityIndicator size="small" color="#0088cc" />
                ) : (
                  <Text style={[styles.inlineBtnText, { color: '#0088cc' }]}>Cek Bot</Text>
                )}
              </TouchableOpacity>
            </View>
            {botName && (
              <Text style={[styles.botBadge, { color: '#0088cc' }]}>
                ✓ Terverifikasi: {botName}
              </Text>
            )}
            <Text style={[styles.fieldHint, { color: colors.textMuted }]}>
              Dapatkan token ini dari @BotFather di Telegram saat Anda membuat bot.
            </Text>
          </View>

          {/* Chat ID Input */}
          <View style={styles.fieldGroup}>
            <View style={styles.chatIdLabelRow}>
              <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>CHAT ID TELEGRAM</Text>
              <TouchableOpacity onPress={handleDetectChatId} disabled={isDetectingId}>
                <Text style={[styles.detectBtnText, { color: '#0088cc' }]}>
                  {isDetectingId ? 'Mendeteksi...' : '🔍 Deteksi Otomatis'}
                </Text>
              </TouchableOpacity>
            </View>
            <View style={[styles.inputContainer, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
              <Ionicons name="chatbubble-outline" size={18} color={colors.textMuted} style={styles.inputIcon} />
              <TextInput
                value={chatIdInput}
                onChangeText={setChatIdInput}
                placeholder="Contoh: 123456789 atau -100xxxxxxxxxx"
                placeholderTextColor={colors.textMuted}
                style={[styles.input, { color: colors.textPrimary }]}
                keyboardType="numeric"
                autoCapitalize="none"
                autoCorrect={false}
              />
              <TouchableOpacity
                onPress={handleSendTestMessage}
                disabled={isSendingTest}
                style={[styles.inlineBtn, { backgroundColor: colors.surfaceElevated, borderColor: colors.border }]}
              >
                {isSendingTest ? (
                  <ActivityIndicator size="small" color="#0088cc" />
                ) : (
                  <Text style={[styles.inlineBtnText, { color: '#0088cc' }]}>Kirim Tes</Text>
                )}
              </TouchableOpacity>
            </View>
            <Text style={[styles.fieldHint, { color: colors.textMuted }]}>
              Buka bot Anda di Telegram dan ketik /start. Lalu klik "Deteksi Otomatis" di atas agar Chat ID terisi otomatis.
            </Text>
          </View>

          {/* Toggle Auto Forward */}
          <View style={[styles.switchRow, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
            <View style={styles.switchInfo}>
              <Text style={[styles.switchTitle, { color: colors.textPrimary }]}>Auto-Forward Output AI</Text>
              <Text style={[styles.switchDesc, { color: colors.textMuted }]}>
                Otomatis kirimkan respons analisis Delta AI ke Hermes Telegram Bot setelah selesai diproses.
              </Text>
            </View>
            <Switch
              value={autoForward}
              onValueChange={setAutoForward}
              trackColor={{ false: colors.border, true: '#0088cc' }}
              thumbColor={Platform.OS === 'android' ? '#ffffff' : undefined}
            />
          </View>
        </ScrollView>

        {/* Footer Actions */}
        <View style={[styles.footer, { borderTopColor: colors.border, backgroundColor: colors.bgSurface }]}>
          <TouchableOpacity
            onPress={handleSave}
            style={[styles.saveButton, { backgroundColor: '#0088cc' }]}
            activeOpacity={0.8}
          >
            <Ionicons name="checkmark-circle-outline" size={20} color="#ffffff" />
            <Text style={styles.saveButtonText}>Simpan Konfigurasi Hermes</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    padding: 20,
    gap: 20,
  },
  infoCard: {
    flexDirection: 'row',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
    alignItems: 'flex-start',
  },
  infoIcon: {
    marginTop: 2,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  fieldGroup: {
    gap: 8,
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.6,
  },
  chatIdLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  detectBtnText: {
    fontSize: 11,
    fontWeight: '700',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    height: 48,
  },
  inputIcon: {
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 13.5,
    paddingVertical: 8,
  },
  inlineBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    marginLeft: 8,
  },
  inlineBtnText: {
    fontSize: 12,
    fontWeight: '600',
  },
  botBadge: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 2,
  },
  fieldHint: {
    fontSize: 11.5,
    lineHeight: 16,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 14,
    borderWidth: 1,
    gap: 16,
  },
  switchInfo: {
    flex: 1,
  },
  switchTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  switchDesc: {
    fontSize: 12,
    lineHeight: 16,
  },
  footer: {
    padding: 20,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    gap: 8,
  },
  saveButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },
});
