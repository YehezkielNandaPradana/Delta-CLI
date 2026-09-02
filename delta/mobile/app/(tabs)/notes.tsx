import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../src/theme/theme';
import { useNotesStore } from '../../src/store/useNotesStore';
import { useChatStore } from '../../src/store/useChatStore';
import { PageTransition } from '../../src/components/common/PageTransition';
import { NotesHeader } from '../../src/components/notes/NotesHeader';
import { NoteCard } from '../../src/components/notes/NoteCard';
import { NoteEditorModal } from '../../src/components/notes/NoteEditorModal';
import { NoteActionSheet } from '../../src/components/notes/NoteActionSheet';
import { FolderManagerModal } from '../../src/components/notes/FolderManagerModal';
import { MoveFolderModal } from '../../src/components/notes/MoveFolderModal';
import { NewItemSheet } from '../../src/components/notes/NewItemSheet';
import { Note, NoteAIAction } from '../../src/types/notes';
import { sendChatMessage } from '../../src/services/api/chatApi';

export default function NotesScreen() {
  const router = useRouter();
  const { colors, isDark } = useThemeColors();
  const {
    loadNotes,
    getFilteredNotes,
    createNote,
    deleteNote,
    togglePin,
    duplicateNote,
    updateNote,
  } = useNotesStore();

  const { addMessage, startExecution, appendStreamingText, finishExecution } = useChatStore();

  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);
  const [editorVisible, setEditorVisible] = useState(false);
  const [actionSheetNote, setActionSheetNote] = useState<Note | null>(null);
  const [folderManagerVisible, setFolderManagerVisible] = useState(false);
  const [moveFolderNote, setMoveFolderNote] = useState<Note | null>(null);
  const [newItemSheetVisible, setNewItemSheetVisible] = useState(false);

  useEffect(() => {
    loadNotes();
  }, []);

  const filteredNotes = getFilteredNotes();

  const handleOpenNote = (noteId: string) => {
    setSelectedNoteId(noteId);
    setEditorVisible(true);
  };

  const handleQuickCreateNote = async () => {
    const newNote = await createNote();
    setSelectedNoteId(newNote.id);
    setEditorVisible(true);
  };

  const handleAIAction = async (action: NoteAIAction, note: Note) => {
    if (action === 'ask') {
      // Ingest note context into chat & navigate to chat
      addMessage({
        sender: 'user',
        text: `[Context from Note: "${note.title}"]\n${note.content}\n\nCan you explain and advise on this note?`,
      });
      router.push('/(tabs)');
      return;
    }

    // Direct AI transformations on note
    let prompt = '';
    if (action === 'summarize') {
      prompt = `Summarize the following note clearly with key points and insights:\n\nTitle: ${note.title}\nContent:\n${note.content}`;
    } else if (action === 'improve') {
      prompt = `Improve the structure, clarity, technical precision, and grammar of this note while preserving its core intent:\n\nTitle: ${note.title}\nContent:\n${note.content}`;
    } else if (action === 'expand') {
      prompt = `Elaborate and brainstorm deeper technical details, architectures, security considerations, or next steps for this note:\n\nTitle: ${note.title}\nContent:\n${note.content}`;
    } else if (action === 'tasks') {
      prompt = `Convert the following note into an actionable Markdown task checklist (using [ ] checkboxes):\n\nTitle: ${note.title}\nContent:\n${note.content}`;
    }

    try {
      const res = await sendChatMessage(prompt);
      const aiResponse = res.output || res.response || '';
      if (aiResponse) {
        if (action === 'tasks') {
          await updateNote(note.id, {
            content: `${note.content}\n\n## Actionable Tasks\n${aiResponse}`,
          });
        } else if (action === 'summarize') {
          await updateNote(note.id, {
            content: `${note.content}\n\n## Summary\n${aiResponse}`,
          });
        } else {
          await updateNote(note.id, {
            content: `${note.content}\n\n## Delta Analysis (${action.toUpperCase()})\n${aiResponse}`,
          });
        }
        Alert.alert('AI Action Complete', `Successfully applied "${action}" to note "${note.title}".`);
      }
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to execute AI action');
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <PageTransition style={styles.container}>
        {/* Header with Search & Folder pills */}
        <NotesHeader
          onNewPress={() => setNewItemSheetVisible(true)}
          onManageFoldersPress={() => setFolderManagerVisible(true)}
        />

        {/* Notes List */}
        <FlatList
          data={filteredNotes}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          renderItem={({ item }) => (
            <NoteCard
              note={item}
              onPress={() => handleOpenNote(item.id)}
              onMorePress={() => setActionSheetNote(item)}
            />
          )}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <View
                style={[
                  styles.emptyIconBox,
                  { backgroundColor: colors.bgSurface, borderColor: colors.border },
                ]}
              >
                <Ionicons name="create-outline" size={26} color={colors.textSecondary} />
              </View>
              <Text style={[styles.emptyTitle, { color: colors.textPrimary }]}>
                Belum Ada Catatan
              </Text>
              <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
                Buat ide baru atau minta Delta di chat untuk mencatat temuan secara otomatis.
              </Text>
              <TouchableOpacity
                onPress={handleQuickCreateNote}
                style={[styles.emptyButton, { backgroundColor: colors.textPrimary }]}
                activeOpacity={0.8}
              >
                <Ionicons name="add" size={16} color={colors.bgPrimary} />
                <Text style={[styles.emptyButtonText, { color: colors.bgPrimary }]}>Buat Catatan</Text>
              </TouchableOpacity>
            </View>
          }
        />
      </PageTransition>

      {/* Editor Modal */}
      <NoteEditorModal
        visible={editorVisible}
        noteId={selectedNoteId}
        onClose={() => {
          setEditorVisible(false);
          setSelectedNoteId(null);
        }}
        onAIAction={handleAIAction}
        onMoveFolder={(note) => setMoveFolderNote(note)}
      />

      {/* Note Action Sheet (Long press / More menu) */}
      <NoteActionSheet
        visible={!!actionSheetNote}
        note={actionSheetNote}
        onClose={() => setActionSheetNote(null)}
        onAIAction={(action) => {
          if (actionSheetNote) handleAIAction(action, actionSheetNote);
        }}
        onTogglePin={() => {
          if (actionSheetNote) togglePin(actionSheetNote.id);
        }}
        onMoveFolder={() => {
          setMoveFolderNote(actionSheetNote);
        }}
        onDuplicate={() => {
          if (actionSheetNote) duplicateNote(actionSheetNote.id);
        }}
        onDelete={() => {
          if (actionSheetNote) deleteNote(actionSheetNote.id);
        }}
      />

      {/* Folder Manager Modal */}
      <FolderManagerModal
        visible={folderManagerVisible}
        onClose={() => setFolderManagerVisible(false)}
      />

      {/* Move Folder Modal */}
      <MoveFolderModal
        visible={!!moveFolderNote}
        note={moveFolderNote}
        onClose={() => setMoveFolderNote(null)}
      />

      {/* Quick Action Bottom Sheet */}
      <NewItemSheet
        visible={newItemSheetVisible}
        onClose={() => setNewItemSheetVisible(false)}
        onCreateNote={handleQuickCreateNote}
        onCreateFolder={() => setFolderManagerVisible(true)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 90,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 70,
    paddingHorizontal: 32,
  },
  emptyIconBox: {
    width: 52,
    height: 52,
    borderRadius: 26,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  emptyTitle: {
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 6,
    letterSpacing: -0.3,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
    marginBottom: 20,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 10,
    gap: 6,
  },
  emptyButtonText: {
    fontSize: 13.5,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
});
