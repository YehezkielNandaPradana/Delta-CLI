import { apiRequest } from './apiClient';
import { SystemStatus, ModelsResponse } from '../../types/system';
import { useSettingsStore } from '../../store/useSettingsStore';

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
  const { connectionMode } = useSettingsStore.getState();

  // If running in pure Cloud mode, report 9Router as active directly
  if (connectionMode === 'cloud') {
    return {
      status: 'ok',
      running: true,
      provider: '9router-embedded',
      base_url: 'http://localhost:20128/v1',
      port: 20128,
      latency_ms: 1,
    };
  }

  // Check Termux / local port 20128 directly
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch('http://127.0.0.1:20128/v1/models', {
      method: 'GET',
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (res.ok) {
      return {
        status: 'ok',
        running: true,
        provider: '9router-local',
        base_url: 'http://127.0.0.1:20128/v1',
        port: 20128,
        latency_ms: 5,
      };
    }
  } catch (_) {}

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
