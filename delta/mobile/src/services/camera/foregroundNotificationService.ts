import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

const NOTIFICATION_CHANNEL_ID = 'delta_camera_monitoring_channel';
const NOTIFICATION_IDENTIFIER = 'delta_camera_monitoring_foreground_notification';

// Configure notification behavior for persistent foreground notification
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

export class ForegroundCameraNotificationManager {
  private static isInitialized = false;

  /**
   * Setup Android Notification Channel with high importance for Foreground Service
   */
  static async setupNotificationChannel(): Promise<void> {
    if (Platform.OS !== 'android' || this.isInitialized) return;

    try {
      await Notifications.setNotificationChannelAsync(NOTIFICATION_CHANNEL_ID, {
        name: 'Delta Camera Monitoring',
        importance: Notifications.AndroidImportance.HIGH,
        description: 'Menampilkan status aktif monitoring kamera Delta',
        lockscreenVisibility: Notifications.AndroidNotificationVisibility.PUBLIC,
        sound: null,
        vibrationPattern: [0, 0],
        enableLights: true,
        lightColor: '#38bdf8',
      });

      // Register interactive notification category with 'Hentikan' action
      await Notifications.setNotificationCategoryAsync('camera_monitoring_actions', [
        {
          identifier: 'ACTION_STOP_MONITORING',
          buttonTitle: 'Hentikan',
          options: {
            isDestructive: true,
            isAuthenticationRequired: false,
            opensAppToForeground: false,
          },
        },
      ]);

      this.isInitialized = true;
    } catch (_) {}
  }

  /**
   * Display sticky, persistent notification while monitoring
   */
  static async showMonitoringNotification(deviceName: string): Promise<void> {
    if (Platform.OS !== 'android') return;
    await this.setupNotificationChannel();

    try {
      // Dismiss any prior notification first
      await Notifications.dismissNotificationAsync(NOTIFICATION_IDENTIFIER);

      await Notifications.scheduleNotificationAsync({
        identifier: NOTIFICATION_IDENTIFIER,
        content: {
          title: '● Camera Monitoring Aktif',
          body: `Streaming aktif ke Delta Web (${deviceName}). Sentuh untuk mengontrol.`,
          data: { action: 'open_camera_control' },
          sticky: true,
          autoDismiss: false,
          categoryIdentifier: 'camera_monitoring_actions',
          color: '#0284c7',
        },
        trigger: null, // show immediately
      });
    } catch (_) {}
  }

  /**
   * Dismiss persistent notification upon stopping monitoring
   */
  static async dismissNotification(): Promise<void> {
    if (Platform.OS !== 'android') return;
    try {
      await Notifications.dismissNotificationAsync(NOTIFICATION_IDENTIFIER);
    } catch (_) {}
  }

  /**
   * Listen for user tapping notification action 'Hentikan'
   */
  static registerNotificationActionListener(onStop: () => void): () => void {
    const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
      const actionId = response.actionIdentifier;
      if (
        actionId === 'ACTION_STOP_MONITORING' ||
        actionId === Notifications.DEFAULT_ACTION_IDENTIFIER
      ) {
        if (actionId === 'ACTION_STOP_MONITORING') {
          onStop();
        }
      }
    });

    return () => {
      subscription.remove();
    };
  }
}
