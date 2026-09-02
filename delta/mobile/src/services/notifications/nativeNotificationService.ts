import { Platform } from 'react-native';

export interface NativeNotificationPayload {
  title: string;
  body: string;
  secondsFromNow?: number;
}

/**
 * Native Notification Service with safe runtime loader
 */
export async function scheduleNativeNotification(payload: NativeNotificationPayload): Promise<void> {
  try {
    const Notifications: any = require('expo-notifications');

    if (Platform.OS !== 'web' && Notifications) {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      if (finalStatus !== 'granted') {
        return;
      }

      Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowAlert: true,
          shouldPlaySound: true,
          shouldSetBadge: true,
        }),
      });

      const delaySec = Math.max(1, payload.secondsFromNow || 1);

      await Notifications.scheduleNotificationAsync({
        content: {
          title: `🔔 ${payload.title}`,
          body: payload.body,
          sound: true,
          priority: Notifications.AndroidNotificationPriority ? Notifications.AndroidNotificationPriority.HIGH : undefined,
        },
        trigger: {
          seconds: delaySec,
        },
      });
    }
  } catch (_) {
    // Fallback when running inside standard client / dev server
  }
}
