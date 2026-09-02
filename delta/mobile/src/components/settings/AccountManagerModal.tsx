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
  Linking,
  ActivityIndicator,
} from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import { LiquidGlassCard } from '../common/LiquidGlassCard';
import { BlurBackdrop } from '../common/BlurBackdrop';
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
  const [baseUrl, setBaseUrl] = useState('https://api.antigravity.ai/v1');
  const [defaultModel, setDefaultModel] = useState('ag/gemini-3.7-flash-high');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);

  const [callbackUrl, setCallbackUrl] = useState('');
  const [isAuthorizing, setIsAuthorizing] = useState(false);

  useEffect(() => {
    if (editingAccount) {
      setName(editingAccount.name);
      setApiKey(editingAccount.apiKey);
      setBaseUrl(editingAccount.baseUrl || 'http://127.0.0.1:20128/v1');
      setDefaultModel(editingAccount.defaultModel || 'ag/gemini-3.7-flash-high');
    } else {
      setName('Antigravity 9Router (Google OAuth)');
      setApiKey('');
      setBaseUrl('http://127.0.0.1:20128/v1');
      setDefaultModel('ag/gemini-3.7-flash-high');
    }
    setCallbackUrl('');
    setIsAuthorizing(false);
    setShowKey(false);
  }, [editingAccount, visible]);

  const GOOGLE_AUTH_URL =
    'https://accounts.google.com/o/oauth2/v2/auth?client_id=1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A20128%2Fcallback&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcclog+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fexperimentsandconfigs&state=1ro-udT0wYGCFinjsQah_yZ5mrk8ZkMQ6OuHTLa9sGk&access_type=offline&prompt=consent';

  const handleOpenAntigravityOAuth = async () => {
    setIsAuthorizing(true);
    try {
      await Linking.openURL(GOOGLE_AUTH_URL);
    } catch (_) {
      Alert.alert('Browser Error', 'Salin link manual dan buka di browser.');
    }
  };

  const handleParseCallbackUrl = (url: string) => {
    setCallbackUrl(url);
    const trimmed = url.trim();
    if (!trimmed) return;

    try {
      if (trimmed.includes('code=')) {
        const codeMatch = trimmed.match(/code=([^&]+)/);
        if (codeMatch && codeMatch[1]) {
          const extractedCode = decodeURIComponent(codeMatch[1]);
          setApiKey(extractedCode);
          setIsAuthorizing(false);
          return;
        }
      }
      if (!trimmed.startsWith('http') && trimmed.length > 20) {
        setApiKey(trimmed);
        setIsAuthorizing(false);
      }
    } catch (_) {}
  };

  const handleSave = async () => {
    const trimmedName = name.trim() || 'Antigravity Cloud';
    const trimmedKey = apiKey.trim();
    const trimmedUrl = baseUrl.trim().replace(/\/+$/, '') || 'https://api.antigravity.ai/v1';

    if (!trimmedKey) {
      Alert.alert('Validation', 'Silakan masukkan Antigravity API Key / Token.');
      return;
    }

    setSaving(true);
    try {
      await onSave(
        {
          name: trimmedName,
          apiKey: trimmedKey,
          baseUrl: trimmedUrl,
          defaultModel: defaultModel.trim() || 'ag/gemini-3.7-flash-high',
          accountType: 'antigravity',
          tier: 'pro',
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
          <BlurBackdrop intensity={50} />
          <LiquidGlassCard style={styles.card}>
            {/* Modal Header */}
            <View style={styles.headerRow}>
              <View style={styles.titleWithIcon}>
                <Ionicons name="sparkles" size={18} color={colors.accent} />
                <Text style={[styles.modalTitle, { color: colors.textPrimary }]}>
                  {editingAccount ? 'Edit Akun Antigravity' : 'Connect Antigravity Cloud'}
                </Text>
              </View>
              <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
                <Feather name="x" size={20} color={colors.textMuted} />
              </TouchableOpacity>
            </View>

            {/* Antigravity OAuth Banner */}
            <View style={[styles.oauthBanner, { backgroundColor: colors.surfaceHover, borderColor: colors.border }]}>
              <View style={styles.oauthHeaderRow}>
                <Ionicons name="logo-google" size={16} color={colors.accent} />
                <Text style={[styles.oauthTitle, { color: colors.textPrimary }]}>
                  Google OAuth (9Router Antigravity)
                </Text>
              </View>

              {/* Step 1 */}
              <View style={styles.stepContainer}>
                <Text style={[styles.stepTitle, { color: colors.accent }]}>
                  Step 1: Open this URL in your browser
                </Text>
                <TouchableOpacity
                  style={[styles.oauthBtn, { backgroundColor: colors.textPrimary }]}
                  onPress={handleOpenAntigravityOAuth}
                  activeOpacity={0.8}
                >
                  <Ionicons name="open-outline" size={15} color={colors.bgPrimary} />
                  <Text style={[styles.oauthBtnText, { color: colors.bgPrimary }]}>
                    {isAuthorizing ? 'Waiting for popup authorization…' : 'Open Google Authorization'}
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Step 2 */}
              <View style={styles.stepContainer}>
                <Text style={[styles.stepTitle, { color: colors.accent }]}>
                  Step 2: Paste the callback URL here
                </Text>
                <Text style={[styles.stepDesc, { color: colors.textSecondary }]}>
                  After authorization, copy the full URL from your browser.
                </Text>
                <TextInput
                  style={[
                    styles.input,
                    {
                      backgroundColor: colors.bgSurface,
                      borderColor: colors.border,
                      color: colors.textPrimary,
                      marginTop: 4,
                    },
                  ]}
                  placeholder="http://localhost:20128/callback?code=..."
                  placeholderTextColor={colors.textMuted}
                  value={callbackUrl}
                  onChangeText={handleParseCallbackUrl}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              {isAuthorizing && (
                <View style={styles.authorizingStatusRow}>
                  <ActivityIndicator size="small" color={colors.accent} />
                  <Text style={[styles.authorizingStatusText, { color: colors.textSecondary }]}>
                    Waiting for popup authorization… or paste callback URL manually
                  </Text>
                </View>
              )}
            </View>

            {/* Label Akun */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>Label Akun</Text>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                    color: colors.textPrimary,
                  },
                ]}
                placeholder="Contoh: Antigravity Pro (Unlimited)"
                placeholderTextColor={colors.textMuted}
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
              />
            </View>

            {/* API Key / Token */}
            <View style={styles.fieldGroup}>
              <View style={styles.labelRow}>
                <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>
                  Antigravity Token / API Key
                </Text>
                <TouchableOpacity onPress={() => setShowKey(!showKey)}>
                  <Text style={[styles.toggleKeyText, { color: colors.accent }]}>
                    {showKey ? 'Sembunyikan' : 'Tampilkan'}
                  </Text>
                </TouchableOpacity>
              </View>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                    color: colors.textPrimary,
                  },
                ]}
                placeholder="Tempel token/key Antigravity..."
                placeholderTextColor={colors.textMuted}
                value={apiKey}
                onChangeText={setApiKey}
                secureTextEntry={!showKey}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Endpoint Base URL */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>Gateway Endpoint URL</Text>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                    color: colors.textPrimary,
                  },
                ]}
                placeholder="https://api.antigravity.ai/v1"
                placeholderTextColor={colors.textMuted}
                value={baseUrl}
                onChangeText={setBaseUrl}
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Target Model */}
            <View style={styles.fieldGroup}>
              <Text style={[styles.fieldLabel, { color: colors.textSecondary }]}>Default AI Model</Text>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
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
                style={[styles.cancelBtn, { borderColor: colors.border }]}
                onPress={onClose}
                activeOpacity={0.7}
              >
                <Text style={[styles.cancelBtnText, { color: colors.textMuted }]}>Batal</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.saveBtn, { backgroundColor: colors.textPrimary }]}
                onPress={handleSave}
                disabled={saving}
                activeOpacity={0.8}
              >
                {saving ? (
                  <ActivityIndicator size="small" color={colors.bgPrimary} />
                ) : (
                  <Text style={[styles.saveBtnText, { color: colors.bgPrimary }]}>
                    {editingAccount ? 'Perbarui Akun' : 'Hubungkan Antigravity'}
                  </Text>
                )}
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
    padding: 16,
  },
  card: {
    width: '100%',
    maxWidth: 440,
    padding: 18,
    borderRadius: 20,
  },
  headerRow: {
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
  modalTitle: {
    fontSize: 16,
    fontWeight: '800',
  },
  closeBtn: {
    padding: 4,
  },
  oauthBanner: {
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 12,
  },
  oauthHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  oauthTitle: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  oauthDesc: {
    fontSize: 11,
    lineHeight: 15,
    marginBottom: 10,
  },
  stepContainer: {
    marginTop: 8,
    marginBottom: 6,
  },
  stepTitle: {
    fontSize: 11.5,
    fontWeight: '700',
    marginBottom: 4,
  },
  stepDesc: {
    fontSize: 10.5,
    marginBottom: 4,
  },
  authorizingStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    padding: 6,
  },
  authorizingStatusText: {
    fontSize: 10.5,
    flex: 1,
  },
  oauthBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 36,
    borderRadius: 10,
    gap: 6,
  },
  oauthBtnText: {
    color: '#090A0C',
    fontSize: 12,
    fontWeight: '700',
  },
  fieldGroup: {
    marginBottom: 10,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: '700',
    marginBottom: 4,
  },
  toggleKeyText: {
    fontSize: 11,
    fontWeight: '600',
  },
  input: {
    height: 40,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    fontSize: 12.5,
  },
  btnRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  cancelBtn: {
    flex: 1,
    height: 42,
    borderRadius: 14,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelBtnText: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  saveBtn: {
    flex: 1.5,
    height: 42,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveBtnText: {
    color: '#090A0C',
    fontSize: 12.5,
    fontWeight: '800',
  },
});
