import React, { useState } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Switch,
  TouchableWithoutFeedback,
  Alert,
  Platform,
} from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useThemeColors } from '../../theme/theme';
import { useSkillsStore } from '../../store/useSkillsStore';
import { DeltaSkill } from '../../types/skills';
import { BlurBackdrop } from '../common/BlurBackdrop';

interface SkillsManagerModalProps {
  visible: boolean;
  onClose: () => void;
}

export const SkillsManagerModal: React.FC<SkillsManagerModalProps> = ({
  visible,
  onClose,
}) => {
  const { colors, isDark } = useThemeColors();
  const { skills, toggleSkill, addCustomSkill, deleteCustomSkill } = useSkillsStore();

  const [isAdding, setIsAdding] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [promptSnippet, setPromptSnippet] = useState('');
  const [tags, setTags] = useState('');

  const handleToggle = (id: string) => {
    Haptics.selectionAsync().catch(() => {});
    toggleSkill(id);
  };

  const handleSaveCustomSkill = async () => {
    if (!name.trim() || !promptSnippet.trim()) {
      Alert.alert('Validasi', 'Nama skill dan instruksi prompt wajib diisi.');
      return;
    }

    const tagList = tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    await addCustomSkill({
      name: name.trim(),
      category: 'Custom',
      description: description.trim() || 'Custom user skill discipline',
      tags: tagList.length > 0 ? tagList : ['Custom'],
      systemPromptSnippet: `[SKILL: ${name.trim()}]\n${promptSnippet.trim()}`,
      isActive: true,
    });

    setName('');
    setDescription('');
    setPromptSnippet('');
    setTags('');
    setIsAdding(false);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
  };

  const handleDelete = (id: string, title: string) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    Alert.alert('Hapus Skill', `Hapus skill "${title}"?`, [
      { text: 'Batal', style: 'cancel' },
      {
        text: 'Hapus',
        style: 'destructive',
        onPress: () => deleteCustomSkill(id),
      },
    ]);
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.backdrop}>
          <BlurBackdrop intensity={50} />
          <TouchableWithoutFeedback>
            <View
              style={[
                styles.sheetContainer,
                {
                  backgroundColor: colors.bgSecondary,
                  borderColor: colors.border,
                },
              ]}
            >
              {/* Header */}
              <View style={styles.header}>
                <View
                  style={[
                    styles.dragBar,
                    { backgroundColor: isDark ? 'rgba(255, 255, 255, 0.25)' : 'rgba(0, 0, 0, 0.2)' },
                  ]}
                />
                <View style={styles.titleRow}>
                  <View style={styles.titleWithIcon}>
                    <View style={[styles.iconBoxMini, { backgroundColor: isDark ? '#262626' : '#EAEAEA' }]}>
                      <Ionicons name="construct-outline" size={16} color={colors.textPrimary} />
                    </View>
                    <View>
                      <Text style={[styles.title, { color: colors.textPrimary }]}>
                        Skill Coding & Desain Delta
                      </Text>
                      <Text style={[styles.subtitle, { color: colors.textMuted }]}>
                        Skill aktif diinject ke AI untuk asistensi coding & arsitektur
                      </Text>
                    </View>
                  </View>
                  <TouchableOpacity
                    onPress={onClose}
                    style={[styles.closeBtn, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}
                  >
                    <Feather name="x" size={15} color={colors.textSecondary} />
                  </TouchableOpacity>
                </View>
              </View>

              <ScrollView
                style={styles.contentScroll}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={true}
              >
                {/* Add Custom Skill Button / Form */}
                {!isAdding ? (
                  <TouchableOpacity
                    onPress={() => setIsAdding(true)}
                    style={[
                      styles.addSkillBtn,
                      {
                        backgroundColor: isDark ? '#262626' : '#EAEAEA',
                        borderColor: colors.border,
                      },
                    ]}
                    activeOpacity={0.7}
                  >
                    <Ionicons name="add-circle-outline" size={16} color={colors.textPrimary} />
                    <Text style={[styles.addSkillText, { color: colors.textPrimary }]}>
                      + Tambah Custom Skill Coding
                    </Text>
                  </TouchableOpacity>
                ) : (
                  <View style={[styles.addForm, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
                    <Text style={[styles.formTitle, { color: colors.textPrimary }]}>
                      Tambah Skill Baru
                    </Text>

                    <TextInput
                      value={name}
                      onChangeText={setName}
                      placeholder="Nama Skill (cth: NextJS Architect)"
                      placeholderTextColor={colors.textMuted}
                      style={[styles.input, { color: colors.textPrimary, borderColor: colors.border, backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA' }]}
                    />

                    <TextInput
                      value={description}
                      onChangeText={setDescription}
                      placeholder="Deskripsi singkat..."
                      placeholderTextColor={colors.textMuted}
                      style={[styles.input, { color: colors.textPrimary, borderColor: colors.border, backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA' }]}
                    />

                    <TextInput
                      value={tags}
                      onChangeText={setTags}
                      placeholder="Tags pemicu (koma): nextjs, server action, app router"
                      placeholderTextColor={colors.textMuted}
                      style={[styles.input, { color: colors.textPrimary, borderColor: colors.border, backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA' }]}
                    />

                    <TextInput
                      value={promptSnippet}
                      onChangeText={setPromptSnippet}
                      placeholder="Instruksi aturan skill yang disuntikkan ke AI..."
                      placeholderTextColor={colors.textMuted}
                      multiline
                      numberOfLines={3}
                      style={[styles.textArea, { color: colors.textPrimary, borderColor: colors.border, backgroundColor: isDark ? '#0A0A0A' : '#FAFAFA' }]}
                    />

                    <View style={styles.formBtnRow}>
                      <TouchableOpacity
                        onPress={() => setIsAdding(false)}
                        style={[styles.formCancelBtn, { borderColor: colors.border }]}
                      >
                        <Text style={[styles.btnText, { color: colors.textMuted }]}>Batal</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        onPress={handleSaveCustomSkill}
                        style={[styles.formSaveBtn, { backgroundColor: colors.textPrimary }]}
                      >
                        <Text style={[styles.btnText, { color: colors.bgPrimary }]}>Simpan Skill</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}

                {/* Skills Table List */}
                <View style={[styles.groupedTable, { backgroundColor: colors.bgSurface, borderColor: colors.border }]}>
                  {skills.map((skill, index) => {
                    const isLast = index === skills.length - 1;

                    return (
                      <View key={skill.id}>
                        <View style={styles.skillRow}>
                          <View style={styles.skillLeft}>
                            <View style={styles.skillTitleRow}>
                              <Text
                                style={[
                                  styles.skillName,
                                  { color: colors.textPrimary, fontWeight: skill.isActive ? '700' : '500' },
                                ]}
                              >
                                {skill.name}
                              </Text>
                              <View
                                style={[
                                  styles.categoryBadge,
                                  { backgroundColor: isDark ? '#262626' : '#E5E5E5' },
                                ]}
                              >
                                <Text style={[styles.categoryText, { color: colors.textPrimary }]}>
                                  {skill.category}
                                </Text>
                              </View>
                            </View>

                            <Text style={[styles.skillDesc, { color: colors.textMuted }]} numberOfLines={2}>
                              {skill.description}
                            </Text>

                            <View style={styles.tagsRow}>
                              {skill.tags.map((t) => (
                                <Text key={t} style={[styles.tagItem, { color: colors.textSecondary }]}>
                                  #{t}
                                </Text>
                              ))}
                            </View>
                          </View>

                          <View style={styles.skillRight}>
                            <Switch
                              value={skill.isActive}
                              onValueChange={() => handleToggle(skill.id)}
                              trackColor={{ false: isDark ? '#262626' : '#E5E5E5', true: colors.textPrimary }}
                              thumbColor={isDark ? '#000000' : '#FFFFFF'}
                            />

                            {skill.isCustom && (
                              <TouchableOpacity
                                onPress={() => handleDelete(skill.id, skill.name)}
                                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                                style={styles.deleteBtn}
                              >
                                <Ionicons name="trash-outline" size={14} color={colors.error} />
                              </TouchableOpacity>
                            )}
                          </View>
                        </View>

                        {!isLast && <View style={[styles.divider, { backgroundColor: colors.border }]} />}
                      </View>
                    );
                  })}
                </View>
              </ScrollView>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.65)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    width: '100%',
    height: Platform.OS === 'ios' ? '82%' : '85%',
    borderTopLeftRadius: 26,
    borderTopRightRadius: 26,
    borderWidth: 1,
    borderBottomWidth: 0,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -4 },
        shadowOpacity: 0.28,
        shadowRadius: 18,
      },
      android: {
        elevation: 16,
      },
    }),
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 8,
  },
  dragBar: {
    width: 36,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 10,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  titleWithIcon: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
    marginRight: 8,
  },
  iconBoxMini: {
    width: 30,
    height: 30,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 16.5,
    fontWeight: '800',
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 11,
    marginTop: 1,
  },
  closeBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  contentScroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: Platform.OS === 'ios' ? 44 : 36,
    gap: 12,
  },
  addSkillBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 40,
    borderRadius: 10,
    borderWidth: 1,
    gap: 6,
  },
  addSkillText: {
    fontSize: 12.5,
    fontWeight: '700',
  },
  addForm: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    gap: 8,
  },
  formTitle: {
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 2,
  },
  input: {
    height: 38,
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 10,
    fontSize: 12.5,
  },
  textArea: {
    height: 64,
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingTop: 8,
    fontSize: 12,
    textAlignVertical: 'top',
  },
  formBtnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  formCancelBtn: {
    flex: 1,
    height: 36,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  formSaveBtn: {
    flex: 1.5,
    height: 36,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnText: {
    fontSize: 12,
    fontWeight: '700',
  },
  groupedTable: {
    borderRadius: 14,
    borderWidth: 1,
    overflow: 'hidden',
  },
  skillRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  skillLeft: {
    flex: 1,
    marginRight: 10,
  },
  skillTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  skillName: {
    fontSize: 13.5,
    letterSpacing: -0.2,
  },
  categoryBadge: {
    paddingHorizontal: 6,
    paddingVertical: 1.5,
    borderRadius: 4,
  },
  categoryText: {
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  skillDesc: {
    fontSize: 11,
    marginTop: 3,
    lineHeight: 15,
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
    marginTop: 4,
  },
  tagItem: {
    fontSize: 10,
  },
  skillRight: {
    alignItems: 'center',
    gap: 8,
  },
  deleteBtn: {
    padding: 2,
  },
  divider: {
    height: StyleSheet.hairlineWidth,
    marginLeft: 14,
  },
});
