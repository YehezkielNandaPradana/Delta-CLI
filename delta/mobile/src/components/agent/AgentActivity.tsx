import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, LayoutAnimation, Platform, UIManager } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { AgentStep } from '../../types/events';
import { formatDuration } from '../../utils/formatters';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface AgentActivityProps {
  steps?: AgentStep[];
  isRunning?: boolean;
  activeStatusText?: string;
}

export const AgentActivity: React.FC<AgentActivityProps> = ({
  steps = [],
  isRunning = false,
  activeStatusText = 'Working',
}) => {
  const { colors, isDark } = useThemeColors();
  const [isExpanded, setIsExpanded] = useState(true);

  if (steps.length === 0 && !isRunning) {
    return null;
  }

  const toggleExpand = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsExpanded(!isExpanded);
  };

  const visibleSteps = steps.filter((s) => s.kind !== 'root');

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: colors.cardBg,
          borderColor: colors.cardBorder,
          borderTopColor: colors.cardSpecular,
          borderTopWidth: 1.5,
          shadowColor: isDark ? '#000000' : '#64748b',
        },
      ]}
    >
      <TouchableOpacity
        style={[
          styles.header,
          {
            backgroundColor: colors.bgSecondary,
            borderBottomColor: colors.cardBorder,
          },
        ]}
        onPress={toggleExpand}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          <View
            style={[
              styles.iconContainer,
              {
                backgroundColor: isRunning ? colors.accentCyanSubtle : colors.accentGreenSubtle,
              },
            ]}
          >
            <Feather
              name={isRunning ? 'loader' : 'check-circle'}
              size={13}
              color={isRunning ? colors.accentCyan : colors.accentGreen}
            />
          </View>
          <Text
            style={[
              styles.title,
              { color: isRunning ? colors.accentCyan : colors.textSecondary },
            ]}
            numberOfLines={1}
          >
            {isRunning ? activeStatusText : 'Agent Execution Complete'}
          </Text>
          {visibleSteps.length > 0 && (
            <View
              style={[
                styles.stepBadge,
                {
                  backgroundColor: colors.bgSurface,
                  borderColor: colors.cardBorder,
                },
              ]}
            >
              <Text style={[styles.stepBadgeText, { color: colors.textMuted }]}>
                {visibleSteps.length}
              </Text>
            </View>
          )}
        </View>

        <Feather
          name={isExpanded ? 'chevron-up' : 'chevron-down'}
          size={14}
          color={colors.textMuted}
        />
      </TouchableOpacity>

      {isExpanded && visibleSteps.length > 0 && (
        <View style={styles.stepsList}>
          {visibleSteps.map((step, index) => {
            const isStepRunning = step.status === 'running';
            const isFailed = step.status === 'failed';
            const isLast = index === visibleSteps.length - 1;

            let iconName: any = 'check';
            let iconColor = colors.accentGreen;
            if (isStepRunning) {
              iconName = 'arrow-right';
              iconColor = colors.accentCyan;
            } else if (isFailed) {
              iconName = 'x';
              iconColor = colors.accentRed;
            }

            let primaryLabel = step.label || step.id;
            let subDetail = '';
            if (step.command) {
              primaryLabel = `$ ${step.command}`;
            } else if (step.file_path) {
              const fname = step.file_path.split(/[/\\]/).pop();
              primaryLabel = `${step.tool_name || 'File'}: ${fname}`;
              subDetail = step.file_path;
            }

            const durStr = formatDuration(step.duration_ms);

            return (
              <View key={step.id || index.toString()} style={styles.stepItem}>
                <View style={styles.treeLine}>
                  <Text style={[styles.treeLineText, { color: colors.textDim }]}>
                    {isLast ? '└─' : '├─'}
                  </Text>
                </View>

                <View style={styles.stepIcon}>
                  <Feather name={iconName} size={11} color={iconColor} />
                </View>

                <View style={styles.stepContent}>
                  <View style={styles.stepHeaderRow}>
                    <Text
                      style={[
                        styles.stepLabel,
                        { color: colors.textSecondary },
                        isStepRunning && { color: colors.accentCyan, fontWeight: '700' },
                        isFailed && { color: colors.accentRed },
                      ]}
                      numberOfLines={2}
                    >
                      {primaryLabel}
                    </Text>
                    {durStr ? (
                      <Text style={[styles.durationText, { color: colors.textDim }]}>
                        · {durStr}
                      </Text>
                    ) : null}
                  </View>

                  {subDetail && subDetail !== primaryLabel ? (
                    <Text style={[styles.subDetailText, { color: colors.textDim }]} numberOfLines={1}>
                      ↳ {subDetail}
                    </Text>
                  ) : null}
                </View>
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 18,
    borderWidth: 1,
    marginVertical: 6,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 3 },
        shadowOpacity: 0.08,
        shadowRadius: 6,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 8,
  },
  iconContainer: {
    width: 22,
    height: 22,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  title: {
    fontSize: 12,
    fontWeight: '600',
    flexShrink: 1,
  },
  stepBadge: {
    marginLeft: 8,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 10,
    borderWidth: 1,
  },
  stepBadgeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  stepsList: {
    paddingHorizontal: 12,
    paddingBottom: 10,
    paddingTop: 6,
  },
  stepItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginVertical: 2.5,
  },
  treeLine: {
    width: 16,
  },
  treeLineText: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 11,
  },
  stepIcon: {
    marginRight: 6,
    marginTop: 2,
  },
  stepContent: {
    flex: 1,
  },
  stepHeaderRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
  },
  stepLabel: {
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    flex: 1,
  },
  durationText: {
    fontSize: 10,
    marginLeft: 6,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  subDetailText: {
    fontSize: 10,
    marginTop: 1,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
});
