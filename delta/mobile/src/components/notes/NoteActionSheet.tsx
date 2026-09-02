import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  TouchableWithoutFeedback,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { NoteAIAction, Note } from '../../types/notes';

interface NoteActionSheetProps {
  visible: boolean;
  note: Note | null;
  onClose: () => void;
  onAIAction: (action: NoteAIAction) => void;
  onTogglePin: () => void;
  onMoveFolder: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}

export const NoteActionSheet: React.FC<NoteActionSheetProps> = ({
  visible,
  note,
  onClose,
  onAIAction,
  onTogglePin,
  onMoveFolder,
  onDuplicate,
  onDelete,
}) => {
  const { colors } = useThemeColors();
  if (!note) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.overlay}>
          <TouchableWithoutFeedback>
            <View
              style={[
                styles.sheet,
                {
                  backgroundColor: colors.surfaceElevated,
                  borderColor: colors.border,
                },
              ]}
            >
              <View style={[styles.dragHandle, { backgroundColor: colors.border }]} />

              <View style={[styles.noteHeaderSnippet, { borderBottomColor: colors.border }]}>
                <Text style={[styles.noteTitle, { color: colors.textPrimary }]} numberOfLines={1}>
                  {note.title || 'Untitled Note'}
                </Text>
              </View>

              <ScrollView style={{ maxHeight: 380 }} showsVerticalScrollIndicator={false}>
                {/* AI Section Header */}
                <Text style={[styles.sectionLabel, { color: colors.accent }]}>
                  DELTA AGENT ACTIONS
                </Text>

                <View style={styles.actionsGrid}>
                  <TouchableOpacity
                    onPress={() => {
                      onClose();
                      onAIAction('ask');
                    }}
                    style={[styles.actionBtn, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}
                  >
                    <Ionicons name="chatbubble-ellipses-outline" size={16} color={colors.accent} />
                    <Text style={[styles.actionBtnText, { color: colors.textPrimary }]}>Ask Delta</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={() => {
                      onClose();
                      onAIAction('summarize');
                    }}
                    style={[styles.actionBtn, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}
                  >
                    <Ionicons name="document-text-outline" size={16} color={colors.textSecondary} />
                    <Text style={[styles.actionBtnText, { color: colors.textPrimary }]}>Summarize</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={() => {
                      onClose();
                      onAIAction('improve');
                    }}
                    style={[styles.actionBtn, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}
                  >
                    <Ionicons name="color-wand-outline" size={16} color={colors.textSecondary} />
                    <Text style={[styles.actionBtnText, { color: colors.textPrimary }]}>Improve</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={() => {
                      onClose();
                      onAIAction('expand');
                    }}
                    style={[styles.actionBtn, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}
                  >
                    <Ionicons name="git-branch-outline" size={16} color={colors.textSecondary} />
                    <Text style={[styles.actionBtnText, { color: colors.textPrimary }]}>Expand</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    onPress={() => {
                      onClose();
                      onAIAction('tasks');
                    }}
                    style={[styles.actionBtn, { backgroundColor: colors.bgSurface, borderColor: colors.border, width: '100%' }]}
                  >
                    <Ionicons name="checkbox-outline" size={16} color={colors.accent} />
                    <Text style={[styles.actionBtnText, { color: colors.textPrimary }]}>Create Tasks List</Text>
                  </TouchableOpacity>
                </View>

                {/* Note Management Section */}
                <Text style={[styles.sectionLabel, { color: colors.textMuted, marginTop: 12 }]}>
                  MANAGE NOTE
                </Text>

                <TouchableOpacity
                  onPress={() => {
                    onClose();
                    onTogglePin();
                  }}
                  style={[styles.menuRow, { borderBottomColor: colors.border }]}
                >
                  <Ionicons
                    name={note.isPinned ? 'pin' : 'pin-outline'}
                    size={16}
                    color={note.isPinned ? colors.accent : colors.textSecondary}
                  />
                  <Text style={[styles.menuRowText, { color: colors.textPrimary }]}>
                    {note.isPinned ? 'Unpin Note' : 'Pin to Top'}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => {
                    onClose();
                    onMoveFolder();
                  }}
                  style={[styles.menuRow, { borderBottomColor: colors.border }]}
                >
                  <Ionicons name="folder-outline" size={16} color={colors.textSecondary} />
                  <Text style={[styles.menuRowText, { color: colors.textPrimary }]}>
                    Move to Folder
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => {
                    onClose();
                    onDuplicate();
                  }}
                  style={[styles.menuRow, { borderBottomColor: colors.border }]}
                >
                  <Ionicons name="copy-outline" size={16} color={colors.textSecondary} />
                  <Text style={[styles.menuRowText, { color: colors.textPrimary }]}>
                    Duplicate Note
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => {
                    onClose();
                    onDelete();
                  }}
                  style={[styles.menuRow, { borderBottomWidth: 0 }]}
                >
                  <Ionicons name="trash-outline" size={16} color={colors.error} />
                  <Text style={[styles.menuRowText, { color: colors.error }]}>Delete Note</Text>
                </TouchableOpacity>
              </ScrollView>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.65)',
    justifyContent: 'flex-end',
  },
  sheet: {
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    borderWidth: 1,
    borderBottomWidth: 0,
    padding: 18,
    paddingBottom: 32,
  },
  dragHandle: {
    width: 36,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 12,
  },
  noteHeaderSnippet: {
    marginBottom: 12,
    paddingBottom: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  noteTitle: {
    fontSize: 15,
    fontWeight: '700',
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 8,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 4,
  },
  actionBtn: {
    width: '48.5%',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
    gap: 8,
  },
  actionBtnText: {
    fontSize: 12.5,
    fontWeight: '600',
  },
  menuRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    gap: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  menuRowText: {
    fontSize: 13.5,
    fontWeight: '500',
  },
});
