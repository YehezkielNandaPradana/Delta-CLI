import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';

interface CodeBlockProps {
  code: string;
  language?: string;
  onCopy?: (text: string) => void;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code, language = '', onCopy }) => {
  const { colors } = useThemeColors();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (onCopy) {
      onCopy(code);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: colors.codeBg,
          borderColor: colors.codeBorder,
        },
      ]}
    >
      <View
        style={[
          styles.header,
          {
            backgroundColor: colors.bgSecondary,
            borderBottomColor: colors.codeBorder,
          },
        ]}
      >
        <View
          style={[
            styles.langBadge,
            { backgroundColor: colors.accentCyanSubtle },
          ]}
        >
          <Text style={[styles.langText, { color: colors.accentCyan }]}>
            {language ? language.toUpperCase() : 'CODE'}
          </Text>
        </View>
        <TouchableOpacity
          style={[
            styles.copyBtn,
            { backgroundColor: colors.bgSurface },
          ]}
          onPress={handleCopy}
          activeOpacity={0.7}
          accessibilityLabel="Copy code"
          accessibilityRole="button"
        >
          <Feather
            name={copied ? 'check' : 'copy'}
            size={12}
            color={copied ? colors.accentGreen : colors.textMuted}
          />
          <Text
            style={[
              styles.copyText,
              { color: copied ? colors.accentGreen : colors.textMuted },
            ]}
          >
            {copied ? 'Copied' : 'Copy'}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.codeContainer}>
        <Text
          style={[
            styles.codeText,
            { color: colors.textPrimary },
          ]}
          selectable
        >
          {code}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: 1,
    marginVertical: 8,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderBottomWidth: 1,
  },
  langBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  langText: {
    fontSize: 10,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    letterSpacing: 0.5,
  },
  copyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  copyText: {
    fontSize: 11,
    marginLeft: 4,
    fontWeight: '500',
  },
  codeContainer: {
    padding: 12,
  },
  codeText: {
    fontSize: 12.5,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 19,
  },
});
