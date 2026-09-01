import React, { useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Animated,
  PanResponder,
} from 'react-native';
import { useThemeColors } from '../../theme/theme';

interface CyberScrollbarProps {
  contentHeight: number;
  containerHeight: number;
  scrollY: Animated.Value;
  onScrollTo?: (offset: number) => void;
  visible?: boolean;
}

export const CyberScrollbar: React.FC<CyberScrollbarProps> = ({
  contentHeight,
  containerHeight,
  scrollY,
  visible = true,
}) => {
  const { colors, isDark } = useThemeColors();
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Ratio of visible track vs content
  const canScroll = contentHeight > containerHeight && containerHeight > 0;
  const scrollableRatio = containerHeight / (contentHeight || 1);
  const rawThumbHeight = containerHeight * scrollableRatio;
  const thumbHeight = Math.max(32, Math.min(rawThumbHeight, containerHeight - 20));

  const maxScrollOffset = Math.max(1, contentHeight - containerHeight);
  const maxThumbTravel = Math.max(1, containerHeight - thumbHeight - 8);

  // Animate fade-in on scroll movement, fade-out after idle
  const showScrollbar = () => {
    Animated.timing(opacityAnim, {
      toValue: 1,
      duration: 150,
      useNativeDriver: true,
    }).start();

    if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
    hideTimeoutRef.current = setTimeout(() => {
      Animated.timing(opacityAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }).start();
    }, 1400);
  };

  useEffect(() => {
    const listenerId = scrollY.addListener(() => {
      showScrollbar();
    });
    return () => {
      scrollY.removeListener(listenerId);
      if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
    };
  }, [scrollY]);

  if (!canScroll || !visible) return null;

  const translateY = scrollY.interpolate({
    inputRange: [0, maxScrollOffset],
    outputRange: [4, maxThumbTravel],
    extrapolate: 'clamp',
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={[
        styles.trackContainer,
        {
          opacity: opacityAnim,
          height: containerHeight,
        },
      ]}
    >
      {/* Subtle Track Line */}
      <View
        style={[
          styles.trackLine,
          {
            backgroundColor: isDark
              ? 'rgba(255, 255, 255, 0.04)'
              : 'rgba(0, 0, 0, 0.04)',
          },
        ]}
      />

      {/* Cyber Neon Thumb with Specular Gradient */}
      <Animated.View
        style={[
          styles.thumb,
          {
            height: thumbHeight,
            transform: [{ translateY }],
            backgroundColor: isDark ? colors.accentCyan : colors.accentGreen,
            shadowColor: isDark ? colors.accentCyan : colors.accentNavy,
          },
        ]}
      >
        {/* Thumb Core Glass Highlight */}
        <View
          style={[
            styles.thumbCore,
            {
              backgroundColor: isDark
                ? 'rgba(255, 255, 255, 0.8)'
                : 'rgba(255, 255, 255, 0.95)',
            },
          ]}
        />
      </Animated.View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  trackContainer: {
    position: 'absolute',
    right: 3,
    top: 0,
    bottom: 0,
    width: 6,
    alignItems: 'center',
    zIndex: 99,
  },
  trackLine: {
    position: 'absolute',
    top: 6,
    bottom: 6,
    width: 2,
    borderRadius: 1,
  },
  thumb: {
    width: 4,
    borderRadius: 2,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.85,
    shadowRadius: 5,
    elevation: 4,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
  },
  thumbCore: {
    width: 1.5,
    height: '60%',
    borderRadius: 1,
  },
});
