import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { AntigravityAccount, ConnectionMode } from '../types/cloud';

const STORAGE_KEY = '@delta_settings';

// Sensible defaults based on execution platform
const DEFAULT_HOST = Platform.OS === 'android' ? 'http://10.0.2.2:8080' : 'http://localhost:8080';
const DEFAULT_ANTIGRAVITY_BASE_URL = 'https://api.antigravity.ai/v1';
const DEFAULT_CLOUD_MODEL = 'ag/gemini-3.7-flash-high';

export type ThemeMode = 'dark' | 'light' | 'system';

export interface SettingsState {
  serverUrl: string;
  activeModel: string;
  hapticEnabled: boolean;
  theme: ThemeMode;
  isLoaded: boolean;

  // Cloud & Multi-Account State
  connectionMode: ConnectionMode;
  accounts: AntigravityAccount[];
  activeAccountId: string;
  cloudModel: string;

  // Actions
  setServerUrl: (url: string) => Promise<void>;
  setActiveModel: (model: string) => Promise<void>;
  setHapticEnabled: (enabled: boolean) => Promise<void>;
  setTheme: (theme: ThemeMode) => Promise<void>;
  setConnectionMode: (mode: ConnectionMode) => Promise<void>;
  setCloudModel: (model: string) => Promise<void>;
  addAccount: (account: Omit<AntigravityAccount, 'id'>) => Promise<string>;
  updateAccount: (id: string, updates: Partial<AntigravityAccount>) => Promise<void>;
  deleteAccount: (id: string) => Promise<void>;
  setActiveAccount: (id: string) => Promise<void>;
  getActiveAccount: () => AntigravityAccount | undefined;
  loadSettings: () => Promise<void>;
}

const DEFAULT_ACCOUNT: AntigravityAccount = {
  id: 'default_acc',
  name: 'Antigravity Default',
  apiKey: '',
  baseUrl: DEFAULT_ANTIGRAVITY_BASE_URL,
  defaultModel: DEFAULT_CLOUD_MODEL,
};

const persistState = async (state: SettingsState) => {
  try {
    const payload = {
      serverUrl: state.serverUrl,
      activeModel: state.activeModel,
      hapticEnabled: state.hapticEnabled,
      theme: state.theme,
      connectionMode: state.connectionMode,
      accounts: state.accounts,
      activeAccountId: state.activeAccountId,
      cloudModel: state.cloudModel,
    };
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch (e) {
    console.warn('Failed to save settings to AsyncStorage', e);
  }
};

export const useSettingsStore = create<SettingsState>((set, get) => ({
  serverUrl: DEFAULT_HOST,
  activeModel: 'Antigravity',
  hapticEnabled: true,
  theme: 'dark',
  isLoaded: false,

  connectionMode: 'cloud',
  accounts: [DEFAULT_ACCOUNT],
  activeAccountId: 'default_acc',
  cloudModel: DEFAULT_CLOUD_MODEL,

  setServerUrl: async (url: string) => {
    const cleanUrl = url.trim().replace(/\/+$/, '');
    set({ serverUrl: cleanUrl });
    await persistState(get());
  },

  setActiveModel: async (model: string) => {
    set({ activeModel: model });
    await persistState(get());
  },

  setHapticEnabled: async (enabled: boolean) => {
    set({ hapticEnabled: enabled });
    await persistState(get());
  },

  setTheme: async (theme: ThemeMode) => {
    set({ theme });
    await persistState(get());
  },

  setConnectionMode: async (mode: ConnectionMode) => {
    set({ connectionMode: mode });
    await persistState(get());
  },

  setCloudModel: async (model: string) => {
    set({ cloudModel: model });
    await persistState(get());
  },

  addAccount: async (accData: Omit<AntigravityAccount, 'id'>) => {
    const id = `acc_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    const newAcc: AntigravityAccount = { ...accData, id };
    const newAccounts = [...get().accounts, newAcc];
    set({
      accounts: newAccounts,
      activeAccountId: id,
    });
    await persistState(get());
    return id;
  },

  updateAccount: async (id: string, updates: Partial<AntigravityAccount>) => {
    const newAccounts = get().accounts.map((a) => (a.id === id ? { ...a, ...updates } : a));
    set({ accounts: newAccounts });
    await persistState(get());
  },

  deleteAccount: async (id: string) => {
    const filtered = get().accounts.filter((a) => a.id !== id);
    const newAccounts = filtered.length > 0 ? filtered : [DEFAULT_ACCOUNT];
    const newActiveId =
      get().activeAccountId === id ? newAccounts[0].id : get().activeAccountId;
    set({
      accounts: newAccounts,
      activeAccountId: newActiveId,
    });
    await persistState(get());
  },

  setActiveAccount: async (id: string) => {
    set({ activeAccountId: id });
    await persistState(get());
  },

  getActiveAccount: () => {
    const { accounts, activeAccountId } = get();
    return accounts.find((a) => a.id === activeAccountId) || accounts[0];
  },

  loadSettings: async () => {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        const savedAccounts: AntigravityAccount[] =
          Array.isArray(parsed.accounts) && parsed.accounts.length > 0
            ? parsed.accounts
            : [DEFAULT_ACCOUNT];

        set({
          serverUrl: parsed.serverUrl || DEFAULT_HOST,
          activeModel: parsed.activeModel || 'Antigravity',
          hapticEnabled: parsed.hapticEnabled !== undefined ? parsed.hapticEnabled : true,
          theme: parsed.theme || 'dark',
          connectionMode: parsed.connectionMode || 'cloud',
          accounts: savedAccounts,
          activeAccountId: parsed.activeAccountId || savedAccounts[0].id,
          cloudModel: parsed.cloudModel || DEFAULT_CLOUD_MODEL,
          isLoaded: true,
        });
      } else {
        set({ isLoaded: true });
      }
    } catch (e) {
      set({ isLoaded: true });
    }
  },
}));
