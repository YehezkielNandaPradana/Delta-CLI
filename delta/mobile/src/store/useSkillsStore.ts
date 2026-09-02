import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { DeltaSkill, PRESET_SKILLS } from '../types/skills';

const STORAGE_KEY = '@delta_skills_config';

interface SkillsState {
  skills: DeltaSkill[];
  isLoaded: boolean;

  loadSkills: () => Promise<void>;
  toggleSkill: (id: string) => Promise<void>;
  addCustomSkill: (skill: Omit<DeltaSkill, 'id' | 'isCustom'>) => Promise<string>;
  deleteCustomSkill: (id: string) => Promise<void>;
  getActiveSkillPrompts: (userQuery?: string) => string;
}

const persistSkills = async (skills: DeltaSkill[]) => {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(skills));
  } catch (e) {
    console.warn('Failed to save skills config', e);
  }
};

/**
 * Keyword match helper to selectively activate skills when relevant
 */
function isSkillRelevant(skill: DeltaSkill, query?: string): boolean {
  if (!query) return true; // If no query, include active skills
  const q = query.toLowerCase();

  // Match tags or name
  const matchTag = skill.tags.some((t) => q.includes(t.toLowerCase()));
  const matchName = q.includes(skill.name.toLowerCase()) || q.includes(skill.id.toLowerCase());

  // Heuristic topic matching
  if (skill.id === 'ui-ux-pro-max' || skill.id === 'frontend-design') {
    if (q.includes('ui') || q.includes('desain') || q.includes('button') || q.includes('tampilan') || q.includes('css') || q.includes('layout') || q.includes('komponen') || q.includes('react') || q.includes('mobile')) {
      return true;
    }
  }
  if (skill.id === 'security-sentinel') {
    if (q.includes('keamanan') || q.includes('security') || q.includes('auth') || q.includes('jwt') || q.includes('csrf') || q.includes('xss') || q.includes('scan') || q.includes('port')) {
      return true;
    }
  }
  if (skill.id === 'testing-guru') {
    if (q.includes('test') || q.includes('uji') || q.includes('assert') || q.includes('verifikasi')) {
      return true;
    }
  }
  if (skill.id === 'clean-architect') {
    if (q.includes('arsitektur') || q.includes('struktur') || q.includes('refactor') || q.includes('code') || q.includes('fungsi')) {
      return true;
    }
  }

  return matchTag || matchName;
}

export const useSkillsStore = create<SkillsState>((set, get) => ({
  skills: PRESET_SKILLS,
  isLoaded: false,

  loadSkills: async () => {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      if (raw) {
        const savedSkills: DeltaSkill[] = JSON.parse(raw);
        // Merge preset skills with saved ones
        const merged = PRESET_SKILLS.map((preset) => {
          const found = savedSkills.find((s) => s.id === preset.id);
          return found ? { ...preset, isActive: found.isActive } : preset;
        });

        // Append custom skills
        const customSkills = savedSkills.filter((s) => s.isCustom);
        set({ skills: [...merged, ...customSkills], isLoaded: true });
        return;
      }
    } catch (_) {}
    set({ isLoaded: true });
  },

  toggleSkill: async (id: string) => {
    const updated = get().skills.map((s) =>
      s.id === id ? { ...s, isActive: !s.isActive } : s
    );
    set({ skills: updated });
    await persistSkills(updated);
  },

  addCustomSkill: async (skillData) => {
    const id = `custom_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    const newSkill: DeltaSkill = {
      ...skillData,
      id,
      isCustom: true,
      isActive: true,
    };
    const updated = [...get().skills, newSkill];
    set({ skills: updated });
    await persistSkills(updated);
    return id;
  },

  deleteCustomSkill: async (id: string) => {
    const updated = get().skills.filter((s) => s.id !== id);
    set({ skills: updated });
    await persistSkills(updated);
  },

  getActiveSkillPrompts: (userQuery?: string) => {
    const { skills } = get();
    const activeSkills = skills.filter((s) => s.isActive);

    // Filter skills that are relevant to current query if query is provided
    const relevantSkills = userQuery
      ? activeSkills.filter((s) => isSkillRelevant(s, userQuery))
      : activeSkills;

    if (relevantSkills.length === 0) {
      return '';
    }

    const snippets = relevantSkills.map((s) => s.systemPromptSnippet).join('\n\n');
    return `\n\n## ACTIVE CODING & DESIGN SKILLS (Applied for this request):\n${snippets}`;
  },
}));
