import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { Header } from '../../src/components/common/Header';
import { MessageList } from '../../src/components/chat/MessageList';
import { ChatInput } from '../../src/components/chat/ChatInput';
import { RouterAlertModal } from '../../src/components/chat/RouterAlertModal';
import { useChatStore } from '../../src/store/useChatStore';
import { useSettingsStore } from '../../src/store/useSettingsStore';
import { useConnectionStore } from '../../src/store/useConnectionStore';
import { sendChatMessage, cancelExecution } from '../../src/services/api/chatApi';
import { getRouterStatus } from '../../src/services/api/systemApi';
import { useThemeColors } from '../../src/theme/theme';

export default function ChatScreen() {
  const { colors } = useThemeColors();
  const {
    messages,
    activeSteps,
    isGenerating,
    activeStatusText,
    addMessage,
    startExecution,
    finishExecution,
  } = useChatStore();
  const { hapticEnabled, connectionMode } = useSettingsStore();
  const { isRouterRunning, setIsRouterRunning } = useConnectionStore();
  const [showRouterModal, setShowRouterModal] = useState(false);
  const [pendingText, setPendingText] = useState<string | null>(null);

  const executeSend = async (text: string) => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    }

    addMessage({
      sender: 'user',
      text,
    });

    const executionId = `exec_${Date.now()}`;
    startExecution(executionId);

    try {
      const res = await sendChatMessage(text, executionId);
      if (res.error) {
        addMessage({
          sender: 'delta',
          text: `[Error] ${res.error}`,
        });
      } else if (res.response || res.output) {
        addMessage({
          sender: 'delta',
          text: res.response || res.output || '',
        });
      }
    } catch (err: any) {
      addMessage({
        sender: 'delta',
        text: `Delta tidak dapat terhubung. (${err.message})`,
      });
    } finally {
      finishExecution();
    }
  };

  const handleSend = async (text: string) => {
    if (connectionMode === 'cloud') {
      await executeSend(text);
      return;
    }

    try {
      const routerRes = await getRouterStatus();
      setIsRouterRunning(routerRes.running);
      if (!routerRes.running) {
        if (hapticEnabled) {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
        }
        setPendingText(text);
        setShowRouterModal(true);
        return;
      }
    } catch (_) {
      // If error checking router, proceed normally
    }

    await executeSend(text);
  };

  const handleStop = async () => {
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    }
    try {
      await cancelExecution();
    } catch (_) {}
    finishExecution();
  };

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]}
      edges={['top']}
    >
      <View style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header
          title="DELTA"
          onRouterWarningPress={() => setShowRouterModal(true)}
        />

        <View style={styles.listWrapper}>
          <MessageList
            messages={messages}
            activeSteps={Object.values(activeSteps)}
            isGenerating={isGenerating}
            activeStatusText={activeStatusText}
          />
        </View>

        <View style={styles.inputWrapper}>
          <ChatInput
            onSend={handleSend}
            onStop={handleStop}
            isGenerating={isGenerating}
          />
        </View>

        <RouterAlertModal
          visible={showRouterModal}
          onClose={() => {
            setShowRouterModal(false);
            setPendingText(null);
          }}
          onStartSuccess={() => {
            if (pendingText) {
              const toSend = pendingText;
              setPendingText(null);
              executeSend(toSend);
            }
          }}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  listWrapper: {
    flex: 1,
  },
  inputWrapper: {
    paddingBottom: 72, // Space above floating bottom bar
  },
});
