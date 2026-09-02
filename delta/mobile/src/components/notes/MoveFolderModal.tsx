import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  TouchableWithoutFeedback,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { useNotesStore } from '../../store/useNotesStore';
import { Note } from '../../types/notes';

interface MoveFolderModalProps {
  visible: boolean;
  note: Note | null;
  onClose: () => void;
}

export const MoveFolderModal: React.FC<MoveFolderModalProps> = ({
  visible,
  note,
  onClose,
}) => {
  const { colors } = useThemeColors();
  const { folders, moveNote } = useNotesStore();

  if (!note) return null;

  const handleSelectFolder = async (folderId: string | null) => {
    await moveNote(note.id, folderId);
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.overlay}>
          <TouchableWithoutFeedback>
            <View
              style={[
                styles.sheet,
                {
                  backgroundColor: colors.cardBg,
                  borderColor: colors.cardBorder,
                  borderTopColor: colors.cardSpecular,
                },
              ]}
            >
              <View style={styles.dragHandle} />
              <Text style={[styles.title, { color: colors.textPrimary }]}>Move Note to Folder</Text>

              <ScrollView style={{ maxHeight: 300 }}>
                {/* Unassigned / No folder option */}
                <TouchableOpacity
                  onPress={() => handleSelectFolder(null)}
                  style={[
                    styles.folderItem,
                    {
                      backgroundColor: note.folderId === null ? colors.accentGreen + '20' : colors.surfaceHover,
                      borderColor: note.folderId === null ? colors.accentGreen : colors.cardBorder,
                    },
                  ]}
                >
                  <Ionicons name="folder-open-outline" size={18} color={note.folderId === null ? colors.accentGreen : colors.textSecondary} />
                  <Text style={[styles.folderName, { color: note.folderId === null ? colors.accentGreen : colors.textPrimary }]}>
                    No Folder (Unassigned)
                  </Text>
                  {note.folderId === null && <Ionicons name="checkmark" size={18} color={colors.accentGreen} />}
                </TouchableOpacity>

                {folders.map((f) => {
                  const isCurrent = note.folderId === f.id;
                  return (
                    <TouchableOpacity
                      key={f.id}
                      onPress={() => handleSelectFolder(f.id)}
                      style={[
                        styles.folderItem,
                        {
                          backgroundColor: isCurrent ? colors.accentGreen + '20' : colors.surfaceHover,
                          borderColor: isCurrent ? colors.accentGreen : colors.cardBorder,
                        },
                      ]}
                    >
                      <Ionicons name="folder-outline" size={18} color={isCurrent ? colors.accentGreen : colors.textSecondary} />
                      <Text style={[styles.folderName, { color: isCurrent ? colors.accentGreen : colors.textPrimary }]}>
                        {f.name}
                      </Text>
                      {isCurrent && <Ionicons name="checkmark" size={18} color={colors.accentGreen} />}
                    </TouchableOpacity>
                  );
                })}
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
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  sheet: {
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    borderWidth: 1,
    borderTopWidth: 1.5,
    padding: 20,
    paddingBottom: 36,
  },
  dragHandle: {
    width: 36,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(150,150,150,0.4)',
    alignSelf: 'center',
    marginBottom: 14,
  },
  title: {
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 16,
  },
  folderItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 8,
    gap: 12,
  },
  folderName: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
  },
});
