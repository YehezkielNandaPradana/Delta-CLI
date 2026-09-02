import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Note } from '../../types/notes';
import { useThemeColors } from '../../theme/theme';
import { useNotesStore } from '../../store/useNotesStore';
import { formatTimestamp } from '../../utils/formatters';

interface NoteCardProps {
  note: Note;
  onPress: () => void;
  onMorePress: () => void;
}

export const NoteCard: React.FC<NoteCardProps> = ({
  note,
  onPress,
  onMorePress,
}) => {
  const { colors, isDark } = useThemeColors();
  const { folders } = useNotesStore();

  const folder = folders.find((f) => f.id === note.folderId);
  const cleanSnippet = note.content
    ? note.content
        .replace(/^#+\s+/gm, '')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/^[-*]\s+/gm, '• ')
        .trim()
        .slice(0, 130)
    : '';

  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[
        styles.card,
        {
          backgroundColor: colors.bgSurface,
          borderColor: note.isPinned ? colors.borderStrong : colors.border,
          borderLeftColor: note.isPinned ? colors.accent : colors.border,
          borderLeftWidth: note.isPinned ? 3 : 1,
        },
      ]}
    >
      {/* Card Header: Title + Action */}
      <View style={styles.headerRow}>
        <Text
          style={[styles.title, { color: colors.textPrimary }]}
          numberOfLines={1}
        >
          {note.title || 'Tanpa Judul'}
        </Text>

        <View style={styles.actionsRight}>
          {note.isPinned && (
            <Ionicons name="pin" size={13} color={colors.accent} style={styles.pinnedIcon} />
          )}

          <TouchableOpacity
            onPress={onMorePress}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            style={styles.actionIconBtn}
          >
            <Ionicons name="ellipsis-horizontal" size={16} color={colors.textMuted} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Content Preview */}
      {cleanSnippet ? (
        <Text
          style={[styles.snippet, { color: colors.textSecondary }]}
          numberOfLines={2}
        >
          {cleanSnippet}
        </Text>
      ) : null}

      {/* Meta Line: Folder + Date + Tags */}
      <View style={styles.metaRow}>
        <View style={styles.metaLeft}>
          <Text style={[styles.timeText, { color: colors.textMuted }]}>
            {formatTimestamp(note.updatedAt)}
          </Text>

          {folder && (
            <View style={styles.folderInline}>
              <Text style={[styles.dotSeparator, { color: colors.textDim }]}>•</Text>
              <Text style={[styles.folderName, { color: colors.textMuted }]}>
                {folder.name}
              </Text>
            </View>
          )}
        </View>

        {note.tags && note.tags.length > 0 && (
          <View style={styles.tagsRow}>
            {note.tags.slice(0, 2).map((tag, idx) => (
              <View
                key={idx}
                style={[
                  styles.tagBadge,
                  {
                    backgroundColor: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)',
                    borderColor: colors.border,
                  },
                ]}
              >
                <Text style={[styles.tagText, { color: colors.textMuted }]}>
                  {tag}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 8,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  title: {
    fontSize: 15.5,
    fontWeight: '700',
    letterSpacing: -0.3,
    flex: 1,
    marginRight: 8,
  },
  actionsRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  pinnedIcon: {
    marginRight: 2,
  },
  actionIconBtn: {
    padding: 2,
  },
  snippet: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 2,
  },
  metaLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  timeText: {
    fontSize: 11,
    fontWeight: '400',
  },
  dotSeparator: {
    fontSize: 10,
    marginHorizontal: 2,
  },
  folderInline: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  folderName: {
    fontSize: 11,
    fontWeight: '500',
  },
  tagsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  tagBadge: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 6,
    borderWidth: 1,
  },
  tagText: {
    fontSize: 10,
    fontWeight: '500',
  },
});