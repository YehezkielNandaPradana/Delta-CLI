export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type StepKind =
  | 'root'
  | 'understand'
  | 'context'
  | 'search'
  | 'read'
  | 'analyze'
  | 'plan'
  | 'tool'
  | 'command'
  | 'edit'
  | 'create'
  | 'delete'
  | 'test'
  | 'verify'
  | 'result';

export interface AgentStep {
  id: string;
  task_id?: string;
  execution_id?: string;
  parent_id?: string | null;
  kind?: StepKind;
  label?: string;
  status: StepStatus;
  created_at?: number;
  started_at?: number | null;
  completed_at?: number | null;
  duration_ms?: number | null;
  tool_name?: string | null;
  file_path?: string | null;
  command?: string | null;
  diff_stats?: { added?: number; removed?: number } | null;
  error?: string | null;
  output_preview?: string | null;
  metadata?: Record<string, any>;
}

export type EventType =
  | 'agent_start'
  | 'agent_thinking'
  | 'agent_status'
  | 'agent_complete'
  | 'agent_step_created'
  | 'agent_step_started'
  | 'agent_step_progress'
  | 'agent_step_completed'
  | 'agent_step_failed'
  | 'agent_step_cancelled'
  | 'task_created'
  | 'task_started'
  | 'task_completed'
  | 'task_failed'
  | 'tool_start'
  | 'tool_progress'
  | 'tool_result'
  | 'file_read'
  | 'file_write'
  | 'file_update'
  | 'file_created'
  | 'file_deleted'
  | 'diff_generated'
  | 'command_start'
  | 'command_output'
  | 'command_completed'
  | 'test_start'
  | 'test_result'
  | 'diagnostic'
  | 'error'
  | 'message_delta'
  | 'message_complete'
  | 'agent_message'
  | 'response'
  | 'ping'
  | 'workspace_info';

export interface AgentEvent {
  type: EventType | string;
  timestamp?: number;
  event_id?: string;
  sequence?: number;
  step_id?: string | null;
  execution_id?: string;
  agent_id?: string;
  session_id?: string;
  status_text?: string;
  content?: string;
  message?: string;
  output?: any;
  tool?: string;
  payload?: {
    step?: AgentStep;
    [key: string]: any;
  };
  working_directory?: string;
  duration_ms?: number;
}
