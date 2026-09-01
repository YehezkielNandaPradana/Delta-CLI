import { AgentEvent } from '../../types/events';
import { useConnectionStore } from '../../store/useConnectionStore';
import { useSettingsStore } from '../../store/useSettingsStore';

export class SSERealtimeClient {
  private url: string = '';
  private isRunning: boolean = false;
  private reconnectTimer: any = null;
  private abortController: AbortController | null = null;
  private listeners: Set<(event: AgentEvent) => void> = new Set();
  private retryCount: number = 0;

  constructor() {}

  public subscribe(callback: (event: AgentEvent) => void): () => void {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.connect();
  }

  public stop(): void {
    this.isRunning = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    useConnectionStore.getState().setStatus('disconnected');
  }

  public restart(): void {
    this.stop();
    this.start();
  }

  private emit(event: AgentEvent): void {
    this.listeners.forEach((listener) => {
      try {
        listener(event);
      } catch (err) {
        console.error('SSE listener error:', err);
      }
    });
  }

  private async connect(): Promise<void> {
    if (!this.isRunning) return;

    const { serverUrl } = useSettingsStore.getState();
    const base = serverUrl.replace(/\/+$/, '');
    this.url = `${base}/api/events`;

    useConnectionStore.getState().setStatus('connecting');
    this.abortController = new AbortController();

    try {
      const response = await fetch(this.url, {
        headers: {
          Accept: 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`SSE HTTP error: ${response.status}`);
      }

      useConnectionStore.getState().setStatus('connected');
      this.retryCount = 0;

      // Handle stream body via text reader or chunking
      const reader = response.body?.getReader?.();

      if (reader) {
        const decoder = new TextDecoder();
        let buffer = '';

        while (this.isRunning) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const block of lines) {
            this.parseBlock(block);
          }
        }
      } else {
        // Fallback for environments where body.getReader() is not polyfilled (XHR stream)
        const text = await response.text();
        const blocks = text.split('\n\n');
        for (const block of blocks) {
          this.parseBlock(block);
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError' && this.isRunning) {
        useConnectionStore.getState().setStatus('disconnected');
        this.scheduleReconnect();
      }
    }
  }

  private parseBlock(block: string): void {
    const trimmed = block.trim();
    if (!trimmed || trimmed.startsWith(':')) {
      // Ping / comment line
      if (trimmed.startsWith(': ping')) {
        useConnectionStore.getState().setLastPing(Date.now());
      }
      return;
    }

    const match = trimmed.match(/^data:\s*(.+)$/m);
    if (match && match[1]) {
      try {
        const json = JSON.parse(match[1]);
        if (json.type === 'ping') {
          useConnectionStore.getState().setLastPing(Date.now());
        } else if (json.type === 'workspace_info') {
          useConnectionStore.getState().setSystemInfo({
            workingDirectory: json.working_directory,
          });
        } else {
          this.emit(json as AgentEvent);
        }
      } catch (e) {
        // Ignored invalid json
      }
    }
  }

  private scheduleReconnect(): void {
    if (!this.isRunning) return;
    this.retryCount++;
    const delay = Math.min(1000 * Math.pow(1.5, this.retryCount), 10000);
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }
}

export const sseClient = new SSERealtimeClient();
