import React, { useRef, useEffect, useState } from 'react';
import {
  FlatList,
  StyleSheet,
  View,
  Text,
  Animated,
  NativeSyntheticEvent,
  NativeScrollEvent,
  LayoutChangeEvent,
} from 'react-native';
import { ChatMessage } from '../../types/chat';
import { MessageBubble } from './MessageBubble';
import { ThinkingIndicator } from './ThinkingIndicator';
import { useThemeColors } from '../../theme/theme';
import { AgentActivity } from '../agent/AgentActivity';
import { AgentStep } from '../../types/events';
import { CyberScrollbar } from '../common/CyberScrollbar';

interface MessageListProps {
  messages: ChatMessage[];
  activeSteps?: AgentStep[];
  isGenerating?: boolean;
  activeStatusText?: string;
  onCopyText?: (text: string) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  activeSteps = [],
  isGenerating = false,
  activeStatusText = 'Working',
  onCopyText,
}) => {
  const { colors, isDark } = useThemeColors();
  const flatListRef = useRef<FlatList>(null);

  const scrollY = useRef(new Animated.Value(0)).current;
  const [contentHeight, setContentHeight] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length, messages[messages.length - 1]?.text, isGenerating]);

  const handleScroll = Animated.event(
    [{ nativeEvent: { contentOffset: { y: scrollY } } }],
    { useNativeDriver: false }
  );

  const handleLayout = (e: LayoutChangeEvent) => {
    setContainerHeight(e.nativeEvent.layout.height);
  };

  const handleContentSizeChange = (_: number, h: number) => {
    setContentHeight(h);
  };

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <View
        style={[
          styles.emptyIconBadge,
          {
            backgroundColor: colors.accentGreenSubtle,
            borderColor: colors.accentGreenGlow,
            borderTopColor: colors.cardSpecular,
            borderTopWidth: 1.5,
            shadowColor: isDark ? '#000000' : '#475569',
          },
        ]}
      >
        <Text style={[styles.emptyLogo, { color: colors.accentGreen }]}>Δ</Text>
      </View>
      <Text style={[styles.emptyTitle, { color: colors.textPrimary }]}>DELTA AI</Text>
      <Text style={[styles.emptyRole, { color: colors.accentCyan }]}>
        Autonomous Security & Intelligence
      </Text>
      <Text style={[styles.emptySubtitle, { color: colors.textMuted }]}>
        Chat, inspect runtime telemetry, and orchestrate security operations with Delta agent.
      </Text>
    </View>
  );

  return (
    <View style={styles.wrapper} onLayout={handleLayout}>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <MessageBubble message={item} onCopyText={onCopyText} />}
        contentContainerStyle={[styles.listContent, messages.length === 0 ? styles.emptyList : null]}
        ListEmptyComponent={renderEmptyState}
        showsVerticalScrollIndicator={false}
        onScroll={handleScroll}
        scrollEventThrottle={16}
        onContentSizeChange={handleContentSizeChange}
        ListFooterComponent={
          isGenerating ? (
            <View style={styles.footerContainer}>
              <ThinkingIndicator statusText={activeStatusText || 'Delta is thinking...'} />
              {activeSteps.length > 0 && (
                <View style={styles.footerActivity}>
                  <AgentActivity
                    steps={activeSteps}
                    isRunning={isGenerating}
                    activeStatusText={activeStatusText}
                  />
                </View>
              )}
            </View>
          ) : null
        }
      />

      {/* Futuristic Cyber Glowing Scrollbar */}
      <CyberScrollbar
        contentHeight={contentHeight}
        containerHeight={containerHeight}
        scrollY={scrollY}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    position: 'relative',
  },
  listContent: {
    paddingVertical: 16,
    paddingBottom: 90,
    flexGrow: 1,
  },
  emptyList: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingHorizontal: 36,
    marginVertical: 'auto',
  },
  emptyIconBadge: {
    width: 68,
    height: 68,
    borderRadius: 20,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  emptyLogo: {
    fontSize: 32,
    fontWeight: '900',
    fontFamily: 'monospace',
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '900',
    letterSpacing: 2,
    marginBottom: 4,
    fontFamily: 'monospace',
  },
  emptyRole: {
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 10,
    letterSpacing: 0.8,
    fontFamily: 'monospace',
    textTransform: 'uppercase',
  },
  emptySubtitle: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 320,
  },
  footerContainer: {
    marginBottom: 8,
  },
  footerActivity: {
    paddingHorizontal: 16,
    marginTop: 4,
  },
});
