import { useSettingsStore } from '../../store/useSettingsStore';

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function apiRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { serverUrl } = useSettingsStore.getState();
  const base = serverUrl.replace(/\/+$/, '');
  const url = `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const { timeoutMs = 20000, ...customConfig } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(options.headers as Record<string, string>),
  };

  try {
    const response = await fetch(url, {
      ...customConfig,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errMessage = `HTTP error ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson.message) errMessage = errJson.message;
        else if (errJson.error) errMessage = errJson.error;
      } catch (_) {}
      throw new Error(errMessage);
    }

    const data = await response.json();
    return data as T;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Delta server connection timed out.');
    }
    throw error;
  }
}
