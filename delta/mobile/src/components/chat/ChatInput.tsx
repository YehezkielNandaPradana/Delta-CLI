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
  const { activeModel } = useSettingsStore();

  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  // 1. Master Typing Glow Transition (0 = completely off, 1 = fully glowing)
  const typingGlowAnim = useRef(new Animated.Value(0)).current;

  // 2. Continuous Rotating Neon Beam along the outer border/perimeter
  const borderRotation = useRef(new Animated.Value(0)).current;

  // 3. Ambient pulsing glow (only visible when typingGlowAnim > 0)
  const glowPulse = useRef(new Animated.Value(0.4)).current;
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Continuous 360-degree border aura rotation
    const rotateLoop = Animated.loop(
      Animated.timing(borderRotation, {
        toValue: 1,
        duration: 2400,
        easing: Easing.linear,
        useNativeDriver: false,
      })
    );
    rotateLoop.start();

    // Ambient pulsing rhythm
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(glowPulse, {
          toValue: 1,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: false,
        }),
        Animated.timing(glowPulse, {
          toValue: 0.4,
          duration: 1200,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: false,
        }),
      ])
    );
    pulseLoop.start();

    return () => {
      rotateLoop.stop();
      pulseLoop.stop();
    };
  }, []);

  // Smoothly fade-in glow ONLY while actively typing
  useEffect(() => {
    if (isTyping) {
      Animated.timing(typingGlowAnim, {
        toValue: 1,
        duration: 250,
        useNativeDriver: false,
      }).start();
    } else {
      Animated.timing(typingGlowAnim, {
        toValue: 0,
        duration: 450,
        useNativeDriver: false,
      }).start();
    }
  }, [isTyping]);

  const handleChangeText = (val: string) => {
    setText(val);
    if (val.length > 0) {
      setIsTyping(true);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => {
        setIsTyping(false);
      }, 1500);
    } else {
      setIsTyping(false);
    }
  };

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    };
  }, []);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    setText('');
    setIsTyping(false);
  };

  const cleanModelLabel = (model: string) => {
    if (!model) return 'Model';
    const name = model.includes('/') ? model.split('/')[1] : model;
    return name.length > 14 ? `${name.slice(0, 13)}…` : name;
  };

  // Interpolate dynamic border colors along the edges
  const edgeColorTop = borderRotation.interpolate({
    inputRange: [0, 0.25, 0.5, 0.75, 1],
    outputRange: [
      colors.accentCyan,
      colors.accentGreen,
      colors.accentPurple,
      colors.accentCyan,
      colors.accentCyan,
    ],
  });

  const edgeColorRight = borderRotation.interpolate({
    inputRange: [0, 0.25, 0.5, 0.75, 1],
    outputRange: [
      colors.accentPurple,
      colors.accentCyan,
      colors.accentGreen,
      colors.accentPurple,
      colors.accentPurple,
    ],
  });

  const edgeColorBottom = borderRotation.interpolate({
    inputRange: [0, 0.25, 0.5, 0.75, 1],
    outputRange: [
      colors.accentGreen,
      colors.accentPurple,
      colors.accentCyan,
      colors.accentGreen,
      colors.accentGreen,
    ],
  });

  const edgeColorLeft = borderRotation.interpolate({
    inputRange: [0, 0.25, 0.5, 0.75, 1],
    outputRange: [
      colors.accentCyan,
      colors.accentGreen,
      colors.accentPurple,
      colors.accentCyan,
      colors.accentCyan,
    ],
  });

  // Dynamic moving glow aura position (-140 to +360)
  const auraTranslateX = borderRotation.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [-140, 360, -140],
  });

  // Total glow intensity (0 when idle, pulsing when typing)
  const outerGlowOpacity = Animated.multiply(
    typingGlowAnim,
    glowPulse.interpolate({
      inputRange: [0.4, 1],
      outputRange: [0.55, 0.95],
    })
  );

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
              borderTopColor: colors.cardBorder,
            },
          ]}
        >
          {/* Top Row Toolbar */}
          <View style={styles.topToolbar}>
            <TouchableOpacity
              style={[
                styles.modelChip,
                {
                  backgroundColor: colors.cardBg,
                  borderColor: colors.cardBorder,
                },
              ]}
              onPress={() => setShowModelPicker(true)}
              activeOpacity={0.7}
              accessibilityLabel="Change AI Model"
              accessibilityRole="button"
            >
              <View
                style={[
                  styles.sparkleCircle,
                  { backgroundColor: colors.accentGreenSubtle },
                ]}
              >
                <Ionicons name="sparkles" size={10} color={colors.accentGreen} />
              </View>
              <Text
                style={[styles.modelChipText, { color: colors.textSecondary }]}
                numberOfLines={1}
              >
                {cleanModelLabel(activeModel)}
              </Text>
              <Feather name="chevron-down" size={12} color={colors.textMuted} />
            </TouchableOpacity>

            <View style={styles.toolbarRight}>
              {isTyping && (
                <View style={styles.typingIndicatorRow}>
                  <View
                    style={[
                      styles.typingDot,
                      { backgroundColor: colors.accentCyan },
                    ]}
                  />
                  <Text style={[styles.typingText, { color: colors.accentCyan }]}>
                    Active prompt
                  </Text>
                </View>
              )}
            </View>
          </View>

          {/* DYNAMIC NEON GLOWING PERIMETER BOX */}
          <View style={styles.borderAuraContainer}>
            {/* 1. Outer Diffused Glow Ring (Active ONLY when typing) */}
            <Animated.View
              pointerEvents="none"
              style={[
                styles.outerGlowRing,
                {
                  opacity: outerGlowOpacity,
                  borderColor: edgeColorTop,
                  shadowColor: isDark ? colors.accentCyan : colors.accentGreen,
                  shadowOpacity: 0.95,
                  shadowRadius: 16,
                  shadowOffset: { width: 0, height: 0 },
                },
              ]}
            />

            {/* 2. Orbiting Neon Edge Beams (Active ONLY when typing) */}
            <Animated.View
              pointerEvents="none"
              style={[
                styles.neonEdgeTop,
                {
                  backgroundColor: edgeColorTop,
                  transform: [{ translateX: auraTranslateX }],
                  opacity: typingGlowAnim,
                },
              ]}
            />
            <Animated.View
              pointerEvents="none"
              style={[
                styles.neonEdgeBottom,
                {
                  backgroundColor: edgeColorBottom,
                  transform: [{ translateX: auraTranslateX }],
                  opacity: typingGlowAnim,
                },
              ]}
            />

            {/* 3. Main Input Capsule Frame */}
            <Animated.View
              style={[
                styles.inputCapsule,
                {
                  backgroundColor: colors.cardBg,
                  borderColor: isTyping ? edgeColorTop : (isFocused ? colors.accentGreen : colors.cardBorder),
                  borderTopColor: isTyping ? edgeColorTop : (isFocused ? colors.accentGreen : colors.cardSpecular),
                  borderRightColor: isTyping ? edgeColorRight : (isFocused ? colors.accentGreen : colors.cardBorder),
                  borderBottomColor: isTyping ? edgeColorBottom : (isFocused ? colors.accentGreen : colors.cardBorder),
                  borderLeftColor: isTyping ? edgeColorLeft : (isFocused ? colors.accentGreen : colors.cardBorder),
                },
              ]}
            >
              <TextInput
                style={[styles.input, { color: colors.textPrimary }]}
                placeholder="Ask Delta anything..."
                placeholderTextColor={colors.textMuted}
                value={text}
                onChangeText={handleChangeText}
                onFocus={() => setIsFocused(true)}
                onBlur={() => {
                  setIsFocused(false);
                  setIsTyping(false);
                }}
                multiline
                maxLength={2500}
                editable={!disabled}
                returnKeyType="default"
              />

              {isGenerating ? (
                <TouchableOpacity
                  style={[styles.actionBtn, { backgroundColor: colors.accentRed }]}
                  onPress={onStop}
                  activeOpacity={0.7}
                  accessibilityLabel="Stop Generation"
                  accessibilityRole="button"
                >
                  <Feather name="square" size={13} color="#ffffff" />
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={[
                    styles.actionBtn,
                    {
                      backgroundColor:
                        text.trim() && !disabled
                          ? colors.accentGreen
                          : colors.bgSecondary,
                    },
                  ]}
                  onPress={handleSend}
                  disabled={!text.trim() || disabled}
                  activeOpacity={0.7}
                  accessibilityLabel="Send Message"
                  accessibilityRole="button"
                >
                  <Feather
                    name="arrow-up"
                    size={16}
                    color={
                      text.trim() && !disabled
                        ? isDark
                          ? '#000000'
                          : '#ffffff'
                        : colors.textMuted
                    }
                  />
                </TouchableOpacity>
              )}
            </Animated.View>
          </View>
        </View>
      </KeyboardAvoidingView>

      {/* Interactive Liquid Glass Model Picker Modal */}
      <ModelPickerSheet
        visible={showModelPicker}
        onClose={() => setShowModelPicker(false)}
      />
    </>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: 14,
    borderTopWidth: 1,
  },
  topToolbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
    paddingHorizontal: 2,
  },
  modelChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 14,
    borderWidth: 1,
  },
  sparkleCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modelChipText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  toolbarRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingIndicatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  typingDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
  },
  typingText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.3,
    fontFamily: 'monospace',
    textTransform: 'uppercase',
  },
  borderAuraContainer: {
    position: 'relative',
    borderRadius: 22,
  },
  outerGlowRing: {
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    borderRadius: 24,
    borderWidth: 2,
    ...Platform.select({
      android: {
        elevation: 6,
      },
    }),
  },
  neonEdgeTop: {
    position: 'absolute',
    top: -1,
    height: 2.5,
    width: 120,
    borderRadius: 2,
    zIndex: 1,
  },
  neonEdgeBottom: {
    position: 'absolute',
    bottom: -1,
    height: 2.5,
    width: 120,
    borderRadius: 2,
    zIndex: 1,
  },
  inputCapsule: {
    position: 'relative',
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderRadius: 22,
    borderWidth: 1.8,
    paddingLeft: 14,
    paddingRight: 6,
    paddingVertical: 5,
    minHeight: 46,
    overflow: 'hidden',
    zIndex: 2,
  },
  input: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    maxHeight: 120,
    paddingTop: 6,
    paddingBottom: 6,
    marginRight: 6,
  },
  actionBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 1,
  },
});
