import { AgentStep } from './events';

export type MessageSender = 'user' | 'delta';

export interface ChatMessage {
  id: string;
  sender: MessageSender;
  text: string;
  timestamp: number;
  executionId?: string;
  steps?: AgentStep[];
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface ConversationHistoryItem {
  id: string | number;
  timestamp: string | number;
  user_input?: string;
  ai_response?: string;
  command?: string;
  result?: string;
  target?: string;
  duration?: number;
}
