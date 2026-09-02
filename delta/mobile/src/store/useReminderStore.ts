import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Haptics from 'expo-haptics';
import { ReminderItem } from '../types/reminder';
import { scheduleNativeNotification } from '../services/notifications/nativeNotificationService';

const STORAGE_KEY = '@delta_reminders';

interface ReminderState {
  reminders: ReminderItem[];
  activeNotification: ReminderItem | null;
  isLoaded: boolean;

  loadReminders: () => Promise<void>;
  createReminder: (params: { title: string; delayMinutes?: number; targetTimestamp?: number; note?: string }) => Promise<ReminderItem>;
  completeReminder: (id: string) => Promise<void>;
  dismissActiveNotification: () => void;
  checkDueReminders: () => void;
}

const persistReminders = async (reminders: ReminderItem[]) => {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(reminders));
  } catch (e) {
    console.warn('Failed to save reminders', e);
  }
};

export const useReminderStore = create<ReminderState>((set, get) => ({
  reminders: [],
  activeNotification: null,
  isLoaded: false,

  loadReminders: async () => {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        set({ reminders: Array.isArray(parsed) ? parsed : [], isLoaded: true });
        return;
      }
    } catch (_) {}
    set({ isLoaded: true });
  },

  createReminder: async ({ title, delayMinutes = 1, targetTimestamp, note }) => {
    const delaySec = Math.max(1, Math.round(delayMinutes * 60));
    const target = targetTimestamp || (Date.now() + delaySec * 1000);
    const item: ReminderItem = {
      id: `rem_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      title: title || 'Pengingat Delta',
      targetTime: target,
      note: note || '',
      isTriggered: false,
      isCompleted: false,
      createdAt: Date.now(),
    };

    const updated = [item, ...get().reminders];
    set({ reminders: updated });
    await persistReminders(updated);

    // Schedule system native notification to device status bar & lockscreen
    scheduleNativeNotification({
      title: item.title,
      body: item.note || 'Waktunya memeriksa pengingat Delta Anda.',
      secondsFromNow: delaySec,
    });

    return item;
  },

  completeReminder: async (id: string) => {
    const updated = get().reminders.map((r) =>
      r.id === id ? { ...r, isCompleted: true } : r
    );
    set({
      reminders: updated,
      activeNotification: get().activeNotification?.id === id ? null : get().activeNotification,
    });
    await persistReminders(updated);
  },

  dismissActiveNotification: () => {
    set({ activeNotification: null });
  },

  checkDueReminders: () => {
    const now = Date.now();
    const { reminders, activeNotification } = get();

    const dueItem = reminders.find(
      (r) => !r.isTriggered && !r.isCompleted && r.targetTime <= now
    );

    if (dueItem && (!activeNotification || activeNotification.id !== dueItem.id)) {
      // Trigger haptics alert
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});

      const updated = reminders.map((r) =>
        r.id === dueItem.id ? { ...r, isTriggered: true } : r
      );

      set({
        reminders: updated,
        activeNotification: dueItem,
      });

      persistReminders(updated);
    }
  },
}));
