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
import { CameraMonitoringPermissionDialog } from '../src/components/camera/CameraMonitoringPermissionDialog';
import { ActiveMonitoringIndicator } from '../src/components/camera/ActiveMonitoringIndicator';
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
      // 1. Direct AgentStep payload from agent_step_*
      if (event.type.startsWith('agent_step_') && event.payload?.step) {
        updateStep(event.payload.step);
      }

      // 2. Realtime Tool Start (npm/pip install, web search, browser, file, etc.)
      if (event.type === 'tool_start' && event.tool) {
        const inputData = event.input || {};
        let label = event.tool;
        const cmd = inputData.command || event.command;
        const filePath = inputData.path || inputData.file_path || event.path;
        let kind: any = 'tool';

        if (event.tool === 'execute_command' && cmd) {
          label = `$ ${cmd}`;
          kind = 'command';
        } else if (event.tool.includes('browser') || event.tool.includes('chromium')) {
          label = `browser: ${inputData.url || inputData.action || 'navigating...'}`;
        } else if (event.tool.includes('search')) {
          label = `search: "${inputData.query || ''}"`;
          kind = 'search';
        } else if (filePath) {
          const fname = filePath.split(/[/\\]/).pop();
          label = `${event.tool}: ${fname}`;
        }

        const stepId = event.step_id || `tool_${event.tool}_${Date.now()}`;
        updateStep({
          id: stepId,
          task_id: event.task_id || 'root',
          execution_id: event.execution_id || 'exec',
          kind,
          label,
          status: 'running',
          tool_name: event.tool,
          command: cmd,
          file_path: filePath,
          created_at: event.timestamp || Date.now() / 1000,
          started_at: event.timestamp || Date.now() / 1000,
        });
      }

      // 3. Realtime Tool Result
      if (event.type === 'tool_result' && event.tool) {
        const activeSteps = useChatStore.getState().activeSteps;
        const matching = Object.values(activeSteps).reverse().find(
          (s) => s.tool_name === event.tool && s.status === 'running'
        );
        const stepId = matching?.id || event.step_id || `tool_${event.tool}_${Date.now()}`;
        const started = matching?.started_at ? matching.started_at * 1000 : undefined;
        const dur = event.duration_ms || (started ? Date.now() - started : undefined);

        updateStep({
          id: stepId,
          task_id: event.task_id || 'root',
          execution_id: event.execution_id || 'exec',
          kind: matching?.kind || 'tool',
          label: matching?.label || event.tool,
          command: matching?.command,
          file_path: matching?.file_path,
          tool_name: event.tool,
          status: event.success !== false ? 'completed' : 'failed',
          duration_ms: dur,
          completed_at: Date.now() / 1000,
          output_preview: typeof event.output === 'string' ? event.output : undefined,
        });
      }

      // 4. Command Lifecycle
      if (event.type === 'command_start' && event.command) {
        const stepId = event.step_id || `cmd_${Date.now()}`;
        updateStep({
          id: stepId,
          task_id: event.task_id || 'root',
          execution_id: event.execution_id || 'exec',
          kind: 'command',
          label: `$ ${event.command}`,
          command: event.command,
          status: 'running',
          created_at: event.timestamp || Date.now() / 1000,
          started_at: event.timestamp || Date.now() / 1000,
        });
      } else if (event.type === 'command_completed' && event.command) {
        const activeSteps = useChatStore.getState().activeSteps;
        const matching = Object.values(activeSteps).reverse().find(
          (s) => s.command === event.command && s.status === 'running'
        );
        const stepId = matching?.id || event.step_id || `cmd_${Date.now()}`;
        updateStep({
          id: stepId,
          task_id: event.task_id || 'root',
          execution_id: event.execution_id || 'exec',
          kind: 'command',
          label: `$ ${event.command}`,
          command: event.command,
          status: event.exit_code === 0 ? 'completed' : 'failed',
          duration_ms: matching?.started_at ? Date.now() - matching.started_at * 1000 : undefined,
          completed_at: Date.now() / 1000,
        });
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
      <CameraMonitoringPermissionDialog />
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
