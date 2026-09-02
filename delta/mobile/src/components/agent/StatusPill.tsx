import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { useConnectionStore } from '../../store/useConnectionStore';
import { useSettingsStore } from '../../store/useSettingsStore';

interface StatusPillProps {
  showModel?: boolean;
}

export const StatusPill: React.FC<StatusPillProps> = ({ showModel = true }) => {
  const { colors } = useThemeColors();
  const { isConnected } = useConnectionStore();
  const { activeModel, connectionMode } = useSettingsStore();

  let dotColor = colors.textDisabled;
  let statusLabel = 'OFFLINE';

  if (connectionMode === 'cloud') {
    dotColor = colors.success;
    statusLabel = 'CLOUD READY';
  } else if (isConnected) {
    dotColor = colors.success;
    statusLabel = 'ONLINE';
  }

  const cleanModelName = (name: string) => {
    if (!name) return 'Ollama';
    const parts = name.split('/');
    const clean = parts[parts.length - 1];
    return clean.length > 16 ? `${clean.slice(0, 15)}…` : clean;
  };

  return (
    <View
      style={[
        styles.pillContainer,
        {
          backgroundColor: colors.bgSecondary,
          borderColor: colors.border,
        },
      ]}
    >
      <View style={styles.statusSection}>
        <View style={[styles.dot, { backgroundColor: dotColor }]} />
        <Text style={[styles.statusText, { color: colors.textSecondary }]}>
          {statusLabel}
        </Text>
      </View>

      {showModel && (
        <>
          <View style={[styles.separator, { backgroundColor: colors.border }]} />
          <View style={styles.modelSection}>
            <Ionicons name="hardware-chip-outline" size={11} color={colors.accent} />
            <Text style={[styles.modelText, { color: colors.textPrimary }]} numberOfLines={1}>
              {cleanModelName(activeModel)}
            </Text>
          </View>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  pillContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
    gap: 8,
  },
  statusSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: 10.5,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  separator: {
    width: 1,
    height: 12,
  },
  modelSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    maxWidth: 140,
  },
  modelText: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: -0.1,
  },
});
