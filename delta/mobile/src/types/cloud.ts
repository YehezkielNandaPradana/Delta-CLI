export interface AntigravityAccount {
  id: string;
  name: string;
  apiKey: string;
  baseUrl: string;
  defaultModel: string;
  accountType?: 'google' | 'antigravity' | 'custom';
  tier?: 'pro' | 'flash' | 'standard';
  availableModels?: string[];
}

export type ConnectionMode = 'cloud' | 'local' | 'tunnel' | 'telegram';
