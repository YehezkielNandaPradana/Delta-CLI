import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useReminderStore } from '../../store/useReminderStore';
import { useThemeColors } from '../../theme/theme';

export const NotificationBanner: React.FC = () => {
  const { colors, isDark } = useThemeColors();
  const { activeNotification, dismissActiveNotification, completeReminder } = useReminderStore();

  const slideAnim = useRef(new Animated.Value(-120)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (activeNotification) {
      // Slide Down Entrance
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        bounciness: 8,
      }).start();

      // Breathing Icon Pulse
      const pulseLoop = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.25,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      );
      pulseLoop.start();

      return () => pulseLoop.stop();
    } else {
      Animated.timing(slideAnim, {
        toValue: -120,
        duration: 250,
        useNativeDriver: true,
      }).start();
    }
  }, [activeNotification]);

  if (!activeNotification) return null;

  const handleDone = () => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    completeReminder(activeNotification.id);
  };

  const handleDismiss = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    dismissActiveNotification();
  };

  return (
    <Animated.View
      style={[
        styles.wrapper,
        {
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      <View
        style={[
          styles.islandContainer,
          {
            backgroundColor: isDark ? '#141414' : '#000000',
            borderColor: isDark ? '#2E2E2E' : '#333333',
          },
        ]}
      >
        {/* Left Pulse Icon */}
        <Animated.View style={[styles.iconBox, { transform: [{ scale: pulseAnim }] }]}>
          <Ionicons name="notifications" size={17} color="#FFFFFF" />
        </Animated.View>

        {/* Content Body */}
        <View style={styles.textContainer}>
          <View style={styles.topMetaRow}>
            <Text style={styles.badgeLabel}>DELTA PENGINGAT</Text>
            <Text style={styles.timeLabel}>Sekarang</Text>
          </View>
          <Text style={styles.titleText} numberOfLines={1}>
            {activeNotification.title}
          </Text>
          {activeNotification.note ? (
            <Text style={styles.noteText} numberOfLines={1}>
              {activeNotification.note}
            </Text>
          ) : null}
        </View>

        {/* Actions Right */}
        <View style={styles.actionButtons}>
          <TouchableOpacity
            onPress={handleDone}
            style={styles.doneBtn}
            activeOpacity={0.7}
          >
            <Ionicons name="checkmark" size={15} color="#000000" />
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleDismiss}
            style={styles.dismissBtn}
            activeOpacity={0.7}
          >
            <Ionicons name="close" size={14} color="#888888" />
          </TouchableOpacity>
        </View>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 48 : 20,
    left: 14,
    right: 14,
    zIndex: 9999,
    alignItems: 'center',
  },
  islandContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    maxWidth: 420,
    borderRadius: 22,
    borderWidth: 1.2,
    paddingHorizontal: 14,
    paddingVertical: 10,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.35,
        shadowRadius: 16,
      },
      android: {
        elevation: 12,
      },
    }),
  },
  iconBox: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  textContainer: {
    flex: 1,
    marginRight: 8,
  },
  topMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  badgeLabel: {
    color: '#A3A3A3',
    fontSize: 9.5,
    fontWeight: '800',
    letterSpacing: 0.6,
  },
  timeLabel: {
    color: '#737373',
    fontSize: 10,
  },
  titleText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
  noteText: {
    color: '#A3A3A3',
    fontSize: 11.5,
    marginTop: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  doneBtn: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dismissBtn: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: 'rgba(255, 255, 255, 0.10)',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
