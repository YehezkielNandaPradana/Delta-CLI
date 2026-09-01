import { apiRequest } from './apiClient';
import { useSettingsStore } from '../../store/useSettingsStore';
import { embedded9Router } from '../router/embeddedRouterEngine';

export interface ChatResponse {
  output?: string;
  response?: string;
  is_task?: boolean;
  task_id?: string | null;
  error?: string;
}

export async function sendChatMessage(
  message: string,
  executionId?: string
): Promise<ChatResponse> {
  const { connectionMode, cloudModel, activeModel, getActiveAccount } = useSettingsStore.getState();

  if (connectionMode === 'cloud') {
    const selectedModel = cloudModel || activeModel || 'AntigravityCombo';
    const activeAccount = getActiveAccount();
    return embedded9Router.routeCompletion(message, selectedModel, activeAccount);
  }

  return apiRequest<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      command: message,
      prompt: message,
      message: message,
      execution_id: executionId,
    }),
  });
}

export async function cancelExecution(): Promise<{ status: string; message?: string }> {
  const { connectionMode } = useSettingsStore.getState();
  if (connectionMode === 'cloud') {
    return { status: 'cancelled', message: 'Direct request aborted' };
  }

  return apiRequest<{ status: string; message?: string }>('/api/cancel', {
    method: 'POST',
  });
}
