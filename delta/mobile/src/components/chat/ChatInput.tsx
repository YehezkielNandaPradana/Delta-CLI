import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  StyleSheet,
  Platform,
  KeyboardAvoidingView,
  Animated,
  Easing,
} from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { useSettingsStore } from '../../store/useSettingsStore';
import { ModelPickerSheet } from './ModelPickerSheet';

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isGenerating?: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onStop,
  isGenerating = false,
  disabled = false,
}) => {
  const { colors, isDark } = useThemeColors();
  const { activeModel, cloudModel, connectionMode } = useSettingsStore();

  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showModelPicker, setShowModelPicker] = useState(false);

  // Continuous animation values (Always active)
  const borderRotation = useRef(new Animated.Value(0)).current;
  const glowPulse = useRef(new Animated.Value(0.35)).current;
  const beamTranslate = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // 1. Smooth endless border gradient rotation
    const rotateLoop = Animated.loop(
      Animated.timing(borderRotation, {
        toValue: 1,
        duration: 3200,
        easing: Easing.linear,
        useNativeDriver: false,
      })
    );
    rotateLoop.start();

    // 2. Continuous breathing pulse glow
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(glowPulse, {
          toValue: 0.85,
          duration: 1600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: false,
        }),
        Animated.timing(glowPulse, {
          toValue: 0.35,
          duration: 1600,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: false,
        }),
      ])
    );
    pulseLoop.start();

    // 3. Continuous horizontal glowing beam
    const beamLoop = Animated.loop(
      Animated.timing(beamTranslate, {
        toValue: 1,
        duration: 2800,
        easing: Easing.inOut(Easing.sin),
        useNativeDriver: false,
      })
    );
    beamLoop.start();

    return () => {
      rotateLoop.stop();
      pulseLoop.stop();
      beamLoop.stop();
    };
  }, []);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    setText('');
  };

  const currentDisplayModel =
    connectionMode === 'telegram'
      ? 'Hermes Telegram'
      : connectionMode === 'cloud'
      ? cloudModel
      : activeModel;

  const cleanModelLabel = (model: string) => {
    if (!model) return 'AI Model';
    if (model === 'Hermes Telegram') return 'Hermes Bot';
    const name = model.includes('/') ? model.split('/')[1] : model;
    return name.length > 16 ? `${name.slice(0, 15)}…` : name;
  };

  // Dynamic monochrome border interpolations
  const edgeColorTop = borderRotation.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: isDark
      ? ['rgba(255, 255, 255, 0.45)', 'rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.45)']
      : ['rgba(0, 0, 0, 0.35)', 'rgba(0, 0, 0, 0.10)', 'rgba(0, 0, 0, 0.35)'],
  });

  const edgeColorBottom = borderRotation.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: isDark
      ? ['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.45)', 'rgba(255, 255, 255, 0.15)']
      : ['rgba(0, 0, 0, 0.10)', 'rgba(0, 0, 0, 0.35)', 'rgba(0, 0, 0, 0.10)'],
  });

  const auraTranslateX = beamTranslate.interpolate({
    inputRange: [0, 1],
    outputRange: [-100, 280],
  });

  return (
    <>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View
          style={[
            styles.container,
            {
              backgroundColor: colors.bgPrimary,
              borderTopColor: colors.border,
            },
          ]}
        >
          {/* ALWAYS ACTIVE DYNAMIC GLOWING CARD */}
          <View style={styles.borderAuraContainer}>
            {/* Outer Subtle Pulse Ring (Always Active) */}
            <Animated.View
              pointerEvents="none"
              style={[
                styles.outerGlowRing,
                {
                  opacity: glowPulse,
                  borderColor: isDark ? 'rgba(255, 255, 255, 0.25)' : 'rgba(0, 0, 0, 0.15)',
                  shadowColor: isDark ? '#FFFFFF' : '#000000',
                  shadowOpacity: 0.35,
                  shadowRadius: 10,
                  shadowOffset: { width: 0, height: 0 },
                },
              ]}
            />

            {/* Orbiting Subtle Edge Beams (Always Active) */}
            <Animated.View
              pointerEvents="none"
              style={[
                styles.neonEdgeTop,
                {
                  backgroundColor: isDark ? '#FFFFFF' : '#000000',
                  transform: [{ translateX: auraTranslateX }],
                  opacity: isDark ? 0.3 : 0.15,
                },
              ]}
            />

            {/* Main Input Card */}
            <Animated.View
              style={[
                styles.inputCard,
                {
                  backgroundColor: colors.bgSurface,
                  borderColor: isFocused ? colors.textPrimary : (isDark ? '#262626' : '#E5E5E5'),
                  borderTopColor: edgeColorTop,
                  borderBottomColor: edgeColorBottom,
                },
              ]}
            >
              {/* Text Input Area (Top) */}
              <TextInput
                style={[styles.input, { color: colors.textPrimary }]}
                placeholder="Tanyakan sesuatu pada Delta..."
                placeholderTextColor={colors.textMuted}
                value={text}
                onChangeText={setText}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                multiline
                maxLength={2500}
                editable={!disabled}
                returnKeyType="default"
              />

              {/* Bottom Accessory Bar */}
              <View style={styles.bottomAccessoryRow}>
                {/* Model Selector Chip */}
                <TouchableOpacity
                  style={[
                    styles.modelAccessoryBtn,
                    {
                      backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
                      borderColor: isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)',
                    },
                  ]}
                  onPress={() => setShowModelPicker(true)}
                  activeOpacity={0.7}
                  accessibilityLabel="Pilih Model AI"
                  accessibilityRole="button"
                >
                  <Ionicons
                    name="sparkles"
                    size={12}
                    color={colors.textPrimary}
                    style={{ marginRight: 4 }}
                  />
                  <Text
                    style={[styles.modelBtnText, { color: colors.textPrimary }]}
                    numberOfLines={1}
                  >
                    {cleanModelLabel(currentDisplayModel)}
                  </Text>
                  <Feather
                    name="chevron-down"
                    size={12}
                    color={colors.textSecondary}
                    style={{ marginLeft: 3 }}
                  />
                </TouchableOpacity>

                {/* Send / Stop Action Button */}
                {isGenerating ? (
                  <TouchableOpacity
                    style={[styles.actionBtn, { backgroundColor: colors.error }]}
                    onPress={onStop}
                    activeOpacity={0.7}
                    accessibilityLabel="Hentikan"
                    accessibilityRole="button"
                  >
                    <Feather name="square" size={12} color="#ffffff" />
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity
                    style={[
                      styles.actionBtn,
                      {
                        backgroundColor:
                          text.trim() && !disabled
                            ? colors.textPrimary
                            : (isDark ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)'),
                      },
                    ]}
                    onPress={handleSend}
                    disabled={!text.trim() || disabled}
                    activeOpacity={0.7}
                    accessibilityLabel="Kirim Pesan"
                    accessibilityRole="button"
                  >
                    <Feather
                      name="arrow-up"
                      size={16}
                      color={
                        text.trim() && !disabled
                          ? colors.bgPrimary
                          : colors.textMuted
                      }
                    />
                  </TouchableOpacity>
                )}
              </View>
            </Animated.View>
          </View>
        </View>
      </KeyboardAvoidingView>

      {/* Model Picker Sheet */}
      <ModelPickerSheet
        visible={showModelPicker}
        onClose={() => setShowModelPicker(false)}
      />
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 14,
    paddingTop: 8,
    paddingBottom: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  borderAuraContainer: {
    position: 'relative',
    borderRadius: 20,
  },
  outerGlowRing: {
    position: 'absolute',
    top: -1.5,
    left: -1.5,
    right: -1.5,
    bottom: -1.5,
    borderRadius: 21.5,
    borderWidth: 1.5,
    ...Platform.select({
      android: {
        elevation: 3,
      },
    }),
  },
  neonEdgeTop: {
    position: 'absolute',
    top: -1,
    height: 2,
    width: 100,
    borderRadius: 1,
    zIndex: 1,
  },
  inputCard: {
    position: 'relative',
    borderRadius: 20,
    borderWidth: 1.2,
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 8,
    overflow: 'hidden',
    zIndex: 2,
  },
  input: {
    fontSize: 14.5,
    lineHeight: 21,
    minHeight: 38,
    maxHeight: 120,
    paddingTop: 0,
    paddingBottom: 6,
  },
  bottomAccessoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 4,
    marginTop: 2,
  },
  modelAccessoryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5.5,
    borderRadius: 14,
    borderWidth: 1,
  },
  modelBtnText: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: -0.2,
  },
  actionBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
