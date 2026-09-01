import { apiRequest } from './apiClient';
import { SystemStatus, ModelsResponse } from '../../types/system';

export async function getSystemStatus(): Promise<SystemStatus> {
  return apiRequest<SystemStatus>('/api/status', {
    method: 'GET',
    timeoutMs: 5000,
  });
}

export async function getModels(): Promise<ModelsResponse> {
  return apiRequest<ModelsResponse>('/api/models', {
    method: 'GET',
    timeoutMs: 8000,
  });
}

export async function selectModel(modelName: string): Promise<{ status: string; model?: string }> {
  return apiRequest<{ status: string; model?: string }>('/api/models/select', {
    method: 'POST',
    body: JSON.stringify({ model: modelName }),
  });
}

export interface RouterStatusResponse {
  status: string;
  running: boolean;
  provider: string;
  base_url: string;
  port: number;
  latency_ms?: number | null;
  message?: string;
}

export async function getRouterStatus(): Promise<RouterStatusResponse> {
  return apiRequest<RouterStatusResponse>('/api/router', {
    method: 'GET',
    timeoutMs: 4000,
  });
}

export async function startRouter(): Promise<RouterStatusResponse> {
  return apiRequest<RouterStatusResponse>('/api/router/start', {
    method: 'POST',
    timeoutMs: 20000,
  });
}
