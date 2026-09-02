import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useSettingsStore } from '../src/store/useSettingsStore';
import { useChatStore } from '../src/store/useChatStore';
import { useConnectionStore } from '../src/store/useConnectionStore';
import { useReminderStore } from '../src/store/useReminderStore';
import { useSkillsStore } from '../src/store/useSkillsStore';
import { NotificationBanner } from '../src/components/common/NotificationBanner';
import { sseClient } from '../src/services/realtime/sseClient';
import { embedded9Router } from '../src/services/router/embeddedRouterEngine';
import { useThemeColors } from '../src/theme/theme';

export default function RootLayout() {
  const { loadSettings, isLoaded, connectionMode } = useSettingsStore();
  const { setIsRouterRunning } = useConnectionStore();
  const { loadReminders, checkDueReminders } = useReminderStore();
  const { updateStep, setActiveStatusText, appendStreamingText, finishExecution } = useChatStore();
  const { colors, isDark } = useThemeColors();

  useEffect(() => {
    // 1. Load persisted settings, reminders & skills
    loadSettings();
    loadReminders();
    useSkillsStore.getState().loadSkills();

    // 2. Automatically initialize embedded 9Router inside app
    embedded9Router.init();
    setIsRouterRunning(true);

    // 3. Start reminder countdown polling interval (every 4 seconds)
    const reminderInterval = setInterval(() => {
      checkDueReminders();
    }, 4000);

    return () => clearInterval(reminderInterval);
  }, []);

  useEffect(() => {
    if (!isLoaded) return;

    // Only connect local SSE stream if in local server mode
    if (connectionMode !== 'local') {
      sseClient.stop();
      return;
    }

    const unsubscribe = sseClient.subscribe((event) => {
      if (event.type.startsWith('agent_step_') && event.payload?.step) {
        updateStep(event.payload.step);
      }
      if (event.status_text) {
        setActiveStatusText(event.status_text);
      }
      if (event.type === 'message_delta' && event.content) {
        appendStreamingText(event.content);
      }
      if (event.type === 'agent_complete' || event.type === 'message_complete') {
        finishExecution();
      }
    });

    sseClient.start();

    return () => {
      unsubscribe();
      sseClient.stop();
    };
  }, [isLoaded, connectionMode]);

  return (
    <SafeAreaProvider style={{ backgroundColor: colors.bgPrimary }}>
      <StatusBar
        style={isDark ? 'light' : 'dark'}
        backgroundColor={colors.bgPrimary}
      />
      <NotificationBanner />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.bgPrimary },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="+not-found" options={{ title: 'Not Found' }} />
      </Stack>
    </SafeAreaProvider>
  );
}
