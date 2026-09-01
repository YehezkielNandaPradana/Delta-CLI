export interface AntigravityAccount {
  id: string;
  name: string;
  apiKey: string;
  baseUrl: string;
  defaultModel: string;
}

export type ConnectionMode = 'cloud' | 'local';
