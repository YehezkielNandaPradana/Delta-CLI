import React from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';
import { useNotesStore } from '../../store/useNotesStore';

interface NotesHeaderProps {
  onNewPress: () => void;
  onManageFoldersPress: () => void;
}

export const NotesHeader: React.FC<NotesHeaderProps> = ({
  onNewPress,
  onManageFoldersPress,
}) => {
  const { colors, isDark } = useThemeColors();
  const {
    notes,
    folders,
    selectedFolderId,
    setSelectedFolder,
    searchQuery,
    setSearchQuery,
  } = useNotesStore();

  const totalCount = selectedFolderId
    ? notes.filter((n) => n.folderId === selectedFolderId).length
    : notes.length;

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: colors.bgPrimary,
          borderBottomColor: colors.border,
          shadowColor: isDark ? '#FFFFFF' : '#000000',
        },
      ]}
    >
      {/* Title & Top Action Row */}
      <View style={styles.titleRow}>
        <View style={styles.titleWithBadge}>
          <Text style={[styles.title, { color: colors.textPrimary }]}>Notes</Text>
          <Text style={[styles.countBadge, { color: colors.textMuted }]}>
            {totalCount}
          </Text>
        </View>

        <View style={styles.headerActions}>
          <TouchableOpacity
            onPress={onManageFoldersPress}
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
            onPress={onNewPress}
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
      </View>

      {/* Editorial Search Input */}
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

      {/* Notion-Style Folder Chips */}
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
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 6,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  titleWithBadge: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    letterSpacing: -0.6,
  },
  countBadge: {
    fontSize: 13,
    fontWeight: '500',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  iconButton: {
    width: 34,
    height: 34,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    height: 34,
    borderRadius: 10,
    gap: 4,
  },
  primaryButtonText: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: -0.2,
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
});
