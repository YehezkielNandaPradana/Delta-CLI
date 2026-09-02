import { create } from 'zustand';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

interface ConnectionState {
  status: ConnectionStatus;
  isConnected: boolean;
  isEngineRunning: boolean;
  isRouterRunning: boolean;
  activeTarget: string;
  workingDirectory: string;
  lastPing: number | null;
  errorMessage: string | null;
  setStatus: (status: ConnectionStatus) => void;
  setEngineRunning: (running: boolean) => void;
  setIsRouterRunning: (running: boolean) => void;
  setSystemInfo: (info: { workingDirectory?: string; activeTarget?: string }) => void;
  setLastPing: (timestamp: number) => void;
  setError: (msg: string | null) => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  status: 'disconnected',
  isConnected: false,
  isEngineRunning: false,
  isRouterRunning: true,
  activeTarget: '',
  workingDirectory: '',
  lastPing: null,
  errorMessage: null,

  setStatus: (status: ConnectionStatus) =>
    set({
      status,
      isConnected: status === 'connected',
      errorMessage: status === 'connected' ? null : undefined,
    }),
  setEngineRunning: (running: boolean) => set({ isEngineRunning: running }),
  setIsRouterRunning: (running: boolean) => set({ isRouterRunning: running }),
  setSystemInfo: (info) =>
    set((state) => ({
      workingDirectory: info.workingDirectory !== undefined ? info.workingDirectory : state.workingDirectory,
      activeTarget: info.activeTarget !== undefined ? info.activeTarget : state.activeTarget,
    })),
  setLastPing: (timestamp: number) => set({ lastPing: timestamp }),
  setError: (msg: string | null) => set({ errorMessage: msg, status: msg ? 'error' : 'disconnected' }),
}));
