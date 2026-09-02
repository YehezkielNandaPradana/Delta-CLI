import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import { LiquidGlassCard } from '../common/LiquidGlassCard';
import { AntigravityAccount } from '../../types/cloud';
import { useThemeColors } from '../../theme/theme';

interface AccountManagerModalProps {
  visible: boolean;
  onClose: () => void;
  onSave: (account: Omit<AntigravityAccount, 'id'>, editId?: string) => Promise<void>;
  editingAccount?: AntigravityAccount | null;
}

export function AccountManagerModal({
  visible,
  onClose,
  onSave,
  editingAccount,
}: AccountManagerModalProps) {
  const { colors, isDark } = useThemeColors();
  const [name, setName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [defaultModel, setDefaultModel] = useState('gemini-1.5-flash');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (editingAccount) {
      setName(editingAccount.name);
      setApiKey(editingAccount.apiKey);
      setBaseUrl(editingAccount.baseUrl || '');
      setDefaultModel(editingAccount.defaultModel || 'gemini-2.0-flash');
    } else {
      setName('');
      setApiKey('');
      setBaseUrl('');
      setDefaultModel('gemini-2.0-flash');
    }
    setShowKey(false);
  }, [editingAccount, visible]);

  const handleSave = async () => {
    const trimmedName = name.trim();
    const trimmedKey = apiKey.trim();
    const trimmedUrl = baseUrl.trim().replace(/\/+$/, '');

    if (!trimmedName) {
      Alert.alert('Validation', 'Silakan masukkan nama akun.');
      return;
    }
    if (!trimmedKey) {
      Alert.alert('Validation', 'Silakan masukkan API Key.');
      return;
    }

    setSaving(true);
    try {
      await onSave(
        {
          name: trimmedName,
          apiKey: trimmedKey,
          baseUrl: trimmedUrl, // Boleh string kosong untuk direct Google Gemini API
          defaultModel: defaultModel.trim() || 'gemini-2.0-flash',
        },
        editingAccount?.id
      );
      onClose();
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Gagal menyimpan akun.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        style={styles.modalOverlay}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.modalBackdrop}>
          <LiquidGlassCard style={styles.card}>
            <View style={styles.headerRow}>
              <View style={styles.titleWithIcon}>
                <Ionicons name="key-outline" size={20} color={colors.accentGreen} />
                <Text style={[styles.modalTitle, { color: colors.textPrimary }]}>
                  {editingAccount ? 'Edit Akun Antigravity' : 'Tambah Akun Antigravity'}
                </Text>
              </View>
              <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                <Feather name="x" size={20} color={colors.textMuted} />
              </TouchableOpacity>
            </View>

            {/* Nama Akun */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>Nama Akun / Label</Text>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.codeBg,
                    borderColor: colors.codeBorder,
                    color: colors.textPrimary,
                  },
                ]}
                placeholder="Contoh: Akun Utama / Cloud Pro"
                placeholderTextColor={colors.textMuted}
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
              />
            </View>

            {/* API Key */}
            <View style={styles.fieldGroup}>
              <View style={styles.labelRow}>
                <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>Antigravity API Key</Text>
                <TouchableOpacity onPress={() => setShowKey(!showKey)}>
                  <Text style={[styles.toggleKeyText, { color: colors.accentCyan }]}>
                    {showKey ? 'Sembunyikan' : 'Tampilkan'}
                  </Text>
                </TouchableOpacity>
              </View>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.codeBg,
                    borderColor: colors.codeBorder,
                    color: colors.textPrimary,
                  },
                ]}
                placeholder="Masukkan API Key Antigravity..."
                placeholderTextColor={colors.textMuted}
                value={apiKey}
                onChangeText={setApiKey}
                secureTextEntry={!showKey}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Base URL */}
            <View style={styles.fieldGroup}>
              <View style={styles.labelRow}>
                <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>Endpoint Base URL</Text>
                <Text style={[styles.toggleKeyText, { color: colors.textMuted }]}>
                  Opsional (Kosong = Google AI)
                </Text>
              </View>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.codeBg,
                    borderColor: colors.codeBorder,
                    color: colors.textPrimary,
                  },
                ]}
                placeholder="Kosongkan jika menggunakan Gemini AI Studio"
                placeholderTextColor={colors.textMuted}
                value={baseUrl}
                onChangeText={setBaseUrl}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Default Model */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>Model Target</Text>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.codeBg,
                    borderColor: colors.codeBorder,
                    color: colors.textPrimary,
                  },
                ]}
                placeholder="ag/gemini-3.7-flash-high"
                placeholderTextColor={colors.textMuted}
                value={defaultModel}
                onChangeText={setDefaultModel}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Action Buttons */}
            <View style={styles.btnRow}>
              <TouchableOpacity
                style={[styles.cancelBtn, { borderColor: colors.cardBorder }]}
                onPress={onClose}
                activeOpacity={0.7}
              >
                <Text style={[styles.cancelBtnText, { color: colors.textMuted }]}>Batal</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.saveBtn, { backgroundColor: colors.accentGreen }]}
                onPress={handleSave}
                disabled={saving}
                activeOpacity={0.8}
              >
                <Text style={[styles.saveBtnText, { color: isDark ? '#000000' : '#ffffff' }]}>
                  {saving ? 'Menyimpan...' : 'Simpan Akun'}
                </Text>
              </TouchableOpacity>
            </View>
          </LiquidGlassCard>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    width: '100%',
    maxWidth: 420,
    padding: 20,
    borderRadius: 20,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  titleWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '700',
  },
  closeBtn: {
    padding: 4,
  },
  fieldGroup: {
    marginBottom: 14,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  fieldLabel: {
    fontSize: 11.5,
    fontWeight: '700',
    marginBottom: 6,
  },
  toggleKeyText: {
    fontSize: 11,
    fontWeight: '600',
  },
  input: {
    height: 42,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    fontSize: 13,
  },
  btnRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  cancelBtn: {
    flex: 1,
    height: 44,
    borderRadius: 12,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelBtnText: {
    fontSize: 13,
    fontWeight: '700',
  },
  saveBtn: {
    flex: 1.5,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveBtnText: {
    fontSize: 13,
    fontWeight: '800',
  },
});
