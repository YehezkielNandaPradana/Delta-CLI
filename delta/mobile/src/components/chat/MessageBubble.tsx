import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Platform,
  TouchableOpacity,
  Alert,
  Animated,
  Easing,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { ChatMessage } from '../../types/chat';
import { CodeBlock } from './CodeBlock';
import { AgentActivity } from '../agent/AgentActivity';
import { formatTimestamp, cleanAnsiCodes } from '../../utils/formatters';
import { useNotesStore } from '../../store/useNotesStore';

interface MessageBubbleProps {
  message: ChatMessage;
  onCopyText?: (text: string) => void;
  onLongPressMessage?: (msg: ChatMessage) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onCopyText,
  onLongPressMessage,
}) => {
  const { colors, isDark } = useThemeColors();
  const { createNote } = useNotesStore();
  const [savedAsNote, setSavedAsNote] = useState(false);

  const isUser = message.sender === 'user';
  const cleanText = cleanAnsiCodes(message.text || '');

  // Subtle clean entrance transition
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(8)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 220,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 220,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleLongPress = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    if (onLongPressMessage) {
      onLongPressMessage(message);
    }
  };

  const handleSaveAsNote = async () => {
    if (!cleanText.trim()) return;

    const firstLine = cleanText.split('\n')[0].replace(/[#*`_]/g, '').trim();
    const title = firstLine.length > 40 ? `${firstLine.slice(0, 37)}...` : firstLine || 'Saved Note';

    await createNote({
      title,
      content: cleanText,
      tags: [isUser ? 'user-prompt' : 'delta-response'],
    });

    setSavedAsNote(true);
    Alert.alert('Saved to Notes', `"${title}"`);
  };

  const renderContent = (content: string) => {
    const parts = content.split(/(```[\s\S]*?```)/g);

    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const lines = part.slice(3, -3).trim().split('\n');
        let language = '';
        let code = '';
        if (lines[0] && !lines[0].includes(' ') && lines.length > 1) {
          language = lines[0].trim();
          code = lines.slice(1).join('\n');
        } else {
          code = lines.join('\n');
        }
        return <CodeBlock key={index} code={code} language={language} onCopy={onCopyText} />;
      }

      return (
        <Text
          key={index}
          style={[
            styles.messageText,
            {
              color: isUser ? '#FFFFFF' : colors.textPrimary,
            },
          ]}
        >
          {part}
        </Text>
      );
    });
  };

  // Clean solid monochrome palette
  const userBg = isDark ? '#333842' : '#262930';
  const deltaBg = isDark ? '#14171C' : '#F4F5F7';
  const deltaBorder = isDark ? '#23272F' : '#E2E5EA';

  return (
    <Animated.View
      style={[
        styles.wrapper,
        isUser ? styles.userWrapper : styles.deltaWrapper,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {!isUser && message.steps && message.steps.length > 0 && (
        <View style={styles.activityContainer}>
          <AgentActivity steps={message.steps} isRunning={message.isStreaming} />
        </View>
      )}

      <TouchableOpacity
        onLongPress={handleLongPress}
        delayLongPress={280}
        activeOpacity={0.88}
        style={[
          styles.bubble,
          isUser
            ? [styles.userBubble, { backgroundColor: userBg }]
            : [
                styles.deltaBubble,
                {
                  backgroundColor: deltaBg,
                  borderColor: deltaBorder,
                },
              ],
        ]}
      >
        {/* Clean Message Body */}
        <View style={styles.body}>{renderContent(cleanText)}</View>

        {/* Minimal Meta Row (Time & Note Action) */}
        <View style={styles.metaRow}>
          <Text
            style={[
              styles.timestamp,
              { color: isUser ? 'rgba(255, 255, 255, 0.65)' : colors.textMuted },
            ]}
          >
            {formatTimestamp(message.timestamp)}
          </Text>

          <TouchableOpacity
            onPress={handleSaveAsNote}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={styles.actionIcon}
            activeOpacity={0.6}
            accessibilityLabel="Save as note"
          >
            <Ionicons
              name={savedAsNote ? 'bookmark' : 'bookmark-outline'}
              size={13}
              color={
                isUser
                  ? 'rgba(255, 255, 255, 0.8)'
                  : savedAsNote
                  ? colors.accent
                  : colors.textMuted
              }
            />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    marginVertical: 4,
    paddingHorizontal: 16,
    width: '100%',
  },
  userWrapper: {
    alignItems: 'flex-end',
  },
  deltaWrapper: {
    alignItems: 'flex-start',
  },
  activityContainer: {
    width: '100%',
    maxWidth: '92%',
    marginBottom: 4,
  },
  bubble: {
    paddingHorizontal: 14,
    paddingTop: 10,
    paddingBottom: 8,
    maxWidth: '86%',
    borderRadius: 16,
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.06,
        shadowRadius: 3,
      },
      android: {
        elevation: 1,
      },
    }),
  },
  userBubble: {
    borderBottomRightRadius: 3,
  },
  deltaBubble: {
    borderWidth: 1,
    borderBottomLeftRadius: 3,
  },
  body: {
    marginBottom: 2,
  },
  messageText: {
    fontSize: 14.5,
    lineHeight: 21,
    letterSpacing: 0.1,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 8,
    marginTop: 4,
  },
  timestamp: {
    fontSize: 10,
    fontWeight: '400',
  },
  actionIcon: {
    padding: 2,
  },
});
