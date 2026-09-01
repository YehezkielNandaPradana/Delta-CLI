import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';

interface ThinkingIndicatorProps {
  statusText?: string;
}

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
  statusText = 'Delta is thinking...',
}) => {
  const { colors, isDark } = useThemeColors();

  // Wave / Pulse animations for 3 dots
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;
  const orbScale = useRef(new Animated.Value(1)).current;
  const shimmerAnim = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    // Staggered bounce for wave dots
    const createBounce = (anim: Animated.Value, delay: number) => {
      return Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(anim, {
            toValue: -6,
            duration: 400,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 400,
            easing: Easing.in(Easing.quad),
            useNativeDriver: true,
          }),
          Animated.delay(200),
        ])
      );
    };

    const anim1 = createBounce(dot1, 0);
    const anim2 = createBounce(dot2, 160);
    const anim3 = createBounce(dot3, 320);

    // Orb breathing pulse
    const orbPulse = Animated.loop(
      Animated.sequence([
        Animated.timing(orbScale, {
          toValue: 1.12,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(orbScale, {
          toValue: 1,
          duration: 1000,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );

    // Shimmer glow pulse
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0.4,
          duration: 900,
          useNativeDriver: true,
        }),
      ])
    );

    anim1.start();
    anim2.start();
    anim3.start();
    orbPulse.start();
    shimmer.start();

    return () => {
      anim1.stop();
      anim2.stop();
      anim3.stop();
      orbPulse.stop();
      shimmer.stop();
    };
  }, []);

  return (
    <View style={styles.wrapper}>
      <View
        style={[
          styles.container,
          {
            backgroundColor: colors.cardBg,
            borderColor: colors.cardBorder,
            borderTopColor: colors.cardSpecular,
            shadowColor: isDark ? '#000000' : '#1e3a8a',
          },
        ]}
      >
        {/* Glowing Orb Indicator */}
        <Animated.View
          style={[
            styles.orbBadge,
            {
              backgroundColor: colors.accentGreenSubtle,
              borderColor: colors.accentGreen,
              transform: [{ scale: orbScale }],
            },
          ]}
        >
          <Ionicons name="sparkles" size={14} color={colors.accentGreen} />
        </Animated.View>

        {/* Dynamic Status Text */}
        <Text style={[styles.statusText, { color: colors.textSecondary }]}>
          {statusText}
        </Text>

        {/* 3-Dot Fluid Liquid Wave */}
        <View style={styles.dotsRow}>
          <Animated.View
            style={[
              styles.dot,
              {
                backgroundColor: colors.accentGreen,
                transform: [{ translateY: dot1 }],
                opacity: shimmerAnim,
              },
            ]}
          />
          <Animated.View
            style={[
              styles.dot,
              {
                backgroundColor: colors.accentCyan,
                transform: [{ translateY: dot2 }],
                opacity: shimmerAnim,
              },
            ]}
          />
          <Animated.View
            style={[
              styles.dot,
              {
                backgroundColor: colors.accentPurple,
                transform: [{ translateY: dot3 }],
                opacity: shimmerAnim,
              },
            ]}
          />
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    paddingHorizontal: 16,
    marginVertical: 8,
    alignItems: 'flex-start',
  },
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 22,
    borderWidth: 1,
    borderTopWidth: 1.5,
    gap: 10,
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.12,
        shadowRadius: 8,
      },
      android: {
        elevation: 3,
      },
      web: {
        boxShadow: '0 4px 16px rgba(59, 130, 246, 0.12)',
      } as any,
    }),
  },
  orbBadge: {
    width: 26,
    height: 26,
    borderRadius: 13,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusText: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginLeft: 2,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
});
