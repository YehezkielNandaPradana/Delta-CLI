import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  TouchableWithoutFeedback,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useThemeColors } from '../../theme/theme';

interface NewItemSheetProps {
  visible: boolean;
  onClose: () => void;
  onCreateNote: () => void;
  onCreateFolder: () => void;
}

export const NewItemSheet: React.FC<NewItemSheetProps> = ({
  visible,
  onClose,
  onCreateNote,
  onCreateFolder,
}) => {
  const { colors } = useThemeColors();

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
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
              <Text style={[styles.heading, { color: colors.textPrimary }]}>Create New</Text>

              {/* Action 1: Note */}
              <TouchableOpacity
                onPress={() => {
                  onClose();
                  onCreateNote();
                }}
                style={[styles.itemButton, { backgroundColor: colors.surfaceHover }]}
                activeOpacity={0.7}
              >
                <View style={[styles.iconBox, { backgroundColor: colors.accentGreen + '20' }]}>
                  <Ionicons name="document-text-outline" size={22} color={colors.accentGreen} />
                </View>
                <View style={styles.itemMeta}>
                  <Text style={[styles.itemTitle, { color: colors.textPrimary }]}>Note</Text>
                  <Text style={[styles.itemSubtitle, { color: colors.textSecondary }]}>
                    Capture thoughts, ideas, or guides
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
              </TouchableOpacity>

              {/* Action 2: Folder */}
              <TouchableOpacity
                onPress={() => {
                  onClose();
                  onCreateFolder();
                }}
                style={[styles.itemButton, { backgroundColor: colors.surfaceHover }]}
                activeOpacity={0.7}
              >
                <View style={[styles.iconBox, { backgroundColor: '#38bdf820' }]}>
                  <Ionicons name="folder-outline" size={22} color="#38bdf8" />
                </View>
                <View style={styles.itemMeta}>
                  <Text style={[styles.itemTitle, { color: colors.textPrimary }]}>Folder</Text>
                  <Text style={[styles.itemSubtitle, { color: colors.textSecondary }]}>
                    Organize notes into categories
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
              </TouchableOpacity>
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
    backgroundColor: 'rgba(0,0,0,0.5)',
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
    marginBottom: 16,
  },
  heading: {
    fontSize: 17,
    fontWeight: '800',
    marginBottom: 16,
  },
  itemButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 18,
    marginBottom: 10,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  itemMeta: {
    flex: 1,
  },
  itemTitle: {
    fontSize: 15,
    fontWeight: '700',
    marginBottom: 2,
  },
  itemSubtitle: {
    fontSize: 12,
  },
});
