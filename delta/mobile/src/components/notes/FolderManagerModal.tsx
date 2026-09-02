import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { useNotesStore } from '../../store/useNotesStore';
import { NoteFolder } from '../../types/notes';

interface FolderManagerModalProps {
  visible: boolean;
  onClose: () => void;
}

export const FolderManagerModal: React.FC<FolderManagerModalProps> = ({
  visible,
  onClose,
}) => {
  const { colors } = useThemeColors();
  const { folders, createFolder, renameFolder, deleteFolder } = useNotesStore();

  const [newFolderName, setNewFolderName] = useState('');
  const [editingFolderId, setEditingFolderId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  const handleAddFolder = async () => {
    if (!newFolderName.trim()) return;
    await createFolder(newFolderName);
    setNewFolderName('');
  };

  const handleStartRename = (folder: NoteFolder) => {
    setEditingFolderId(folder.id);
    setEditName(folder.name);
  };

  const handleSaveRename = async () => {
    if (editingFolderId && editName.trim()) {
      await renameFolder(editingFolderId, editName);
      setEditingFolderId(null);
    }
  };

  const handleDelete = (folder: NoteFolder) => {
    Alert.alert(
      'Delete Folder',
      `Are you sure you want to delete "${folder.name}"? Notes inside will be unassigned, not deleted.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deleteFolder(folder.id),
        },
      ]
    );
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View
          style={[
            styles.container,
            {
              backgroundColor: colors.surfaceElevated,
              borderColor: colors.border,
            },
          ]}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={[styles.title, { color: colors.textPrimary }]}>Manage Folders</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <Ionicons name="close" size={20} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {/* Create New Folder Input */}
          <View style={styles.inputRow}>
            <TextInput
              value={newFolderName}
              onChangeText={setNewFolderName}
              placeholder="New folder name..."
              placeholderTextColor={colors.textMuted}
              style={[
                styles.input,
                {
                  backgroundColor: colors.bgSurface,
                  borderColor: colors.border,
                  color: colors.textPrimary,
                },
              ]}
            />
            <TouchableOpacity
              onPress={handleAddFolder}
              disabled={!newFolderName.trim()}
              style={[
                styles.addBtn,
                {
                  backgroundColor: newFolderName.trim()
                    ? colors.accent
                    : colors.surfaceHover,
                },
              ]}
            >
              <Ionicons
                name="add"
                size={18}
                color={newFolderName.trim() ? '#090A0C' : colors.textDisabled}
              />
            </TouchableOpacity>
          </View>

          {/* Folder List */}
          <ScrollView style={styles.folderList} contentContainerStyle={{ paddingBottom: 20 }}>
            {folders.map((folder) => {
              const isEditing = editingFolderId === folder.id;

              return (
                <View
                  key={folder.id}
                  style={[
                    styles.folderItem,
                    {
                      borderColor: colors.border,
                      backgroundColor: colors.bgSurface,
                    },
                  ]}
                >
                  <Ionicons name="folder-outline" size={18} color={colors.accent} />

                  {isEditing ? (
                    <View style={styles.renameRow}>
                      <TextInput
                        value={editName}
                        onChangeText={setEditName}
                        autoFocus
                        style={[
                          styles.renameInput,
                          {
                            color: colors.textPrimary,
                            borderBottomColor: colors.accent,
                          },
                        ]}
                      />
                      <TouchableOpacity onPress={handleSaveRename} style={styles.saveRenameBtn}>
                        <Ionicons name="checkmark-circle" size={20} color={colors.accent} />
                      </TouchableOpacity>
                      <TouchableOpacity onPress={() => setEditingFolderId(null)}>
                        <Ionicons name="close-circle-outline" size={20} color={colors.textMuted} />
                      </TouchableOpacity>
                    </View>
                  ) : (
                    <>
                      <Text style={[styles.folderName, { color: colors.textPrimary }]}>
                        {folder.name}
                      </Text>
                      <View style={styles.actions}>
                        <TouchableOpacity
                          onPress={() => handleStartRename(folder)}
                          style={styles.iconAction}
                        >
                          <Ionicons name="pencil-outline" size={15} color={colors.textSecondary} />
                        </TouchableOpacity>
                        <TouchableOpacity
                          onPress={() => handleDelete(folder)}
                          style={styles.iconAction}
                        >
                          <Ionicons name="trash-outline" size={15} color={colors.error} />
                        </TouchableOpacity>
                      </View>
                    </>
                  )}
                </View>
              );
            })}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.65)',
    justifyContent: 'flex-end',
  },
  container: {
    maxHeight: '80%',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    borderWidth: 1,
    borderBottomWidth: 0,
    padding: 18,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
  },
  closeBtn: {
    padding: 2,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 14,
  },
  input: {
    flex: 1,
    height: 42,
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 14,
    fontSize: 13.5,
  },
  addBtn: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  folderList: {
    maxHeight: 320,
  },
  folderItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 8,
    gap: 10,
  },
  folderName: {
    flex: 1,
    fontSize: 13.5,
    fontWeight: '500',
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconAction: {
    padding: 2,
  },
  renameRow: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  renameInput: {
    flex: 1,
    fontSize: 13.5,
    borderBottomWidth: 1,
    paddingVertical: 2,
  },
  saveRenameBtn: {
    padding: 2,
  },
});
