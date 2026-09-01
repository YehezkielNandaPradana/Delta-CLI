import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { useSettingsStore } from '../../store/useSettingsStore';

const TAB_CONFIG: Record<
  string,
  { label: string; activeIcon: keyof typeof Ionicons.glyphMap; inactiveIcon: keyof typeof Ionicons.glyphMap }
> = {
  index: {
    label: 'Chat',
    activeIcon: 'chatbubble-ellipses',
    inactiveIcon: 'chatbubble-ellipses-outline',
  },
  activity: {
    label: '9Router',
    activeIcon: 'git-network',
    inactiveIcon: 'git-network-outline',
  },
  history: {
    label: 'History',
    activeIcon: 'time',
    inactiveIcon: 'time-outline',
  },
  settings: {
    label: 'Settings',
    activeIcon: 'settings',
    inactiveIcon: 'settings-outline',
  },
};

export const FluidBottomBar: React.FC<BottomTabBarProps> = ({
  state,
  descriptors,
  navigation,
}) => {
  const { colors, isDark } = useThemeColors();
  const { hapticEnabled } = useSettingsStore();

  const totalTabs = state.routes.length;
  const slideAnim = useRef(new Animated.Value(state.index)).current;

  useEffect(() => {
    Animated.spring(slideAnim, {
      toValue: state.index,
      useNativeDriver: false,
      damping: 18,
      stiffness: 220,
    }).start();
  }, [state.index]);

  const handleTabPress = (route: any, index: number, isFocused: boolean) => {
    if (hapticEnabled) {
      Haptics.selectionAsync().catch(() => {});
    }

    const event = navigation.emit({
      type: 'tabPress',
      target: route.key,
      canPreventDefault: true,
    });

    if (!isFocused && !event.defaultPrevented) {
      navigation.navigate(route.name);
    }
  };

  const pillWidthPercent = 100 / (totalTabs || 1);

  const leftInterpolate = slideAnim.interpolate({
    inputRange: state.routes.map((_, i) => i),
    outputRange: state.routes.map((_, i) => `${i * pillWidthPercent}%`),
  });

  return (
    <View style={styles.floatingWrapper} pointerEvents="box-none">
      <View
        style={[
          styles.container,
          {
            backgroundColor: colors.bottomBarBg,
            borderColor: colors.bottomBarBorder,
            shadowColor: isDark ? '#000000' : '#475569',
          },
        ]}
      >
        {/* Specular Edge Line */}
        <View
          style={[
            styles.specularTopBorder,
            {
              backgroundColor: isDark
                ? 'rgba(255, 255, 255, 0.2)'
                : 'rgba(255, 255, 255, 0.9)',
            },
          ]}
        />

        {/* Animated Liquid Pill Active Slider */}
        <Animated.View
          style={[
            styles.activePillIndicator,
            {
              width: `${pillWidthPercent}%`,
              left: leftInterpolate,
            },
          ]}
        >
          <View
            style={[
              styles.pillInner,
              {
                backgroundColor: colors.bottomBarActivePill,
                borderColor: colors.accentGreen,
              },
            ]}
          />
        </Animated.View>

        {/* Tab Items */}
        <View style={styles.tabsRow}>
          {state.routes.map((route, index) => {
            const isFocused = state.index === index;
            const config = TAB_CONFIG[route.name] || {
              label: route.name,
              activeIcon: 'ellipse',
              inactiveIcon: 'ellipse-outline',
            };

            return (
              <TouchableOpacity
                key={route.key}
                onPress={() => handleTabPress(route, index, isFocused)}
                style={styles.tabButton}
                activeOpacity={0.8}
                accessibilityRole="tab"
                accessibilityState={{ selected: isFocused }}
                accessibilityLabel={config.label}
              >
                <Ionicons
                  name={isFocused ? config.activeIcon : config.inactiveIcon}
                  size={21}
                  color={isFocused ? colors.accentGreen : colors.textMuted}
                />
                <Text
                  style={[
                    styles.tabLabel,
                    {
                      color: isFocused ? colors.accentGreen : colors.textMuted,
                      fontWeight: isFocused ? '700' : '500',
                    },
                  ]}
                >
                  {config.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  floatingWrapper: {
    position: 'absolute',
    bottom: 14,
    left: 0,
    right: 0,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  container: {
    width: '100%',
    maxWidth: 420,
    height: 64,
    borderRadius: 32,
    borderWidth: 1,
    position: 'relative',
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.18,
        shadowRadius: 16,
      },
      android: {
        elevation: 6,
      },
      web: {
        boxShadow: '0 12px 32px rgba(0, 0, 0, 0.18)',
        backdropFilter: 'blur(20px)',
      } as any,
    }),
  },
  specularTopBorder: {
    position: 'absolute',
    top: 0,
    left: 16,
    right: 16,
    height: 1.2,
    borderRadius: 1,
  },
  activePillIndicator: {
    position: 'absolute',
    top: 6,
    bottom: 6,
    paddingHorizontal: 6,
  },
  pillInner: {
    flex: 1,
    borderRadius: 24,
    borderWidth: 1,
  },
  tabsRow: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
    paddingVertical: 6,
    zIndex: 2,
  },
  tabLabel: {
    fontSize: 10.5,
    letterSpacing: 0.2,
  },
});
