import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatMessage, ChatSession } from '../types/chat';
import { AgentStep } from '../types/events';

const STORAGE_KEY = '@delta_chat_sessions';

interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string;
  messages: ChatMessage[];
  activeExecutionId: string | null;
  activeSteps: Record<string, AgentStep>;
  activeStatusText: string;
  isGenerating: boolean;
  isLoaded: boolean;

  loadSessions: () => Promise<void>;
  createSession: () => string;
  switchSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => Promise<void>;
  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'> & { id?: string; timestamp?: number }) => string;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  deleteMessage: (id: string) => void;
  appendStreamingText: (text: string) => void;
  startExecution: (executionId?: string) => void;
  finishExecution: () => void;
  updateStep: (step: AgentStep) => void;
  setActiveStatusText: (text: string) => void;
  clearMessages: () => void;
}

const persistSessions = async (sessions: ChatSession[], currentId: string) => {
  try {
    await AsyncStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ sessions, currentSessionId: currentId })
    );
  } catch (e) {
    console.warn('Failed to save chat sessions', e);
  }
};

const createInitialSession = (): ChatSession => {
  const id = `sess_${Date.now()}`;
  return {
    id,
    title: 'Obrolan Baru',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
};

export const useChatStore = create<ChatState>((set, get) => {
  const defaultSession = createInitialSession();

  return {
    sessions: [defaultSession],
    currentSessionId: defaultSession.id,
    messages: [],
    activeExecutionId: null,
    activeSteps: {},
    activeStatusText: 'Ready',
    isGenerating: false,
    isLoaded: false,

    loadSessions: async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          const sessions: ChatSession[] = Array.isArray(parsed.sessions) && parsed.sessions.length > 0
            ? parsed.sessions
            : [createInitialSession()];
          const currentId = parsed.currentSessionId || sessions[0].id;
          const currentSession = sessions.find((s) => s.id === currentId) || sessions[0];

          set({
            sessions,
            currentSessionId: currentSession.id,
            messages: currentSession.messages || [],
            isLoaded: true,
          });
          return;
        }
      } catch (_) {}
      set({ isLoaded: true });
    },

    createSession: () => {
      const newSession = createInitialSession();
      const updated = [newSession, ...get().sessions];
      set({
        sessions: updated,
        currentSessionId: newSession.id,
        messages: [],
        activeSteps: {},
        activeExecutionId: null,
        isGenerating: false,
        activeStatusText: 'Ready',
      });
      persistSessions(updated, newSession.id);
      return newSession.id;
    },

    switchSession: (sessionId: string) => {
      const target = get().sessions.find((s) => s.id === sessionId);
      if (target) {
        set({
          currentSessionId: target.id,
          messages: target.messages || [],
          activeSteps: {},
          activeExecutionId: null,
          isGenerating: false,
          activeStatusText: 'Ready',
        });
        persistSessions(get().sessions, target.id);
      }
    },

    deleteSession: async (sessionId: string) => {
      const remaining = get().sessions.filter((s) => s.id !== sessionId);
      const safeRemaining = remaining.length > 0 ? remaining : [createInitialSession()];
      const nextId = safeRemaining[0].id;
      const nextMessages = safeRemaining[0].messages || [];

      set({
        sessions: safeRemaining,
        currentSessionId: nextId,
        messages: nextMessages,
      });
      await persistSessions(safeRemaining, nextId);
    },

    addMessage: (msg) => {
      const id = msg.id || `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
      const timestamp = msg.timestamp || Date.now();
      const newMsg: ChatMessage = {
        ...msg,
        id,
        timestamp,
      };

      const currentMessages = [...get().messages, newMsg];
      const { currentSessionId, sessions } = get();

      // Generate title from first user message
      const updatedSessions = sessions.map((s) => {
        if (s.id === currentSessionId) {
          let title = s.title;
          if (s.title === 'Obrolan Baru' && msg.sender === 'user' && msg.text) {
            title = msg.text.slice(0, 28) + (msg.text.length > 28 ? '...' : '');
          }
          return {
            ...s,
            title,
            messages: currentMessages,
            updatedAt: Date.now(),
          };
        }
        return s;
      });

      set({
        messages: currentMessages,
        sessions: updatedSessions,
      });

      persistSessions(updatedSessions, currentSessionId);
      return id;
    },

    updateMessage: (id, updates) => {
      const msgs = get().messages.map((m) => (m.id === id ? { ...m, ...updates } : m));
      const { currentSessionId, sessions } = get();
      const updatedSessions = sessions.map((s) =>
        s.id === currentSessionId ? { ...s, messages: msgs, updatedAt: Date.now() } : s
      );

      set({
        messages: msgs,
        sessions: updatedSessions,
      });
      persistSessions(updatedSessions, currentSessionId);
    },

    deleteMessage: (id) => {
      const msgs = get().messages.filter((m) => m.id !== id);
      const { currentSessionId, sessions } = get();
      const updatedSessions = sessions.map((s) =>
        s.id === currentSessionId ? { ...s, messages: msgs, updatedAt: Date.now() } : s
      );

      set({
        messages: msgs,
        sessions: updatedSessions,
      });
      persistSessions(updatedSessions, currentSessionId);
    },

    appendStreamingText: (text) => {
      set((state) => {
        const msgs = [...state.messages];
        const last = msgs[msgs.length - 1];
        if (last && last.sender === 'delta' && last.isStreaming) {
          last.text = (last.text || '') + text;
          return { messages: msgs };
        } else {
          const id = `msg_${Date.now()}`;
          msgs.push({
            id,
            sender: 'delta',
            text,
            timestamp: Date.now(),
            isStreaming: true,
          });
          return { messages: msgs };
        }
      });
    },

    startExecution: (executionId) => {
      const execId = executionId || `exec_${Date.now()}`;
      set({
        activeExecutionId: execId,
        activeSteps: {},
        activeStatusText: 'Thinking...',
        isGenerating: true,
      });
    },

    finishExecution: () => {
      const { activeSteps, messages, currentSessionId, sessions } = get();
      const stepsArray = Object.values(activeSteps);

      const msgs = [...messages];
      const last = msgs[msgs.length - 1];
      if (last && last.sender === 'delta') {
        last.steps = stepsArray.length > 0 ? stepsArray : undefined;
        last.isStreaming = false;
      }

      const updatedSessions = sessions.map((s) =>
        s.id === currentSessionId ? { ...s, messages: msgs, updatedAt: Date.now() } : s
      );

      set({
        messages: msgs,
        sessions: updatedSessions,
        isGenerating: false,
        activeStatusText: 'Ready',
        activeExecutionId: null,
      });

      persistSessions(updatedSessions, currentSessionId);
    },

    updateStep: (step) => {
      set((state) => {
        const steps = { ...state.activeSteps };
        steps[step.id] = { ...(steps[step.id] || {}), ...step };
        return { activeSteps: steps };
      });
    },

    setActiveStatusText: (text) => set({ activeStatusText: text }),

    clearMessages: () => {
      const { currentSessionId, sessions } = get();
      const updatedSessions = sessions.map((s) =>
        s.id === currentSessionId ? { ...s, messages: [], updatedAt: Date.now() } : s
      );

      set({
        messages: [],
        sessions: updatedSessions,
        activeSteps: {},
        activeExecutionId: null,
        isGenerating: false,
        activeStatusText: 'Ready',
      });
      persistSessions(updatedSessions, currentSessionId);
    },
  };
});
