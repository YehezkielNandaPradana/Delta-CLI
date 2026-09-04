import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { AntigravityAccount, ConnectionMode } from '../types/cloud';

const STORAGE_KEY = '@delta_settings';

// Sensible defaults based on execution platform
const DEFAULT_HOST = Platform.OS === 'android' ? 'http://192.168.1.6:8000' : 'http://localhost:8000';
const DEFAULT_ROUTER_HOST = 'https://rurpq7a.abc-tunnel.us/v1';
const DEFAULT_9ROUTER_KEY = 'sk-13295da0418e0160-d4rojh-3ca28d24';
const DEFAULT_CLOUD_MODEL = 'ag/gemini-3.7-flash-high';

const DEFAULT_9ROUTER_ACCOUNT: AntigravityAccount = {
  id: 'acc_9router_default',
  name: '9Router Tunnel Gateway',
  apiKey: DEFAULT_9ROUTER_KEY,
  baseUrl: DEFAULT_ROUTER_HOST,
  defaultModel: DEFAULT_CLOUD_MODEL,
  accountType: 'antigravity',
  tier: 'pro',
};

export type ThemeMode = 'dark' | 'light' | 'system';

export interface SettingsState {
  serverUrl: string;
  tunnelUrl: string;
  routerHostUrl: string;
  activeModel: string;
  hapticEnabled: boolean;
  theme: ThemeMode;
  isLoaded: boolean;

  // Cloud & Multi-Account State
  connectionMode: ConnectionMode;
  accounts: AntigravityAccount[];
  activeAccountId: string;
  cloudModel: string;

  // Telegram Hermes Bot Integration
  telegramBotToken: string;
  telegramChatId: string;
  telegramAutoForward: boolean;

  // Actions
  setServerUrl: (url: string) => Promise<void>;
  setTunnelUrl: (url: string) => Promise<void>;
  setRouterHostUrl: (url: string) => Promise<void>;
  setActiveModel: (model: string) => Promise<void>;
  setHapticEnabled: (enabled: boolean) => Promise<void>;
  setTheme: (theme: ThemeMode) => Promise<void>;
  setConnectionMode: (mode: ConnectionMode) => Promise<void>;
  setCloudModel: (model: string) => Promise<void>;
  setTelegramBotToken: (token: string) => Promise<void>;
  setTelegramChatId: (chatId: string) => Promise<void>;
  setTelegramAutoForward: (enabled: boolean) => Promise<void>;
  addAccount: (account: Omit<AntigravityAccount, 'id'>) => Promise<string>;
  updateAccount: (id: string, updates: Partial<AntigravityAccount>) => Promise<void>;
  deleteAccount: (id: string) => Promise<void>;
  clearAccountKey: (id: string) => Promise<void>;
  setActiveAccount: (id: string) => Promise<void>;
  getActiveAccount: () => AntigravityAccount | undefined;
  loadSettings: () => Promise<void>;
}

const persistState = async (state: SettingsState) => {
  try {
    const payload = {
      serverUrl: state.serverUrl,
      tunnelUrl: state.tunnelUrl,
      routerHostUrl: state.routerHostUrl,
      activeModel: state.activeModel,
      hapticEnabled: state.hapticEnabled,
      theme: state.theme,
      connectionMode: state.connectionMode,
      accounts: state.accounts,
      activeAccountId: state.activeAccountId,
      cloudModel: state.cloudModel,
      telegramBotToken: state.telegramBotToken,
      telegramChatId: state.telegramChatId,
      telegramAutoForward: state.telegramAutoForward,
    };
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch (e) {
    console.warn('Failed to save settings to AsyncStorage', e);
  }
};

export const useSettingsStore = create<SettingsState>((set, get) => ({
  serverUrl: DEFAULT_HOST,
  tunnelUrl: DEFAULT_ROUTER_HOST,
  routerHostUrl: DEFAULT_ROUTER_HOST,
  activeModel: 'ag/gemini-3.7-flash-high',
  hapticEnabled: true,
  theme: 'dark',
  isLoaded: false,

  connectionMode: 'cloud',
  accounts: [DEFAULT_9ROUTER_ACCOUNT],
  activeAccountId: DEFAULT_9ROUTER_ACCOUNT.id,
  cloudModel: DEFAULT_CLOUD_MODEL,

  telegramBotToken: '',
  telegramChatId: '',
  telegramAutoForward: false,

  setServerUrl: async (url: string) => {
    const cleanUrl = url.trim().replace(/\/+$/, '');
    set({ serverUrl: cleanUrl });
    await persistState(get());
  },

  setTunnelUrl: async (url: string) => {
    const cleanUrl = url.trim().replace(/\/+$/, '');
    set({ tunnelUrl: cleanUrl });
    await persistState(get());
  },

  setRouterHostUrl: async (url: string) => {
    const cleanUrl = url.trim().replace(/\/+$/, '');
    set({ routerHostUrl: cleanUrl });
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

  setTelegramBotToken: async (token: string) => {
    set({ telegramBotToken: token.trim() });
    await persistState(get());
  },

  setTelegramChatId: async (chatId: string) => {
    set({ telegramChatId: chatId.trim() });
    await persistState(get());
  },

  setTelegramAutoForward: async (enabled: boolean) => {
    set({ telegramAutoForward: enabled });
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
    const newActiveId =
      get().activeAccountId === id
        ? (filtered.length > 0 ? filtered[0].id : '')
        : get().activeAccountId;
    set({
      accounts: filtered,
      activeAccountId: newActiveId,
    });
    await persistState(get());
  },

  clearAccountKey: async (id: string) => {
    const updated = get().accounts.map((a) =>
      a.id === id ? { ...a, apiKey: '', tier: undefined } : a
    );
    set({ accounts: updated });
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
          Array.isArray(parsed.accounts) ? parsed.accounts : [];

        set({
          serverUrl: parsed.serverUrl || DEFAULT_HOST,
          tunnelUrl: parsed.tunnelUrl || DEFAULT_ROUTER_HOST,
          routerHostUrl: parsed.routerHostUrl || DEFAULT_ROUTER_HOST,
          activeModel: parsed.activeModel || 'ag/gemini-3.7-flash-high',
          hapticEnabled: parsed.hapticEnabled !== undefined ? parsed.hapticEnabled : true,
          theme: parsed.theme || 'dark',
          connectionMode: parsed.connectionMode || 'cloud',
          accounts: savedAccounts.length > 0 ? savedAccounts : [DEFAULT_9ROUTER_ACCOUNT],
          activeAccountId: parsed.activeAccountId || (savedAccounts[0]?.id || DEFAULT_9ROUTER_ACCOUNT.id),
          cloudModel: parsed.cloudModel || DEFAULT_CLOUD_MODEL,
          telegramBotToken: parsed.telegramBotToken || '',
          telegramChatId: parsed.telegramChatId || '',
          telegramAutoForward: parsed.telegramAutoForward !== undefined ? parsed.telegramAutoForward : false,
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
