import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
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
    activeIcon: 'terminal',
    inactiveIcon: 'terminal-outline',
  },
  notes: {
    label: 'Notes',
    activeIcon: 'document-text',
    inactiveIcon: 'document-text-outline',
  },
  activity: {
    label: 'Router',
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
    activeIcon: 'settings-sharp',
    inactiveIcon: 'settings-outline',
  },
};

export const FluidBottomBar: React.FC<BottomTabBarProps> = ({
  state,
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
      damping: 24,
      stiffness: 280,
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
            backgroundColor: colors.bgSecondary,
            borderColor: colors.border,
          },
        ]}
      >
        {/* Subtle Selected Tab Active Pill */}
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
                backgroundColor: isDark ? '#262626' : '#E5E5E5',
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
                activeOpacity={0.7}
                accessibilityRole="tab"
                accessibilityState={{ selected: isFocused }}
                accessibilityLabel={config.label}
              >
                <Ionicons
                  name={isFocused ? config.activeIcon : config.inactiveIcon}
                  size={19}
                  color={isFocused ? colors.accent : colors.textMuted}
                />
                <Text
                  style={[
                    styles.tabLabel,
                    {
                      color: isFocused ? colors.textPrimary : colors.textMuted,
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
    bottom: 12,
    left: 0,
    right: 0,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  container: {
    width: '100%',
    maxWidth: 440,
    height: 58,
    borderRadius: 24,
    borderWidth: 1,
    position: 'relative',
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 6,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  activePillIndicator: {
    position: 'absolute',
    top: 4,
    bottom: 4,
    paddingHorizontal: 4,
  },
  pillInner: {
    flex: 1,
    borderRadius: 18,
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
    paddingVertical: 4,
    zIndex: 2,
  },
  tabLabel: {
    fontSize: 10,
    letterSpacing: 0.2,
  },
});
