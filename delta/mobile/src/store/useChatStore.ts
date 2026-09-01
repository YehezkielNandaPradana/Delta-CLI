import { create } from 'zustand';
import { ChatMessage } from '../types/chat';
import { AgentStep } from '../types/events';

interface ChatState {
  messages: ChatMessage[];
  activeExecutionId: string | null;
  activeSteps: Record<string, AgentStep>;
  activeStatusText: string;
  isGenerating: boolean;

  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'> & { id?: string; timestamp?: number }) => string;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  appendStreamingText: (text: string) => void;
  startExecution: (executionId?: string) => void;
  finishExecution: () => void;
  updateStep: (step: AgentStep) => void;
  setActiveStatusText: (text: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  activeExecutionId: null,
  activeSteps: {},
  activeStatusText: 'Ready',
  isGenerating: false,

  addMessage: (msg) => {
    const id = msg.id || `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    const timestamp = msg.timestamp || Date.now();
    const newMsg: ChatMessage = {
      ...msg,
      id,
      timestamp,
    };
    set((state) => ({
      messages: [...state.messages, newMsg],
    }));
    return id;
  },

  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    }));
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
    const { activeSteps, messages } = get();
    const stepsArray = Object.values(activeSteps);

    // Attach steps to the last AI message if present
    set((state) => {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.sender === 'delta') {
        last.steps = stepsArray.length > 0 ? stepsArray : undefined;
        last.isStreaming = false;
      }
      return {
        messages: msgs,
        isGenerating: false,
        activeStatusText: 'Ready',
        activeExecutionId: null,
      };
    });
  },

  updateStep: (step) => {
    set((state) => {
      const steps = { ...state.activeSteps };
      steps[step.id] = { ...(steps[step.id] || {}), ...step };
      return { activeSteps: steps };
    });
  },

  setActiveStatusText: (text) => set({ activeStatusText: text }),

  clearMessages: () =>
    set({
      messages: [],
      activeSteps: {},
      activeExecutionId: null,
      isGenerating: false,
      activeStatusText: 'Ready',
    }),
}));
