import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert, Clipboard } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { Header } from '../../src/components/common/Header';
import { PageTransition } from '../../src/components/common/PageTransition';
import { MessageList } from '../../src/components/chat/MessageList';
import { ChatInput } from '../../src/components/chat/ChatInput';
import { RouterAlertModal } from '../../src/components/chat/RouterAlertModal';
import { ChatSessionSidebar } from '../../src/components/chat/ChatSessionSidebar';
import { MessageActionSheet } from '../../src/components/chat/MessageActionSheet';
import { useChatStore } from '../../src/store/useChatStore';
import { useSettingsStore } from '../../src/store/useSettingsStore';
import { useConnectionStore } from '../../src/store/useConnectionStore';
import { useNotesStore } from '../../src/store/useNotesStore';
import { sendChatMessage, cancelExecution } from '../../src/services/api/chatApi';
import { getRouterStatus } from '../../src/services/api/systemApi';
import { useThemeColors } from '../../src/theme/theme';
import { ChatMessage } from '../../src/types/chat';

export default function ChatScreen() {
  const { colors } = useThemeColors();
  const {
    messages,
    activeSteps,
    isGenerating,
    activeStatusText,
    addMessage,
    deleteMessage,
    startExecution,
    finishExecution,
    loadSessions,
  } = useChatStore();
  const { createNote } = useNotesStore();
  const { hapticEnabled, connectionMode } = useSettingsStore();
  const { isRouterRunning, setIsRouterRunning } = useConnectionStore();
  const [showRouterModal, setShowRouterModal] = useState(false);
  const [showSessionSidebar, setShowSessionSidebar] = useState(false);
  const [selectedActionMessage, setSelectedActionMessage] = useState<ChatMessage | null>(null);
  const [pendingText, setPendingText] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, []);

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

  const handleCopyText = (text: string) => {
    Clipboard.setString(text);
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }
  };

  const handleSaveNoteFromAction = async (text: string, isUser: boolean) => {
    if (!text.trim()) return;
    const firstLine = text.split('\n')[0].replace(/[#*`_]/g, '').trim();
    const title = firstLine.length > 40 ? `${firstLine.slice(0, 37)}...` : firstLine || 'Saved Note';

    await createNote({
      title,
      content: text,
      tags: [isUser ? 'user-prompt' : 'delta-response'],
    });
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }
    Alert.alert('Tersimpan ke Catatan', `"${title}"`);
  };

  const handleQuoteMessage = (text: string) => {
    const quoteText = `> ${text.slice(0, 100).replace(/\n/g, '\n> ')}\n\n`;
    setPendingText(quoteText);
  };

  const handleDeleteMessage = (id: string) => {
    deleteMessage(id);
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
    }
  };

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]}
      edges={['top']}
    >
      <PageTransition style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <Header
          title="Delta"
          subtitle="AI Cybersecurity Intelligence"
          onRouterWarningPress={() => setShowRouterModal(true)}
          onTitlePress={() => {
            if (hapticEnabled) {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
            }
            setShowSessionSidebar(true);
          }}
        />

        <View style={styles.listWrapper}>
          <MessageList
            messages={messages}
            activeSteps={Object.values(activeSteps)}
            isGenerating={isGenerating}
            activeStatusText={activeStatusText}
            onCopyText={handleCopyText}
            onLongPressMessage={(msg) => setSelectedActionMessage(msg)}
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

        <ChatSessionSidebar
          visible={showSessionSidebar}
          onClose={() => setShowSessionSidebar(false)}
        />

        <MessageActionSheet
          visible={!!selectedActionMessage}
          message={selectedActionMessage}
          onClose={() => setSelectedActionMessage(null)}
          onCopy={handleCopyText}
          onSaveNote={handleSaveNoteFromAction}
          onQuote={handleQuoteMessage}
          onDelete={handleDeleteMessage}
        />
      </PageTransition>
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
