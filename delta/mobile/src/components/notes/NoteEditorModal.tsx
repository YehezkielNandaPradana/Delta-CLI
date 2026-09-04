import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  Modal,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { useNotesStore } from '../../store/useNotesStore';
import { Note, NoteAIAction } from '../../types/notes';
import { NoteActionSheet } from './NoteActionSheet';
import { CodeBlock } from '../chat/CodeBlock';
import { formatTimestamp } from '../../utils/formatters';

interface NoteEditorModalProps {
  visible: boolean;
  noteId: string | null;
  onClose: () => void;
  onAIAction: (action: NoteAIAction, note: Note) => void;
  onMoveFolder: (note: Note) => void;
}

export const NoteEditorModal: React.FC<NoteEditorModalProps> = ({
  visible,
  noteId,
  onClose,
  onAIAction,
  onMoveFolder,
}) => {
  const { colors } = useThemeColors();
  const { notes, updateNote, deleteNote, togglePin, duplicateNote } = useNotesStore();

  const note = notes.find((n) => n.id === noteId) || null;

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saveStatus, setSaveStatus] = useState<'saving' | 'saved' | 'idle'>('saved');
  const [actionSheetVisible, setActionSheetVisible] = useState(false);
  const [previewMarkdown, setPreviewMarkdown] = useState(true);

  const debounceTimer = useRef<any>(null);

  useEffect(() => {
    if (note) {
      setTitle(note.title);
      setContent(note.content);
      setSaveStatus('saved');
      // Otomatis aktifkan Rich Canvas Preview jika catatan memiliki struktur markdown / kode
      const hasMarkdownOrCode =
        note.content &&
        (note.content.includes('#') ||
          note.content.includes('```') ||
          note.content.includes('`') ||
          note.content.includes('- ') ||
          note.content.includes('* '));
      setPreviewMarkdown(!!hasMarkdownOrCode);
    } else {
      setTitle('');
      setContent('');
      setPreviewMarkdown(false);
    }
  }, [noteId]);

  const triggerAutoSave = (newTitle: string, newContent: string) => {
    if (!noteId) return;
    setSaveStatus('saving');

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(async () => {
      await updateNote(noteId, {
        title: newTitle.trim() || 'Untitled Note',
        content: newContent,
      });
      setSaveStatus('saved');
    }, 400);
  };

  const handleTitleChange = (val: string) => {
    setTitle(val);
    triggerAutoSave(val, content);
  };

  const handleContentChange = (val: string) => {
    setContent(val);
    triggerAutoSave(title, val);
  };

  const handleClose = async () => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    if (noteId && saveStatus === 'saving') {
      await updateNote(noteId, {
        title: title.trim() || 'Untitled Note',
        content,
      });
    }
    onClose();
  };

  const renderFormattedLine = (text: string, keyPrefix: string) => {
    // Check for inline code snippet `...`
    const parts = text.split(/(`[^`]+`)/g);
    if (parts.length === 1) {
      return (
        <Text style={[styles.mdText, { color: colors.textPrimary }]}>
          {text}
        </Text>
      );
    }

    return (
      <Text style={[styles.mdText, { color: colors.textPrimary }]}>
        {parts.map((part, pIdx) => {
          if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
            const codeVal = part.slice(1, -1);
            return (
              <Text
                key={`${keyPrefix}_code_${pIdx}`}
                style={[
                  styles.inlineCode,
                  {
                    backgroundColor: colors.surfaceHover,
                    color: colors.accent,
                    borderColor: colors.border,
                  },
                ]}
              >
                {` ${codeVal} `}
              </Text>
            );
          }
          return (
            <Text key={`${keyPrefix}_txt_${pIdx}`} style={{ color: colors.textPrimary }}>
              {part}
            </Text>
          );
        })}
      </Text>
    );
  };

  const renderSimpleMarkdown = (text: string) => {
    // Check for code blocks ```...```
    const parts = text.split(/(```[\s\S]*?```)/g);

    return parts.map((part, pIdx) => {
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
        return <CodeBlock key={`cb_${pIdx}`} code={code} language={language} />;
      }

      const lines = part.split('\n');
      return lines.map((line, idx) => {
        const trimmed = line.trim();

        if (trimmed.startsWith('# ')) {
          return (
            <View key={`h1_${pIdx}_${idx}`} style={[styles.mdH1Container, { borderBottomColor: colors.border }]}>
              <Text style={[styles.mdH1, { color: colors.textPrimary }]}>
                {trimmed.slice(2)}
              </Text>
            </View>
          );
        }
        if (trimmed.startsWith('## ')) {
          return (
            <View key={`h2_${pIdx}_${idx}`} style={styles.mdH2Container}>
              <Text style={[styles.mdH2, { color: colors.textPrimary }]}>
                {trimmed.slice(3)}
              </Text>
            </View>
          );
        }
        if (trimmed.startsWith('### ')) {
          return (
            <View key={`h3_${pIdx}_${idx}`} style={styles.mdH3Container}>
              <Text style={[styles.mdH3, { color: colors.textSecondary }]}>
                {trimmed.slice(4)}
              </Text>
            </View>
          );
        }
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <View key={`li_${pIdx}_${idx}`} style={styles.mdListRow}>
              <Text style={[styles.mdBullet, { color: colors.accent }]}>•</Text>
              <View style={{ flex: 1 }}>
                {renderFormattedLine(trimmed.slice(2), `item_${pIdx}_${idx}`)}
              </View>
            </View>
          );
        }
        if (trimmed.startsWith('[ ] ') || trimmed.startsWith('- [ ] ')) {
          return (
            <View key={`chk_${pIdx}_${idx}`} style={styles.mdListRow}>
              <Ionicons name="square-outline" size={15} color={colors.accent} style={{ marginTop: 2 }} />
              <View style={{ flex: 1 }}>
                {renderFormattedLine(trimmed.replace(/^(\[ \]|-\s*\[ \])\s*/, ''), `check_${pIdx}_${idx}`)}
              </View>
            </View>
          );
        }
        if (trimmed.startsWith('[x] ') || trimmed.startsWith('- [x] ')) {
          return (
            <View key={`chkd_${pIdx}_${idx}`} style={styles.mdListRow}>
              <Ionicons name="checkbox" size={15} color={colors.success} style={{ marginTop: 2 }} />
              <View style={{ flex: 1 }}>
                {renderFormattedLine(trimmed.replace(/^(\[x\]|-\s*\[x\])\s*/, ''), `checked_${pIdx}_${idx}`)}
              </View>
            </View>
          );
        }
        if (!trimmed) {
          return <View key={`emp_${pIdx}_${idx}`} style={styles.emptyLine} />;
        }
        return (
          <View key={`p_${pIdx}_${idx}`} style={styles.mdParagraph}>
            {renderFormattedLine(trimmed, `p_${pIdx}_${idx}`)}
          </View>
        );
      });
    });
  };

  if (!note && visible) return null;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={handleClose}>
      <SafeAreaView style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          {/* Top Bar Navigation */}
          <View
            style={[
              styles.topBar,
              {
                backgroundColor: colors.bgSecondary,
                borderBottomColor: colors.border,
              },
            ]}
          >
            <TouchableOpacity onPress={handleClose} style={styles.backBtn} activeOpacity={0.7}>
              <Ionicons name="chevron-back" size={20} color={colors.accent} />
              <Text style={[styles.backText, { color: colors.accent }]}>Notes</Text>
            </TouchableOpacity>

            {/* Save Status Badge */}
            <View style={styles.statusContainer}>
              {saveStatus === 'saving' ? (
                <View style={styles.statusRow}>
                  <ActivityIndicator size="small" color={colors.accent} />
                  <Text style={[styles.statusText, { color: colors.accent }]}>Saving...</Text>
                </View>
              ) : (
                <View style={styles.statusRow}>
                  <Ionicons name="checkmark-circle" size={13} color={colors.success} />
                  <Text style={[styles.statusText, { color: colors.textMuted }]}>Saved</Text>
                </View>
              )}
            </View>

            {/* Action Buttons Right */}
            <View style={styles.topActions}>
              <TouchableOpacity
                onPress={() => setPreviewMarkdown(!previewMarkdown)}
                style={[
                  styles.iconButton,
                  {
                    backgroundColor: previewMarkdown ? colors.surfaceHover : colors.bgSurface,
                    borderColor: previewMarkdown ? colors.borderStrong : colors.border,
                  },
                ]}
                activeOpacity={0.7}
              >
                <Ionicons
                  name={previewMarkdown ? 'create-outline' : 'eye-outline'}
                  size={16}
                  color={previewMarkdown ? colors.accent : colors.textSecondary}
                />
              </TouchableOpacity>

              <TouchableOpacity
                onPress={() => setActionSheetVisible(true)}
                style={[styles.iconButton, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}
                activeOpacity={0.7}
              >
                <Ionicons name="sparkles" size={15} color={colors.accent} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Editor Body */}
          <ScrollView
            style={styles.editorScroll}
            contentContainerStyle={styles.editorContent}
            keyboardShouldPersistTaps="handled"
          >
            {/* Title Input */}
            <TextInput
              value={title}
              onChangeText={handleTitleChange}
              placeholder="Title"
              placeholderTextColor={colors.textMuted}
              style={[
                styles.titleInput,
                { color: colors.textPrimary },
              ]}
              multiline={false}
              returnKeyType="next"
            />

            {/* Note Meta / Last Updated */}
            {note && (
              <Text style={[styles.updatedText, { color: colors.textMuted }]}>
                Last edited {formatTimestamp(note.updatedAt)}
              </Text>
            )}

            {/* Content Input or Markdown Preview */}
            {previewMarkdown ? (
              <View style={styles.previewContainer}>
                {renderSimpleMarkdown(content)}
              </View>
            ) : (
              <TextInput
                value={content}
                onChangeText={handleContentChange}
                placeholder="Start typing your technical notes, commands, ideas..."
                placeholderTextColor={colors.textMuted}
                style={[
                  styles.contentInput,
                  { color: colors.textPrimary },
                ]}
                multiline
                textAlignVertical="top"
                autoCapitalize="sentences"
                scrollEnabled={false}
              />
            )}
          </ScrollView>
        </KeyboardAvoidingView>

        {/* AI & Note Action Sheet */}
        {note && (
          <NoteActionSheet
            visible={actionSheetVisible}
            note={note}
            onClose={() => setActionSheetVisible(false)}
            onAIAction={(action) => onAIAction(action, note)}
            onTogglePin={() => togglePin(note.id)}
            onMoveFolder={() => onMoveFolder(note)}
            onDuplicate={() => duplicateNote(note.id)}
            onDelete={() => {
              deleteNote(note.id);
              onClose();
            }}
          />
        )}
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
  },
  backBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
    paddingRight: 6,
  },
  backText: {
    fontSize: 15,
    fontWeight: '600',
    marginLeft: -2,
  },
  statusContainer: {
    flex: 1,
    alignItems: 'center',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statusText: {
    fontSize: 11.5,
    fontWeight: '500',
  },
  topActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  iconButton: {
    width: 34,
    height: 34,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  editorScroll: {
    flex: 1,
  },
  editorContent: {
    padding: 16,
    paddingBottom: 90,
  },
  titleInput: {
    fontSize: 20,
    fontWeight: '700',
    letterSpacing: -0.2,
    marginBottom: 4,
    paddingVertical: 0,
  },
  updatedText: {
    fontSize: 11,
    fontWeight: '400',
    marginBottom: 14,
  },
  contentInput: {
    fontSize: 14.5,
    lineHeight: 24,
    minHeight: 300,
    paddingVertical: 0,
  },
  previewContainer: {
    paddingTop: 4,
  },
  mdH1Container: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    paddingBottom: 6,
    marginTop: 14,
    marginBottom: 8,
  },
  mdH1: {
    fontSize: 20,
    fontWeight: '800',
    letterSpacing: -0.4,
  },
  mdH2Container: {
    marginTop: 14,
    marginBottom: 6,
  },
  mdH2: {
    fontSize: 16.5,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
  mdH3Container: {
    marginTop: 10,
    marginBottom: 4,
  },
  mdH3: {
    fontSize: 14.5,
    fontWeight: '600',
  },
  mdParagraph: {
    marginVertical: 3,
  },
  mdText: {
    fontSize: 14.5,
    lineHeight: 22,
  },
  inlineCode: {
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontSize: 12.5,
    fontWeight: '600',
    borderRadius: 4,
    overflow: 'hidden',
  },
  mdListRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginVertical: 3.5,
    paddingLeft: 2,
  },
  mdBullet: {
    fontSize: 14,
    fontWeight: '800',
    marginTop: 1,
  },
  emptyLine: {
    height: 8,
  },
});
