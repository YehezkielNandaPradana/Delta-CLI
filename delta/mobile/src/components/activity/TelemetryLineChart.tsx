import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  LayoutChangeEvent,
  Easing,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';

export interface DataPoint {
  label: string;
  value: number; // e.g. latency in ms or tokens/sec
  secondaryValue?: number;
}

interface TelemetryLineChartProps {
  title?: string;
  subtitle?: string;
  data: DataPoint[];
  unit?: string;
  color?: string;
  height?: number;
}

export const TelemetryLineChart: React.FC<TelemetryLineChartProps> = ({
  title = 'AI LATENCY & THROUGHPUT',
  subtitle = 'Real-time telemetry per event',
  data,
  unit = 'ms',
  color,
  height = 140,
}) => {
  const { colors, isDark } = useThemeColors();
  const [chartWidth, setChartWidth] = useState(300);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Animation values
  const progressAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  const chartColor = color || (isDark ? colors.accentCyan : colors.accentGreen);

  useEffect(() => {
    progressAnim.setValue(0);
    Animated.timing(progressAnim, {
      toValue: 1,
      duration: 1000,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
      useNativeDriver: false,
    }).start();

    // Pulse active node
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.4,
          duration: 800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 800,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ])
    );
    pulseLoop.start();

    // Shimmer scan line
    const shimmerLoop = Animated.loop(
      Animated.timing(shimmerAnim, {
        toValue: 1,
        duration: 3000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    );
    shimmerLoop.start();

    return () => {
      pulseLoop.stop();
      shimmerLoop.stop();
    };
  }, [data]);

  const handleLayout = (e: LayoutChangeEvent) => {
    setChartWidth(e.nativeEvent.layout.width);
  };

  const values = data.map((d) => d.value);
  const maxValue = Math.max(...values, 10);
  const minValue = Math.min(...values, 0);
  const range = Math.max(1, maxValue - minValue);

  // Calculate coordinates for points and segments
  const usableHeight = height - 40;
  const stepX = data.length > 1 ? (chartWidth - 44) / (data.length - 1) : 0;

  const rawPoints = data.map((d, index) => {
    const x = 22 + index * stepX;
    const normalizedY = (d.value - minValue) / range;
    const y = usableHeight - normalizedY * usableHeight + 16;
    return { x, y, value: d.value, label: d.label };
  });

  // Generate dense Catmull-Rom spline subdivisions for smooth rounded curve
  const curveSubdivisions = 6;
  const smoothPoints: { x: number; y: number }[] = [];

  for (let i = 0; i < rawPoints.length - 1; i++) {
    const p0 = rawPoints[Math.max(0, i - 1)];
    const p1 = rawPoints[i];
    const p2 = rawPoints[i + 1];
    const p3 = rawPoints[Math.min(rawPoints.length - 1, i + 2)];

    for (let t = 0; t < curveSubdivisions; t++) {
      const u = t / curveSubdivisions;
      const u2 = u * u;
      const u3 = u2 * u;

      // Catmull-Rom spline equation
      const x = 0.5 * ((2 * p1.x) +
        (-p0.x + p2.x) * u +
        (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * u2 +
        (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * u3);

      const y = 0.5 * ((2 * p1.y) +
        (-p0.y + p2.y) * u +
        (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * u2 +
        (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * u3);

      smoothPoints.push({ x, y });
    }
  }
  if (rawPoints.length > 0) {
    smoothPoints.push({ x: rawPoints[rawPoints.length - 1].x, y: rawPoints[rawPoints.length - 1].y });
  }

  const activePoint = selectedIndex !== null ? rawPoints[selectedIndex] : rawPoints[rawPoints.length - 1];

  const shimmerTranslateX = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-60, chartWidth + 60],
  });

  return (
    <View style={styles.cardContainer} onLayout={handleLayout}>
      {/* Header Info */}
      <View style={styles.chartHeader}>
        <View>
          <View style={styles.titleRow}>
            <Ionicons name="analytics" size={13} color={chartColor} />
            <Text style={[styles.title, { color: colors.textPrimary }]}>{title}</Text>
          </View>
          <Text style={[styles.subtitle, { color: colors.textMuted }]}>{subtitle}</Text>
        </View>

        {activePoint ? (
          <View
            style={[
              styles.valBadge,
              {
                backgroundColor: isDark ? 'rgba(56, 189, 248, 0.12)' : 'rgba(29, 78, 216, 0.1)',
                borderColor: chartColor,
              },
            ]}
          >
            <Text style={[styles.valBadgeText, { color: chartColor }]}>
              {activePoint.value} {unit}
            </Text>
            <Text style={[styles.valBadgeLabel, { color: colors.textMuted }]}>
              {activePoint.label}
            </Text>
          </View>
        ) : null}
      </View>

      {/* Main Chart Area */}
      <View style={[styles.chartCanvas, { height }]}>
        {/* Background Grid Lines */}
        <View style={[styles.gridLine, { top: 16, backgroundColor: colors.cardBorder }]} />
        <View style={[styles.gridLine, { top: usableHeight / 2 + 16, backgroundColor: colors.cardBorder }]} />
        <View style={[styles.gridLine, { top: usableHeight + 16, backgroundColor: colors.cardBorder }]} />

        {/* Shimmer Light Scanner */}
        <Animated.View
          style={[
            styles.shimmerScanLine,
            {
              transform: [{ translateX: shimmerTranslateX }],
              backgroundColor: chartColor,
              shadowColor: chartColor,
            },
          ]}
        />

        {/* Vertical Curved Rounded Area Pill Underglow */}
        {rawPoints.map((p, i) => {
          const barHeight = Math.max(4, usableHeight + 16 - p.y);
          const isSelected = selectedIndex === i || (selectedIndex === null && i === rawPoints.length - 1);
          return (
            <Animated.View
              key={`bar-${i}`}
              style={[
                styles.underglowPill,
                {
                  left: p.x - 6,
                  bottom: 18,
                  height: progressAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0, barHeight],
                  }),
                  backgroundColor: isSelected
                    ? (isDark ? 'rgba(56, 189, 248, 0.28)' : 'rgba(29, 78, 216, 0.2)')
                    : 'rgba(255, 255, 255, 0.04)',
                  borderColor: isSelected ? chartColor : 'transparent',
                },
              ]}
            />
          );
        })}

        {/* Smooth Curved Spline Line Segments */}
        {smoothPoints.map((p, i) => {
          if (i === smoothPoints.length - 1) return null;
          const nextP = smoothPoints[i + 1];
          const dx = nextP.x - p.x;
          const dy = nextP.y - p.y;
          const length = Math.sqrt(dx * dx + dy * dy);
          const angle = Math.atan2(dy, dx) * (180 / Math.PI);

          return (
            <Animated.View
              key={`smooth-seg-${i}`}
              style={[
                styles.smoothLineSegment,
                {
                  left: p.x,
                  top: p.y,
                  width: progressAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0, length + 0.4],
                  }),
                  backgroundColor: chartColor,
                  transform: [
                    { rotate: `${angle}deg` },
                    { translateY: -1.5 },
                  ],
                  shadowColor: chartColor,
                  shadowOpacity: 0.8,
                  shadowRadius: 5,
                },
              ]}
            />
          );
        })}

        {/* Interactive Data Point Nodes (Round Circles) */}
        {rawPoints.map((p, i) => {
          const isLast = i === rawPoints.length - 1;
          const isSelected = selectedIndex === i;

          return (
            <TouchableOpacity
              key={`node-${i}`}
              style={[
                styles.touchableNode,
                {
                  left: p.x - 14,
                  top: p.y - 14,
                },
              ]}
              onPress={() => setSelectedIndex(i)}
              activeOpacity={0.8}
            >
              {/* Pulsing Outer Glow Ring */}
              {(isSelected || isLast) && (
                <Animated.View
                  style={[
                    styles.pulsingRing,
                    {
                      borderColor: chartColor,
                      transform: [{ scale: pulseAnim }],
                    },
                  ]}
                />
              )}

              {/* Node Core Circle */}
              <View
                style={[
                  styles.nodeCore,
                  {
                    backgroundColor: isSelected || isLast ? chartColor : colors.bgSurface,
                    borderColor: chartColor,
                  },
                ]}
              />
            </TouchableOpacity>
          );
        })}
      </View>

      {/* X-Axis Labels */}
      <View style={styles.xAxisRow}>
        {rawPoints.map((p, i) => (
          <Text
            key={`lbl-${i}`}
            style={[
              styles.xLabel,
              {
                left: p.x - 18,
                color: selectedIndex === i ? chartColor : colors.textMuted,
                fontWeight: selectedIndex === i ? '700' : '500',
              },
            ]}
          >
            {p.label}
          </Text>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    padding: 16,
    borderRadius: 20,
    borderWidth: 1,
    overflow: 'hidden',
    position: 'relative',
  },
  chartHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  title: {
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
    fontFamily: 'monospace',
  },
  subtitle: {
    fontSize: 10,
    marginTop: 2,
  },
  valBadge: {
    alignItems: 'flex-end',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    borderWidth: 1,
  },
  valBadgeText: {
    fontSize: 12,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  valBadgeLabel: {
    fontSize: 8.5,
    fontWeight: '600',
    fontFamily: 'monospace',
  },
  chartCanvas: {
    width: '100%',
    position: 'relative',
    marginVertical: 4,
  },
  gridLine: {
    position: 'absolute',
    left: 10,
    right: 10,
    height: 1,
    opacity: 0.5,
    borderRadius: 0.5,
  },
  shimmerScanLine: {
    position: 'absolute',
    top: 10,
    bottom: 20,
    width: 2,
    borderRadius: 1,
    opacity: 0.4,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.9,
    shadowRadius: 6,
  },
  underglowPill: {
    position: 'absolute',
    width: 12,
    borderRadius: 6,
    borderWidth: 1,
  },
  smoothLineSegment: {
    position: 'absolute',
    height: 3,
    borderRadius: 1.5,
    transformOrigin: 'left center' as any,
  },
  touchableNode: {
    position: 'absolute',
    width: 28,
    height: 28,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  pulsingRing: {
    position: 'absolute',
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
    opacity: 0.65,
  },
  nodeCore: {
    width: 9,
    height: 9,
    borderRadius: 4.5,
    borderWidth: 2,
  },
  xAxisRow: {
    height: 16,
    position: 'relative',
    marginTop: 2,
  },
  xLabel: {
    position: 'absolute',
    fontSize: 9,
    fontFamily: 'monospace',
    textAlign: 'center',
    width: 36,
  },
});
