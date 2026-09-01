import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { useThemeColors } from '../../theme/theme';
import { ChatMessage } from '../../types/chat';
import { CodeBlock } from './CodeBlock';
import { AgentActivity } from '../agent/AgentActivity';
import { formatTimestamp, cleanAnsiCodes } from '../../utils/formatters';

interface MessageBubbleProps {
  message: ChatMessage;
  onCopyText?: (text: string) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onCopyText }) => {
  const { colors, isDark } = useThemeColors();
  const isUser = message.sender === 'user';
  const cleanText = cleanAnsiCodes(message.text || '');

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
            { color: isUser ? '#ffffff' : colors.textPrimary },
          ]}
        >
          {part}
        </Text>
      );
    });
  };

  return (
    <View style={[styles.wrapper, isUser ? styles.userWrapper : styles.deltaWrapper]}>
      {!isUser && message.steps && message.steps.length > 0 && (
        <View style={styles.activityContainer}>
          <AgentActivity steps={message.steps} isRunning={message.isStreaming} />
        </View>
      )}

      <View
        style={[
          styles.bubble,
          isUser
            ? [
                styles.userBubble,
                {
                  backgroundColor: colors.accentGreen,
                  borderColor: isDark ? 'rgba(0, 245, 155, 0.4)' : 'rgba(5, 150, 105, 0.4)',
                },
              ]
            : [
                styles.deltaBubble,
                {
                  backgroundColor: colors.cardBg,
                  borderColor: colors.cardBorder,
                  borderTopColor: colors.cardSpecular,
                  borderTopWidth: 1.5,
                  shadowColor: isDark ? '#000000' : '#64748b',
                },
              ],
        ]}
      >
        <View style={styles.headerRow}>
          <View style={styles.senderBadge}>
            <Text
              style={[
                styles.senderLabel,
                { color: isUser ? '#ffffff' : colors.accentGreen },
              ]}
            >
              {isUser ? 'USER' : 'DELTA'}
            </Text>
          </View>
          <Text
            style={[
              styles.timestamp,
              { color: isUser ? 'rgba(255, 255, 255, 0.8)' : colors.textMuted },
            ]}
          >
            {formatTimestamp(message.timestamp)}
          </Text>
        </View>

        <View style={styles.body}>{renderContent(cleanText)}</View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    marginVertical: 6,
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
    marginBottom: 6,
  },
  bubble: {
    borderRadius: 18,
    padding: 14,
    maxWidth: '88%',
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  userBubble: {
    borderBottomRightRadius: 4,
  },
  deltaBubble: {
    borderBottomLeftRadius: 4,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  senderBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  senderLabel: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  timestamp: {
    fontSize: 10,
    marginLeft: 8,
    fontWeight: '500',
  },
  body: {
    marginTop: 2,
  },
  messageText: {
    fontSize: 14.5,
    lineHeight: 22,
    letterSpacing: 0.2,
  },
});
