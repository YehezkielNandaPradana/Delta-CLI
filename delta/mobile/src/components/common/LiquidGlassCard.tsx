import React, { useRef } from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  Animated,
  Pressable,
  Platform,
} from 'react-native';
import { useThemeColors } from '../../theme/theme';

interface LiquidGlassCardProps {
  children: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
  specular?: boolean;
  onPress?: () => void;
  variant?: 'surface' | 'glass' | 'subtle';
  active?: boolean;
}

export const LiquidGlassCard: React.FC<LiquidGlassCardProps> = ({
  children,
  style,
  specular = true,
  onPress,
  variant = 'surface',
  active = false,
}) => {
  const { colors, isDark } = useThemeColors();
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    if (!onPress) return;
    Animated.spring(scaleAnim, {
      toValue: 0.975,
      useNativeDriver: true,
      damping: 18,
      stiffness: 250,
    }).start();
  };

  const handlePressOut = () => {
    if (!onPress) return;
    Animated.spring(scaleAnim, {
      toValue: 1,
      useNativeDriver: true,
      damping: 15,
      stiffness: 200,
    }).start();
  };

  const getBackgroundColor = () => {
    if (variant === 'subtle') return colors.bgSecondary;
    return colors.cardBg;
  };

  const getBorderColor = () => {
    if (active) return colors.accentGreen;
    return colors.cardBorder;
  };

  const cardContent = (
    <View
      style={[
        styles.card,
        {
          backgroundColor: getBackgroundColor(),
          borderColor: getBorderColor(),
          shadowColor: isDark ? '#000' : '#64748b',
        },
        specular && {
          borderTopColor: colors.cardSpecular,
          borderTopWidth: 1.5,
        },
        style,
      ]}
    >
      {/* Specular sheen gradient simulation */}
      {specular && (
        <View
          style={[
            styles.specularSheen,
            {
              backgroundColor: isDark
                ? 'rgba(255, 255, 255, 0.04)'
                : 'rgba(255, 255, 255, 0.6)',
            },
          ]}
          pointerEvents="none"
        />
      )}
      {children}
    </View>
  );

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        style={styles.pressable}
      >
        <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
          {cardContent}
        </Animated.View>
      </Pressable>
    );
  }

  return cardContent;
};

const styles = StyleSheet.create({
  pressable: {
    width: '100%',
  },
  card: {
    borderRadius: 20,
    borderWidth: 1,
    overflow: 'hidden',
    position: 'relative',
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.12,
        shadowRadius: 12,
      },
      android: {
        elevation: 3,
      },
      web: {
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.06)',
      } as any,
    }),
  },
  specularSheen: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 36,
    opacity: 0.5,
  },
});
