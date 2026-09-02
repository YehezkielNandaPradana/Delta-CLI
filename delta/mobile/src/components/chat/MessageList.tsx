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
  TouchableOpacity,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
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
  onLongPressMessage?: (msg: ChatMessage) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  activeSteps = [],
  isGenerating = false,
  activeStatusText = 'Working',
  onCopyText,
  onLongPressMessage,
}) => {
  const { colors, isDark } = useThemeColors();
  const flatListRef = useRef<FlatList>(null);

  const scrollY = useRef(new Animated.Value(0)).current;
  const [contentHeight, setContentHeight] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const scrollBtnAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (messages.length > 0 && !showScrollBottom) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length, messages[messages.length - 1]?.text, isGenerating]);

  const handleScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { layoutMeasurement, contentOffset, contentSize } = e.nativeEvent;
    const distanceFromBottom = contentSize.height - layoutMeasurement.height - contentOffset.y;

    // Show button when user scrolls up by > 180px
    const shouldShow = distanceFromBottom > 180;
    if (shouldShow !== showScrollBottom) {
      setShowScrollBottom(shouldShow);
      Animated.spring(scrollBtnAnim, {
        toValue: shouldShow ? 1 : 0,
        damping: 18,
        stiffness: 240,
        useNativeDriver: true,
      }).start();
    }
  };

  const scrollToBottom = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    flatListRef.current?.scrollToEnd({ animated: true });
  };

  const handleLayout = (e: LayoutChangeEvent) => {
    setContainerHeight(e.nativeEvent.layout.height);
  };

  const handleContentSizeChange = (_: number, h: number) => {
    setContentHeight(h);
    if (!showScrollBottom && (isGenerating || messages.length > 0)) {
      flatListRef.current?.scrollToEnd({ animated: true });
    }
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
        renderItem={({ item }) => (
          <MessageBubble
            message={item}
            onCopyText={onCopyText}
            onLongPressMessage={onLongPressMessage}
          />
        )}
        contentContainerStyle={[styles.listContent, messages.length === 0 ? styles.emptyList : null]}
        ListEmptyComponent={renderEmptyState}
        showsVerticalScrollIndicator={false}
        onScroll={handleScroll}
        scrollEventThrottle={16}
        onContentSizeChange={handleContentSizeChange}
        ListFooterComponent={
          isGenerating ? (
            <View style={styles.footerContainer}>
              <ThinkingIndicator
                statusText={activeStatusText || 'Delta is thinking...'}
                steps={activeSteps}
              />
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

      {/* iOS Style Floating Scroll-To-Bottom Button */}
      {showScrollBottom && (
        <Animated.View
          style={[
            styles.scrollBottomWrapper,
            {
              opacity: scrollBtnAnim,
              transform: [
                {
                  scale: scrollBtnAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.6, 1],
                  }),
                },
                {
                  translateY: scrollBtnAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [20, 0],
                  }),
                },
              ],
            },
          ]}
        >
          <TouchableOpacity
            onPress={scrollToBottom}
            style={[
              styles.scrollBottomBtn,
              {
                backgroundColor: isDark ? 'rgba(30, 30, 30, 0.90)' : 'rgba(255, 255, 255, 0.92)',
                borderColor: colors.border,
              },
            ]}
            activeOpacity={0.8}
            accessibilityLabel="Scroll ke paling bawah"
          >
            <Ionicons name="chevron-down" size={18} color={colors.textPrimary} />
          </TouchableOpacity>
        </Animated.View>
      )}
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
  scrollBottomWrapper: {
    position: 'absolute',
    bottom: 12,
    alignSelf: 'center',
    zIndex: 10,
  },
  scrollBottomBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.18,
        shadowRadius: 8,
      },
      android: {
        elevation: 6,
      },
    }),
  },
});
