import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Clipboard,
  Platform,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { useSettingsStore } from '../../store/useSettingsStore';

interface CodeBlockProps {
  code: string;
  language?: string;
  onCopy?: (text: string) => void;
}

// One Dark Pro Syntax Highlighting Colors
const ONE_DARK_COLORS = {
  keyword: '#C678DD', // purple (function, const, if, return, import, def)
  string: '#98C379',  // light green ("text", 'text')
  number: '#D19A66',  // orange (123, 0.5)
  function: '#61AFEF',// blue (methodName, call())
  comment: '#7F848E', // gray italic (// comment, # comment)
  operator: '#56B6C2',// cyan (=, +, =>, :, $)
  defaultDark: '#ABB2BF', // light gray
  defaultLight: '#24292E',
};

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, language = '', onCopy }) => {
  const { colors, isDark } = useThemeColors();
  const { hapticEnabled } = useSettingsStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (hapticEnabled) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }
    Clipboard.setString(code);
    if (onCopy) {
      onCopy(code);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  /**
   * One Dark Pro Syntax Tokenizer
   */
  const renderHighlightedLine = (line: string, lineIdx: number) => {
    // Comment line check
    const trimmed = line.trim();
    if (trimmed.startsWith('//') || trimmed.startsWith('#') || trimmed.startsWith('/*') || trimmed.startsWith('*')) {
      return (
        <Text key={lineIdx} style={[styles.codeText, { color: ONE_DARK_COLORS.comment, fontStyle: 'italic' }]}>
          {line || ' '}
        </Text>
      );
    }

    // Tokenizer regex
    const tokenRegex = /(\/\/.*$|#.*$|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\b(?:const|let|var|function|return|import|export|from|class|extends|if|else|switch|case|break|for|while|try|catch|finally|async|await|def|public|private|protected|namespace|use|self|this|php|artisan)\b|\b\d+(?:\.\d+)?\b|\b[a-zA-Z_]\w*(?=\()|[=><!+\-*/%&|:;]+|[a-zA-Z_]\w*|\s+|.)/g;

    const tokens: React.ReactNode[] = [];
    let match: RegExpExecArray | null;
    let tIdx = 0;

    while ((match = tokenRegex.exec(line)) !== null) {
      const token = match[0];
      let tokenColor = isDark ? ONE_DARK_COLORS.defaultDark : ONE_DARK_COLORS.defaultLight;

      if (token.startsWith('//') || token.startsWith('#')) {
        tokenColor = ONE_DARK_COLORS.comment;
      } else if (token.startsWith('"') || token.startsWith("'") || token.startsWith('`')) {
        tokenColor = ONE_DARK_COLORS.string;
      } else if (
        /^(const|let|var|function|return|import|export|from|class|extends|if|else|switch|case|break|for|while|try|catch|finally|async|await|def|public|private|protected|namespace|use|self|this|php|artisan)$/.test(
          token
        )
      ) {
        tokenColor = ONE_DARK_COLORS.keyword;
      } else if (/^\d+(\.\d+)?$/.test(token)) {
        tokenColor = ONE_DARK_COLORS.number;
      } else if (/^[a-zA-Z_]\w*$/.test(token) && line[match.index + token.length] === '(') {
        tokenColor = ONE_DARK_COLORS.function;
      } else if (/^[=><!+\-*/%&|:]+$/.test(token)) {
        tokenColor = ONE_DARK_COLORS.operator;
      }

      tokens.push(
        <Text key={`t_${lineIdx}_${tIdx++}`} style={{ color: tokenColor }}>
          {token}
        </Text>
      );
    }

    return (
      <Text key={lineIdx} style={styles.codeText}>
        {tokens.length > 0 ? tokens : line || ' '}
      </Text>
    );
  };

  const lines = code.split('\n');

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: isDark ? '#181A1F' : '#F5F6F8',
          borderColor: colors.border,
        },
      ]}
    >
      {/* MacOS Style Window Header */}
      <View
        style={[
          styles.header,
          {
            backgroundColor: isDark ? '#14161B' : '#EAECEF',
            borderBottomColor: colors.border,
          },
        ]}
      >
        {/* Left: MacOS Traffic Light Dots */}
        <View style={styles.macControlsRow}>
          <View style={[styles.macDot, { backgroundColor: '#FF5F56' }]} />
          <View style={[styles.macDot, { backgroundColor: '#FFBD2E' }]} />
          <View style={[styles.macDot, { backgroundColor: '#27C93F' }]} />

          {/* Language Tag */}
          <Text style={[styles.langLabel, { color: colors.textSecondary }]}>
            {language ? language.toUpperCase() : 'CODE'}
          </Text>
        </View>

        {/* Right: Quick 1-Tap Copy Button */}
        <TouchableOpacity
          style={[
            styles.copyBtn,
            {
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
            },
          ]}
          onPress={handleCopy}
          activeOpacity={0.7}
          accessibilityLabel="Copy code"
          accessibilityRole="button"
        >
          <Feather
            name={copied ? 'check' : 'copy'}
            size={11}
            color={copied ? '#98C379' : colors.textSecondary}
          />
          <Text
            style={[
              styles.copyText,
              { color: copied ? '#98C379' : colors.textSecondary },
            ]}
          >
            {copied ? 'Copied' : 'Copy'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Code Canvas Body with Horizontal Scroll */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.canvasContent}
      >
        <View style={styles.codeLinesWrapper}>
          {lines.map((l, idx) => renderHighlightedLine(l, idx))}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    borderWidth: 1,
    marginVertical: 8,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.15,
        shadowRadius: 8,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  macControlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  macDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  langLabel: {
    fontSize: 10.5,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginLeft: 8,
    letterSpacing: 0.5,
  },
  copyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3.5,
    borderRadius: 6,
    gap: 4,
  },
  copyText: {
    fontSize: 10.5,
    fontWeight: '600',
  },
  canvasContent: {
    padding: 12,
    minWidth: '100%',
  },
  codeLinesWrapper: {
    flexDirection: 'column',
  },
  codeText: {
    fontSize: 12.5,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 19,
    letterSpacing: -0.2,
  },
});
