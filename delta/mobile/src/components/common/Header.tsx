import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { useConnectionStore } from '../../store/useConnectionStore';
import { useSettingsStore } from '../../store/useSettingsStore';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  countBadge?: string | number;
  showStatus?: boolean;
  onRouterWarningPress?: () => void;
  onTitlePress?: () => void;
  rightAction?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'Delta',
  subtitle,
  countBadge,
  showStatus = true,
  onTitlePress,
  rightAction,
}) => {
  const { colors, isDark, toggleTheme } = useThemeColors();
  const { isConnected } = useConnectionStore();
  const { connectionMode } = useSettingsStore();

  const isLive = connectionMode === 'cloud' || isConnected;

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: colors.bgPrimary,
          borderBottomColor: colors.border,
          shadowColor: isDark ? '#FFFFFF' : '#000000',
        },
      ]}
    >
      {/* Title with iOS Editorial style */}
      <View style={styles.titleRow}>
        <TouchableOpacity
          onPress={onTitlePress}
          activeOpacity={onTitlePress ? 0.7 : 1}
          style={styles.titleWrapper}
        >
          <Text style={[styles.title, { color: colors.textPrimary }]}>{title}</Text>
          {countBadge !== undefined ? (
            <Text style={[styles.countBadge, { color: colors.textMuted }]}>
              {countBadge}
            </Text>
          ) : null}
          {onTitlePress && (
            <Ionicons name="chevron-down" size={15} color={colors.textSecondary} style={{ marginLeft: 2, marginTop: 4 }} />
          )}
        </TouchableOpacity>

        {/* Right Actions */}
        <View style={styles.rightActions}>
          {rightAction}

          {showStatus && (
            <View
              style={styles.microStatusContainer}
              accessibilityLabel={`Connection status: ${connectionMode === 'cloud' ? 'CLOUD' : (isConnected ? 'LOCAL' : 'OFFLINE')}`}
            >
              <Ionicons
                name={isLive ? (connectionMode === 'cloud' ? 'cloud-done' : 'hardware-chip-outline') : 'cloud-offline-outline'}
                size={18}
                color={isLive ? colors.textPrimary : colors.textDim}
              />
            </View>
          )}

          <TouchableOpacity
            onPress={toggleTheme}
            style={[
              styles.iconButton,
              {
                backgroundColor: colors.bgSurface,
                borderColor: colors.border,
              },
            ]}
            activeOpacity={0.7}
            accessibilityLabel="Toggle Theme"
          >
            <Ionicons
              name={isDark ? 'moon-outline' : 'sunny-outline'}
              size={15}
              color={colors.textSecondary}
            />
          </TouchableOpacity>
        </View>
      </View>

      {subtitle && (
        <Text style={[styles.subtitle, { color: colors.textMuted }]}>
          {subtitle}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 6,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  titleWrapper: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: -0.6,
  },
  countBadge: {
    fontSize: 13,
    fontWeight: '500',
  },
  subtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  rightActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  microStatusContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
  iconButton: {
    width: 34,
    height: 34,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
