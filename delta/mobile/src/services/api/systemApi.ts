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
  const { connectionMode, routerHostUrl, serverUrl } = useSettingsStore.getState();

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

  // Check Termux / PRoot / local candidates port 20128
  const candidateUrls = [
    routerHostUrl ? routerHostUrl.replace(/\/+$/, '') : '',
    'http://127.0.0.1:20128',
    'http://localhost:20128',
    'http://192.168.1.6:20128',
  ].filter(Boolean);

  for (const host of candidateUrls) {
    try {
      const cleanHost = host.replace(/\/v1\/?$/, '');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1200);
      const res = await fetch(`${cleanHost}/v1/models`, {
        method: 'GET',
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (res.ok) {
        return {
          status: 'ok',
          running: true,
          provider: '9router-local',
          base_url: `${cleanHost}/v1`,
          port: 20128,
          latency_ms: 5,
        };
      }
    } catch (_) {}
  }

  return apiRequest<RouterStatusResponse>('/api/router', {
    method: 'GET',
    timeoutMs: 4000,
  });
}

export async function test9RouterPing(targetUrl?: string, customApiKey?: string): Promise<{
  success: boolean;
  latencyMs: number;
  modelsCount: number;
  url: string;
  error?: string;
}> {
  const { routerHostUrl, serverUrl, getActiveAccount } = useSettingsStore.getState();
  const activeAccount = getActiveAccount();
  const apiKey = customApiKey || activeAccount?.apiKey || '';

  let urlToTest = (targetUrl || routerHostUrl || '').trim();
  if (!urlToTest) {
    try {
      if (serverUrl && !serverUrl.includes('localhost') && !serverUrl.includes('127.0.0.1')) {
        const u = new URL(serverUrl);
        urlToTest = `http://${u.hostname}:20128`;
      }
    } catch (_) {}
  }
  if (!urlToTest) {
    urlToTest = 'https://rurpq7a.abc-tunnel.us/v1';
  }

  const cleanUrl = urlToTest.replace(/\/+$/, '').replace(/\/v1\/?$/, '');
  const endpoint = `${cleanUrl}/v1/models`;

  const startT = Date.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    const headers: Record<string, string> = {};
    if (apiKey) {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }
    const res = await fetch(endpoint, {
      method: 'GET',
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    const latencyMs = Date.now() - startT;

    if (res.ok) {
      const json = await res.json();
      const count = Array.isArray(json?.data) ? json.data.length : 0;
      return {
        success: true,
        latencyMs,
        modelsCount: count,
        url: cleanUrl,
      };
    }
    return {
      success: false,
      latencyMs,
      modelsCount: 0,
      url: cleanUrl,
      error: `HTTP ${res.status}`,
    };
  } catch (err: any) {
    return {
      success: false,
      latencyMs: Date.now() - startT,
      modelsCount: 0,
      url: cleanUrl,
      error: err.name === 'AbortError' ? 'Connection timed out (8s)' : err.message || 'Unreachable',
    };
  }
}

export async function startRouter(): Promise<RouterStatusResponse> {
  return apiRequest<RouterStatusResponse>('/api/router/start', {
    method: 'POST',
    timeoutMs: 20000,
  });
}

export interface TunnelStatusResponse {
  status: string;
  running: boolean;
  url: string | null;
  available: boolean;
  message?: string;
}

export async function getTunnelStatus(): Promise<TunnelStatusResponse> {
  return apiRequest<TunnelStatusResponse>('/api/tunnel', {
    method: 'GET',
    timeoutMs: 5000,
  });
}

export async function startTunnel(port: number = 8080): Promise<TunnelStatusResponse> {
  return apiRequest<TunnelStatusResponse>('/api/tunnel/start', {
    method: 'POST',
    body: JSON.stringify({ port }),
    timeoutMs: 30000,
  });
}

export async function stopTunnel(): Promise<{ status: string; stopped: boolean }> {
  return apiRequest<{ status: string; stopped: boolean }>('/api/tunnel/stop', {
    method: 'POST',
    timeoutMs: 10000,
  });
}

export interface TunnelLogEntry {
  timestamp: string;
  time: number;
  level: string;
  message: string;
}

export interface TunnelLogsResponse {
  status: string;
  tunnel: TunnelStatusResponse;
  logs: TunnelLogEntry[];
}

export async function getTunnelLogs(limit: number = 100): Promise<TunnelLogsResponse> {
  return apiRequest<TunnelLogsResponse>(`/api/tunnel/logs?limit=${limit}`, {
    method: 'GET',
    timeoutMs: 5000,
  });
}
