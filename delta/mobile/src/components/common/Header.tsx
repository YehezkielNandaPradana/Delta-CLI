import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Platform,
  Image,
} from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { useConnectionStore } from '../../store/useConnectionStore';
import { useSettingsStore } from '../../store/useSettingsStore';
import { ModelPickerSheet } from '../chat/ModelPickerSheet';

const LOGO_SOURCE = require('../../../assets/LogoDelta.png');

interface HeaderProps {
  title?: string;
  subtitle?: string;
  showThemeToggle?: boolean;
  onRouterWarningPress?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'DELTA',
  subtitle = 'AI Workstation',
  showThemeToggle = true,
  onRouterWarningPress,
}) => {
  const { colors, isDark, toggleTheme } = useThemeColors();
  const { status, isEngineRunning, isRouterRunning, workingDirectory } = useConnectionStore();
  const { activeModel, hapticEnabled, connectionMode, cloudModel } = useSettingsStore();
  const [showModelPicker, setShowModelPicker] = useState(false);

  const handleOpenModelPicker = () => {
    if (hapticEnabled) {
      Haptics.selectionAsync().catch(() => {});
    }
    setShowModelPicker(true);
  };

  const handleThemeToggle = () => {
    if (hapticEnabled) {
      Haptics.selectionAsync().catch(() => {});
    }
    toggleTheme();
  };

  // Format clean model name
  const effectiveModel = connectionMode === 'cloud' ? (cloudModel || 'ag/gemini-3.7-flash-high') : (activeModel || 'Model');
  let cleanModel = effectiveModel;
  if (cleanModel.includes('/')) {
    cleanModel = cleanModel.split('/').pop() || cleanModel;
  }
  if (cleanModel.length > 18) {
    cleanModel = cleanModel.substring(0, 17) + '…';
  }

  // Workspace shortened path
  let shortCwd = workingDirectory ? workingDirectory.replace(/^[A-Z]:[/\\]Users[/\\][^/\\]+/i, '~').replace(/\\/g, '/') : '~/workspace';
  if (shortCwd.length > 20) {
    shortCwd = '…' + shortCwd.slice(-18);
  }

  const isConnected = status === 'connected';

  return (
    <View
      style={[
        styles.wrapper,
        {
          backgroundColor: colors.bgPrimary,
          borderBottomColor: colors.cardBorder,
        },
      ]}
    >
      {/* Top Specular Glass Ambient Line */}
      <View
        style={[
          styles.ambientHairline,
          {
            backgroundColor: isDark
              ? 'rgba(59, 130, 246, 0.28)'
              : 'rgba(29, 78, 216, 0.2)',
          },
        ]}
      />

      {/* MAIN TOP ROW */}
      <View style={styles.topRow}>
        {/* BRAND IDENTITY */}
        <View style={styles.brandContainer}>
          <View
            style={[
              styles.logoFrame,
              {
                backgroundColor: colors.bgSurface,
                borderColor: isConnected ? colors.accentGreenGlow : colors.cardBorder,
              },
            ]}
          >
            <Image
              source={LOGO_SOURCE}
              style={styles.logoImg}
              resizeMode="contain"
            />
          </View>

          <View style={styles.brandMeta}>
            <View style={styles.titleLine}>
              <Text style={[styles.brandTitleText, { color: colors.textPrimary }]}>
                {title}
              </Text>
              <View
                style={[
                  styles.versionTag,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.cardBorder,
                  },
                ]}
              >
                <Text style={[styles.versionTagText, { color: colors.accentNavyLight || colors.accentGreen }]}>
                  v1.0
                </Text>
              </View>
            </View>

            <View style={styles.cwdRow}>
              <Feather name="folder" size={9.5} color={colors.textMuted} />
              <Text style={[styles.cwdText, { color: colors.textMuted }]} numberOfLines={1}>
                {shortCwd}
              </Text>
            </View>
          </View>
        </View>

        {/* RIGHT CONTROLS */}
        <View style={styles.controlsContainer}>
          {/* 9Router Status Indicator / Warning Trigger (Only shown in local mode) */}
          {connectionMode === 'local' && !isRouterRunning ? (
            <TouchableOpacity
              onPress={onRouterWarningPress}
              style={[
                styles.routerAlertBtn,
                {
                  backgroundColor: colors.accentYellowSubtle,
                  borderColor: colors.accentYellow,
                },
              ]}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              accessibilityRole="button"
              accessibilityLabel="9Router offline alert"
            >
              <View style={[styles.routerAlertDot, { backgroundColor: colors.accentYellow }]} />
              <Ionicons name="flash-off" size={11} color={colors.accentYellow} />
              <Text style={[styles.routerAlertText, { color: colors.accentYellow }]}>
                OFFLINE
              </Text>
            </TouchableOpacity>
          ) : null}

          {/* Theme Mode Toggle */}
          {showThemeToggle && (
            <TouchableOpacity
              onPress={handleThemeToggle}
              style={[
                styles.controlBtn,
                {
                  backgroundColor: colors.bgSurface,
                  borderColor: colors.cardBorder,
                },
              ]}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              accessibilityRole="button"
              accessibilityLabel="Toggle Theme Mode"
            >
              <Ionicons
                name={isDark ? 'sunny' : 'moon'}
                size={13}
                color={isDark ? colors.accentYellow : colors.accentPurple}
              />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* SECONDARY HUD TELEMETRY DOCK */}
      <View
        style={[
          styles.hudDock,
          {
            backgroundColor: colors.cardBg,
            borderColor: colors.cardBorder,
          },
        ]}
      >
        {/* Connection & Engine State */}
        <View style={styles.hudStateBox}>
          <View
            style={[
              styles.connectionIndicatorDot,
              {
                backgroundColor:
                  status === 'connected'
                    ? (isEngineRunning ? colors.accentCyan : '#10b981')
                    : status === 'connecting'
                    ? colors.accentYellow
                    : colors.accentRed,
              },
            ]}
          />
          <Text style={[styles.hudStateText, { color: colors.textSecondary }]}>
            {status === 'connected' ? (isEngineRunning ? 'PROCESSING' : 'ONLINE') : status.toUpperCase()}
          </Text>
        </View>

        <View style={[styles.hudDivider, { backgroundColor: colors.cardBorder }]} />

        {/* Clickable AI Model Picker Selector */}
        <TouchableOpacity
          style={styles.hudModelSelector}
          onPress={handleOpenModelPicker}
          activeOpacity={0.7}
          accessibilityRole="button"
          accessibilityLabel={`Active model: ${cleanModel}. Tap to change.`}
        >
          <Ionicons name="hardware-chip-outline" size={12} color={colors.accentGreen} />
          <Text style={[styles.hudModelText, { color: colors.textPrimary }]} numberOfLines={1}>
            {cleanModel}
          </Text>
          <Feather name="chevron-down" size={11} color={colors.textMuted} />
        </TouchableOpacity>
      </View>

      {/* Modal Model Picker Sheet */}
      <ModelPickerSheet
        visible={showModelPicker}
        onClose={() => setShowModelPicker(false)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    paddingHorizontal: 14,
    paddingTop: 4,
    paddingBottom: 10,
    borderBottomWidth: 1,
    gap: 8,
  },
  ambientHairline: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 1.5,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brandContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  logoFrame: {
    width: 36,
    height: 36,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.3,
        shadowRadius: 6,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  logoImg: {
    width: 28,
    height: 28,
  },
  brandMeta: {
    justifyContent: 'center',
    gap: 1,
  },
  titleLine: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  brandTitleText: {
    fontSize: 15,
    fontWeight: '900',
    letterSpacing: 1.5,
    fontFamily: 'monospace',
  },
  versionTag: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 8,
    borderWidth: 1,
  },
  versionTagText: {
    fontSize: 8.5,
    fontWeight: '800',
    letterSpacing: 0.5,
    fontFamily: 'monospace',
  },
  cwdRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  cwdText: {
    fontSize: 10,
    fontFamily: 'monospace',
    fontWeight: '500',
  },
  controlsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  routerAlertBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 10,
    borderWidth: 1,
  },
  routerAlertDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  routerAlertText: {
    fontSize: 9,
    fontWeight: '900',
    letterSpacing: 0.5,
    fontFamily: 'monospace',
  },
  controlBtn: {
    width: 32,
    height: 32,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  hudDock: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 14,
    borderWidth: 1,
  },
  hudStateBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  connectionIndicatorDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
  },
  hudStateText: {
    fontSize: 9.5,
    fontWeight: '800',
    letterSpacing: 0.6,
    fontFamily: 'monospace',
  },
  hudDivider: {
    width: 1,
    height: 14,
    marginHorizontal: 8,
  },
  hudModelSelector: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 6,
    paddingVertical: 2,
    paddingHorizontal: 4,
  },
  hudModelText: {
    fontSize: 11,
    fontFamily: 'monospace',
    fontWeight: '700',
    maxWidth: 180,
  },
});
