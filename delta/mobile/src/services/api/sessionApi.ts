import { apiRequest } from './apiClient';
import { ConversationHistoryItem } from '../../types/chat';

export interface HistoryResponse {
  status: string;
  history: ConversationHistoryItem[];
  message?: string;
}

export async function getConversationHistory(limit: number = 50): Promise<HistoryResponse> {
  return apiRequest<HistoryResponse>(`/api/history?limit=${limit}`, {
    method: 'GET',
    timeoutMs: 8000,
  });
}

export async function clearConversationHistory(): Promise<{ status: string; message?: string }> {
  return apiRequest<{ status: string; message?: string }>('/api/history/clear', {
    method: 'POST',
  });
}

export async function deleteHistoryItem(id: number): Promise<{ status: string; deleted?: boolean; message?: string }> {
  return apiRequest<{ status: string; deleted?: boolean; message?: string }>('/api/history/delete', {
    method: 'POST',
    body: JSON.stringify({ id }),
  });
}
