export interface SystemStatus {
  status: string;
  version: string;
  working_directory?: string;
  llm_enabled?: boolean;
  active_target?: string;
  targets_count?: number;
  tools_count?: number;
  llm_model?: string;
  llm_provider?: string;
  is_running?: boolean;
  active_agents_count?: number;
}

export interface AIModel {
  name: string;
  description: string;
  provider: string;
  is_current: boolean;
}

export interface AIProvider {
  name: string;
  description: string;
  base_url: string;
}

export interface ModelsResponse {
  status: string;
  current_model: string;
  current_provider: string;
  models: AIModel[];
  providers: AIProvider[];
}
