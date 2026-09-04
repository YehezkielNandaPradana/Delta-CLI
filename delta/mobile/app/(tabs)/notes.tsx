import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../src/theme/theme';
import { useNotesStore } from '../../src/store/useNotesStore';
import { useChatStore } from '../../src/store/useChatStore';
import { PageTransition } from '../../src/components/common/PageTransition';
import { Header } from '../../src/components/common/Header';
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
    notes,
    folders,
    selectedFolderId,
    setSelectedFolder,
    searchQuery,
    setSearchQuery,
    loadNotes,
    getFilteredNotes,
    createNote,
    deleteNote,
    togglePin,
    duplicateNote,
    updateNote,
  } = useNotesStore();

  const { addMessage } = useChatStore();

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
  const totalCount = selectedFolderId
    ? notes.filter((n) => n.folderId === selectedFolderId).length
    : notes.length;

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
      addMessage({
        sender: 'user',
        text: `[Context from Note: "${note.title}"]\n${note.content}\n\nCan you explain and advise on this note?`,
      });
      router.push('/(tabs)');
      return;
    }

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
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]}
      edges={['top']}
    >
      <PageTransition style={[styles.container, { backgroundColor: colors.bgPrimary }]}>
        {/* Standard Unified Header */}
        <Header
          title="Notes"
          countBadge={totalCount}
          subtitle="Catatan & Dokumentasi Teknis"
          rightAction={
            <View style={styles.headerRightButtons}>
              <TouchableOpacity
                onPress={() => setFolderManagerVisible(true)}
                style={[
                  styles.iconButton,
                  {
                    backgroundColor: colors.bgSurface,
                    borderColor: colors.border,
                  },
                ]}
                activeOpacity={0.7}
                accessibilityLabel="Manage folders"
              >
                <Ionicons name="folder-outline" size={15} color={colors.textSecondary} />
              </TouchableOpacity>

              <TouchableOpacity
                onPress={() => setNewItemSheetVisible(true)}
                style={[
                  styles.primaryButton,
                  {
                    backgroundColor: colors.textPrimary,
                  },
                ]}
                activeOpacity={0.8}
                accessibilityLabel="Create note or folder"
              >
                <Ionicons name="add" size={16} color={colors.bgPrimary} />
                <Text style={[styles.primaryButtonText, { color: colors.bgPrimary }]}>Tulis</Text>
              </TouchableOpacity>
            </View>
          }
        />

        {/* Search & Folder Strip */}
        <View style={styles.searchStrip}>
          <View
            style={[
              styles.searchBox,
              {
                backgroundColor: colors.bgSecondary,
                borderColor: searchQuery.length > 0 ? colors.accent : colors.border,
              },
            ]}
          >
            <Ionicons name="search-outline" size={15} color={colors.textMuted} style={styles.searchIcon} />
            <TextInput
              value={searchQuery}
              onChangeText={setSearchQuery}
              placeholder="Cari catatan atau tag..."
              placeholderTextColor={colors.textMuted}
              style={[styles.searchInput, { color: colors.textPrimary }]}
              autoCapitalize="none"
              autoCorrect={false}
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity
                onPress={() => setSearchQuery('')}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Ionicons name="close-circle-sharp" size={16} color={colors.textMuted} />
              </TouchableOpacity>
            )}
          </View>

          {/* Folder Chips */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.folderPillsContainer}
          >
            <TouchableOpacity
              onPress={() => setSelectedFolder(null)}
              style={[
                styles.folderChip,
                {
                  backgroundColor:
                    selectedFolderId === null
                      ? (isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)')
                      : 'transparent',
                  borderColor:
                    selectedFolderId === null
                      ? colors.borderStrong
                      : 'transparent',
                },
              ]}
              activeOpacity={0.7}
            >
              <Ionicons
                name="layers-outline"
                size={12}
                color={selectedFolderId === null ? colors.textPrimary : colors.textMuted}
              />
              <Text
                style={[
                  styles.folderChipText,
                  {
                    color: selectedFolderId === null ? colors.textPrimary : colors.textSecondary,
                    fontWeight: selectedFolderId === null ? '600' : '400',
                  },
                ]}
              >
                Semua
              </Text>
            </TouchableOpacity>

            {folders.map((folder) => {
              const isSelected = selectedFolderId === folder.id;
              return (
                <TouchableOpacity
                  key={folder.id}
                  onPress={() => setSelectedFolder(folder.id)}
                  style={[
                    styles.folderChip,
                    {
                      backgroundColor: isSelected
                        ? (isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)')
                        : 'transparent',
                      borderColor: isSelected
                        ? colors.borderStrong
                        : 'transparent',
                    },
                  ]}
                  activeOpacity={0.7}
                >
                  <Ionicons
                    name="folder-outline"
                    size={12}
                    color={isSelected ? colors.textPrimary : colors.textMuted}
                  />
                  <Text
                    style={[
                      styles.folderChipText,
                      {
                        color: isSelected ? colors.textPrimary : colors.textSecondary,
                        fontWeight: isSelected ? '600' : '400',
                      },
                    ]}
                  >
                    {folder.name}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

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
  safeArea: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  headerRightButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  iconButton: {
    width: 32,
    height: 32,
    borderRadius: 9,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    height: 32,
    borderRadius: 9,
    gap: 3,
  },
  primaryButtonText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: -0.2,
  },
  searchStrip: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 38,
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 10,
    marginBottom: 8,
  },
  searchIcon: {
    marginRight: 6,
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    paddingVertical: 0,
  },
  folderPillsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingRight: 16,
    paddingBottom: 2,
  },
  folderChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    gap: 5,
  },
  folderChipText: {
    fontSize: 12,
    letterSpacing: -0.2,
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
