import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Easing,
  Platform,
  LayoutAnimation,
  UIManager,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { AgentStep } from '../../types/events';
import { formatDuration } from '../../utils/formatters';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface ThinkingIndicatorProps {
  statusText?: string;
  steps?: AgentStep[];
}

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({
  statusText = 'Delta is thinking...',
  steps = [],
}) => {
  const { colors, isDark } = useThemeColors();

  // Wave / Pulse animations for 3 dots
  const dot1 = useRef(new Animated.Value(0)).current;
  const dot2 = useRef(new Animated.Value(0)).current;
  const dot3 = useRef(new Animated.Value(0)).current;
  const orbScale = useRef(new Animated.Value(1)).current;
  const shimmerAnim = useRef(new Animated.Value(0.4)).current;

  // Toggle expandable tree state
  const [showTree, setShowTree] = useState(false);

  useEffect(() => {
    // Staggered bounce for wave dots
    const createBounce = (anim: Animated.Value, delay: number) => {
      return Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(anim, {
            toValue: -5,
            duration: 380,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 380,
            easing: Easing.in(Easing.quad),
            useNativeDriver: true,
          }),
          Animated.delay(180),
        ])
      );
    };

    const anim1 = createBounce(dot1, 0);
    const anim2 = createBounce(dot2, 140);
    const anim3 = createBounce(dot3, 280);

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
          duration: 850,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0.4,
          duration: 850,
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

  const handleToggleTree = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setShowTree(!showTree);
  };

  const realSteps = steps.filter((s) => s.kind !== 'root');

  return (
    <View style={styles.wrapper}>
      <View
        style={[
          styles.container,
          {
            backgroundColor: colors.bgSurface,
            borderColor: colors.border,
            shadowColor: isDark ? '#000000' : '#000000',
          },
        ]}
      >
        {/* Clickable Header Button to reveal Process Tree */}
        <TouchableOpacity
          onPress={handleToggleTree}
          activeOpacity={0.8}
          style={styles.clickableHeader}
        >
          {/* Unchanged Original Orb Icon */}
          <Animated.View
            style={[
              styles.orbBadge,
              {
                backgroundColor: isDark ? '#262626' : '#E5E5E5',
                borderColor: colors.border,
                transform: [{ scale: orbScale }],
              },
            ]}
          >
            <Ionicons name="sparkles" size={13} color={colors.textPrimary} />
          </Animated.View>

          {/* Dynamic Status Text */}
          <Text style={[styles.statusText, { color: colors.textPrimary }]} numberOfLines={1}>
            {statusText}
          </Text>

          {/* 3-Dot Fluid Liquid Wave Animation */}
          <View style={styles.dotsRow}>
            <Animated.View
              style={[
                styles.dot,
                {
                  backgroundColor: colors.textPrimary,
                  transform: [{ translateY: dot1 }],
                  opacity: shimmerAnim,
                },
              ]}
            />
            <Animated.View
              style={[
                styles.dot,
                {
                  backgroundColor: colors.textSecondary,
                  transform: [{ translateY: dot2 }],
                  opacity: shimmerAnim,
                },
              ]}
            />
            <Animated.View
              style={[
                styles.dot,
                {
                  backgroundColor: colors.textMuted,
                  transform: [{ translateY: dot3 }],
                  opacity: shimmerAnim,
                },
              ]}
            />
          </View>

          {/* Tree Toggle Indicator Icon */}
          <Ionicons
            name={showTree ? 'chevron-up' : 'chevron-down'}
            size={14}
            color={colors.textMuted}
            style={{ marginLeft: 6 }}
          />
        </TouchableOpacity>

        {/* Real Branching Working Tree View (Rendered only when expanded) */}
        {showTree && (
          <View style={[styles.treeContainer, { borderTopColor: colors.border }]}>
            {/* Root Execution Node */}
            <View style={styles.treeNode}>
              <View style={styles.nodeBranch}>
                <View style={[styles.nodeDot, { backgroundColor: colors.textPrimary }]} />
                <View style={[styles.verticalLine, { backgroundColor: colors.border }]} />
              </View>
              <View style={styles.nodeBody}>
                <Text style={[styles.nodeTitle, { color: colors.textPrimary }]}>
                  Delta Orchestrator (Root Task)
                </Text>
                <Text style={[styles.nodeSub, { color: colors.textMuted }]}>
                  Analyzing prompt context & dispatching execution pipeline
                </Text>
              </View>
            </View>

            {/* Real Dynamic Sub-Steps Branching */}
            {realSteps.length > 0 ? (
              realSteps.map((step, idx) => {
                const isLast = idx === realSteps.length - 1;
                const isRunning = step.status === 'running';
                const isFailed = step.status === 'failed';

                let stepTitle = step.label || step.id;
                let stepSub = '';
                if (step.command) {
                  stepTitle = `$ ${step.command}`;
                } else if (step.file_path) {
                  const fname = step.file_path.split(/[/\\]/).pop();
                  stepTitle = `${step.tool_name || 'Tool'}: ${fname}`;
                  stepSub = step.file_path;
                }

                const dur = formatDuration(step.duration_ms);

                return (
                  <View key={step.id || idx.toString()} style={styles.treeNode}>
                    <View style={styles.nodeBranch}>
                      <View
                        style={[
                          styles.subDot,
                          {
                            backgroundColor: isRunning
                              ? colors.textPrimary
                              : isFailed
                              ? colors.error
                              : colors.textMuted,
                          },
                        ]}
                      />
                      {!isLast && (
                        <View style={[styles.verticalLine, { backgroundColor: colors.border }]} />
                      )}
                    </View>

                    <View style={styles.nodeBody}>
                      <View style={styles.nodeTitleRow}>
                        <Text
                          style={[
                            styles.nodeStepTitle,
                            {
                              color: isRunning ? colors.textPrimary : colors.textSecondary,
                              fontWeight: isRunning ? '700' : '500',
                            },
                          ]}
                          numberOfLines={1}
                        >
                          {stepTitle}
                        </Text>
                        {dur ? (
                          <Text style={[styles.nodeDuration, { color: colors.textMuted }]}>
                            {dur}
                          </Text>
                        ) : null}
                      </View>

                      {stepSub ? (
                        <Text style={[styles.nodeSub, { color: colors.textMuted }]} numberOfLines={1}>
                          ↳ {stepSub}
                        </Text>
                      ) : null}
                    </View>
                  </View>
                );
              })
            ) : (
              /* Live Realtime Thinking Branch Node */
              <View style={styles.treeNode}>
                <View style={styles.nodeBranch}>
                  <View style={[styles.subDot, { backgroundColor: colors.textPrimary }]} />
                </View>
                <View style={styles.nodeBody}>
                  <Text style={[styles.nodeStepTitle, { color: colors.textPrimary, fontWeight: '700' }]}>
                    Reasoning & Synthesizing Response...
                  </Text>
                  <Text style={[styles.nodeSub, { color: colors.textMuted }]}>
                    Active model streaming response tokens
                  </Text>
                </View>
              </View>
            )}
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    paddingHorizontal: 16,
    marginVertical: 6,
    width: '100%',
  },
  container: {
    borderRadius: 18,
    borderWidth: 1,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 3 },
        shadowOpacity: 0.1,
        shadowRadius: 6,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  clickableHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 9,
    gap: 8,
  },
  orbBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusText: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: -0.2,
    flex: 1,
  },
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3.5,
  },
  dot: {
    width: 5.5,
    height: 5.5,
    borderRadius: 2.75,
  },
  treeContainer: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 4,
  },
  treeNode: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    minHeight: 28,
  },
  nodeBranch: {
    width: 18,
    alignItems: 'center',
    marginRight: 8,
  },
  nodeDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    marginTop: 4,
  },
  subDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    marginTop: 5,
  },
  verticalLine: {
    width: 1.5,
    flex: 1,
    marginTop: 2,
    marginBottom: -4,
  },
  nodeBody: {
    flex: 1,
    paddingBottom: 4,
  },
  nodeTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  nodeTitle: {
    fontSize: 12.5,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
  nodeStepTitle: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    flex: 1,
    marginRight: 6,
  },
  nodeSub: {
    fontSize: 10.5,
    marginTop: 1,
  },
  nodeDuration: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
});
