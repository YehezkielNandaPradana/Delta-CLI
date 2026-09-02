export interface NoteFolder {
  id: string;
  name: string;
  icon?: string;
  createdAt: number;
  updatedAt?: number;
}

export interface Note {
  id: string;
  title: string;
  content: string;
  folderId?: string | null;
  isPinned: boolean;
  tags?: string[];
  createdAt: number;
  updatedAt: number;
  syncStatus?: 'synced' | 'pending' | 'local';
}

export type NoteAIAction = 'ask' | 'summarize' | 'improve' | 'expand' | 'tasks';
