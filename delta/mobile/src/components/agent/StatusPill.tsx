import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { useThemeColors } from '../../theme/theme';
import { ConnectionStatus } from '../../store/useConnectionStore';

interface StatusPillProps {
  status: ConnectionStatus;
  isWorking?: boolean;
  modelName?: string;
  onPress?: () => void;
}

export const StatusPill: React.FC<StatusPillProps> = ({
  status,
  isWorking = false,
  modelName,
}) => {
  const { colors } = useThemeColors();
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (isWorking || status === 'connecting') {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 0.3,
            duration: 700,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 700,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isWorking, status]);

  let dotColor = colors.textDim;
  let statusText = 'Offline';
  let badgeBorder = colors.cardBorder;
  let badgeBg = colors.cardBg;

  if (status === 'connected') {
    if (isWorking) {
      dotColor = colors.accentCyan;
      statusText = 'Busy';
      badgeBorder = colors.accentCyan;
      badgeBg = colors.accentCyanSubtle;
    } else {
      dotColor = '#10b981'; // vibrant emerald
      statusText = 'Ready';
      badgeBorder = 'rgba(16, 185, 129, 0.28)';
      badgeBg = 'rgba(16, 185, 129, 0.12)';
    }
  } else if (status === 'connecting') {
    dotColor = colors.accentYellow;
    statusText = 'Sync';
    badgeBorder = colors.accentYellow;
    badgeBg = colors.accentYellowSubtle;
  } else if (status === 'error') {
    dotColor = colors.accentRed;
    statusText = 'Err';
    badgeBorder = colors.accentRed;
    badgeBg = colors.accentRedSubtle;
  }

  // Format model label for high-density header display
  let cleanModel = modelName || '';
  if (cleanModel.includes('/')) {
    cleanModel = cleanModel.split('/').pop() || cleanModel;
  }
  if (cleanModel.length > 15) {
    cleanModel = cleanModel.substring(0, 14) + '…';
  }

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: badgeBg,
          borderColor: badgeBorder,
        },
      ]}
    >
      <View style={styles.statusIndicator}>
        <Animated.View
          style={[
            styles.dot,
            {
              backgroundColor: dotColor,
              opacity: pulseAnim,
            },
          ]}
        />
        <Text style={[styles.statusText, { color: colors.textPrimary }]}>
          {statusText}
        </Text>
      </View>

      {cleanModel ? (
        <View
          style={[
            styles.modelBadge,
            {
              backgroundColor: colors.bgSurface,
              borderColor: colors.cardBorder,
            },
          ]}
        >
          <Text style={[styles.modelText, { color: colors.accentNavyLight || colors.accentGreen }]}>
            {cleanModel}
          </Text>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3.5,
    borderRadius: 4,
    borderWidth: 1,
    gap: 6,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: 1,
  },
  statusText: {
    fontSize: 9.5,
    fontWeight: '800',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    fontFamily: 'monospace',
  },
  modelBadge: {
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 3,
    borderWidth: 1,
  },
  modelText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '700',
    letterSpacing: 0.1,
  },
});
