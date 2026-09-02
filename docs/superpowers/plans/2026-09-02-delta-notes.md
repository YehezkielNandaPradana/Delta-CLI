# Delta Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a local-first Delta Notes ecosystem in Delta Mobile (React Native / Expo), integrated with navigation, chat message actions, and Delta AI Agent tools/actions.

**Architecture:** Create `useNotesStore` using Zustand & AsyncStorage. Add `notes` tab into `FluidBottomBar` and Expo Router. Build liquid glass note list, search, folder filter, and a responsive note editor with auto-save and markdown preview. Add AI actions (Ask Delta, Summarize, Improve, Expand, Tasks) and Agent tools (`create_note`, `search_notes`, `read_note`, etc.). Wire "Save as Note" on Chat messages.

**Tech Stack:** React Native / Expo SDK 51, TypeScript, Zustand, AsyncStorage, Expo Vector Icons.

**Spec:** `docs/superpowers/specs/2026-09-02-delta-notes-design.md`

## Global Constraints
- Target platform: iOS, Android, Web (Expo)
- Storage keys: `@delta_notes`, `@delta_folders`
- Design aesthetic: Liquid Glass / Cyberpunk minimalist (matching `src/theme/theme.ts`)
- Auto-save debounce: 400ms

---

### Task 1: Notes Data Types and Store Implementation

**Files:**
- Create: `delta/mobile/src/types/notes.ts`
- Create: `delta/mobile/src/store/useNotesStore.ts`
- Create: `delta/mobile/tests/notes_store.test.ts`

**Interfaces:**
- Consumes: `@react-native-async-storage/async-storage`, `zustand`
- Produces: `Note`, `NoteFolder`, `NoteAIAction`, `useNotesStore`

- [ ] **Step 1: Write tests for `useNotesStore` CRUD, folders, pin, and search**

Create `delta/mobile/tests/notes_store.test.ts`:
```typescript
import { useNotesStore } from '../src/store/useNotesStore';

describe('useNotesStore', () => {
  beforeEach(() => {
    useNotesStore.setState({
      notes: [],
      folders: [
        { id: 'f_projects', name: 'Projects', createdAt: 1000 },
        { id: 'f_learning', name: 'Learning', createdAt: 1000 },
        { id: 'f_ideas', name: 'Ideas', createdAt: 1000 },
        { id: 'f_personal', name: 'Personal', createdAt: 1000 },
      ],
      selectedFolderId: null,
      searchQuery: '',
      activeNoteId: null,
      isSaving: false,
      lastSavedAt: null,
    });
  });

  test('should create, update, and delete note', async () => {
    const note = await useNotesStore.getState().createNote({
      title: 'Initial Note',
      content: 'Hello Delta',
      folderId: 'f_ideas',
    });

    expect(note.id).toBeDefined();
    expect(useNotesStore.getState().notes.length).toBe(1);
    expect(useNotesStore.getState().notes[0].title).toBe('Initial Note');

    await useNotesStore.getState().updateNote(note.id, { title: 'Updated Title' });
    expect(useNotesStore.getState().notes[0].title).toBe('Updated Title');

    await useNotesStore.getState().deleteNote(note.id);
    expect(useNotesStore.getState().notes.length).toBe(0);
  });

  test('should toggle pin and move note between folders', async () => {
    const note = await useNotesStore.getState().createNote({
      title: 'Pinned Note',
      content: 'Content',
    });

    expect(note.isPinned).toBe(false);
    await useNotesStore.getState().togglePin(note.id);
    expect(useNotesStore.getState().notes[0].isPinned).toBe(true);

    await useNotesStore.getState().moveNote(note.id, 'f_learning');
    expect(useNotesStore.getState().notes[0].folderId).toBe('f_learning');
  });

  test('should create and delete custom folder without deleting notes', async () => {
    const folder = await useNotesStore.getState().createFolder('Security Audits');
    expect(folder.id).toBeDefined();
    expect(useNotesStore.getState().folders.some(f => f.name === 'Security Audits')).toBe(true);

    const note = await useNotesStore.getState().createNote({
      title: 'Audit Report',
      content: 'Vuln summary',
      folderId: folder.id,
    });

    await useNotesStore.getState().deleteFolder(folder.id);
    // Note should have folderId reset to null/unassigned
    const updatedNote = useNotesStore.getState().notes.find(n => n.id === note.id);
    expect(updatedNote?.folderId).toBeNull();
  });
});
```

- [ ] **Step 2: Create `delta/mobile/src/types/notes.ts`**

```typescript
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
```

- [ ] **Step 3: Implement `delta/mobile/src/store/useNotesStore.ts`**

```typescript
import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Note, NoteFolder } from '../types/notes';

const STORAGE_KEY_NOTES = '@delta_notes';
const STORAGE_KEY_FOLDERS = '@delta_folders';

const DEFAULT_FOLDERS: NoteFolder[] = [
  { id: 'f_projects', name: 'Projects', icon: 'briefcase', createdAt: Date.now() },
  { id: 'f_learning', name: 'Learning', icon: 'book', createdAt: Date.now() },
  { id: 'f_ideas', name: 'Ideas', icon: 'bulb', createdAt: Date.now() },
  { id: 'f_personal', name: 'Personal', icon: 'person', createdAt: Date.now() },
];

interface NotesState {
  notes: Note[];
  folders: NoteFolder[];
  selectedFolderId: string | null;
  searchQuery: string;
  activeNoteId: string | null;
  isSaving: boolean;
  lastSavedAt: number | null;
  isLoading: boolean;

  loadNotes: () => Promise<void>;
  createNote: (initial?: Partial<Note>) => Promise<Note>;
  updateNote: (id: string, updates: Partial<Note>) => Promise<void>;
  deleteNote: (id: string) => Promise<void>;
  togglePin: (id: string) => Promise<void>;
  moveNote: (id: string, folderId: string | null) => Promise<void>;
  duplicateNote: (id: string) => Promise<Note | null>;
  createFolder: (name: string, icon?: string) => Promise<NoteFolder>;
  renameFolder: (id: string, name: string) => Promise<void>;
  deleteFolder: (id: string) => Promise<void>;
  setSearchQuery: (query: string) => void;
  setSelectedFolder: (folderId: string | null) => void;
  setActiveNoteId: (id: string | null) => void;
  getFilteredNotes: () => Note[];
}

export const useNotesStore = create<NotesState>((set, get) => ({
  notes: [],
  folders: DEFAULT_FOLDERS,
  selectedFolderId: null,
  searchQuery: '',
  activeNoteId: null,
  isSaving: false,
  lastSavedAt: null,
  isLoading: false,

  loadNotes: async () => {
    try {
      set({ isLoading: true });
      const [savedNotes, savedFolders] = await Promise.all([
        AsyncStorage.getItem(STORAGE_KEY_NOTES),
        AsyncStorage.getItem(STORAGE_KEY_FOLDERS),
      ]);

      const notes: Note[] = savedNotes ? JSON.parse(savedNotes) : [];
      const folders: NoteFolder[] = savedFolders ? JSON.parse(savedFolders) : DEFAULT_FOLDERS;

      set({ notes, folders, isLoading: false });
    } catch (e) {
      set({ isLoading: false });
    }
  },

  createNote: async (initial = {}) => {
    const now = Date.now();
    const newNote: Note = {
      id: `note_${now}_${Math.random().toString(36).slice(2, 7)}`,
      title: initial.title || 'Untitled Note',
      content: initial.content || '',
      folderId: initial.folderId ?? get().selectedFolderId,
      isPinned: initial.isPinned || false,
      tags: initial.tags || [],
      createdAt: now,
      updatedAt: now,
      syncStatus: 'local',
    };

    const updatedNotes = [newNote, ...get().notes];
    set({ notes: updatedNotes, activeNoteId: newNote.id });
    await AsyncStorage.setItem(STORAGE_KEY_NOTES, JSON.stringify(updatedNotes)).catch(() => {});
    return newNote;
  },

  updateNote: async (id, updates) => {
    set({ isSaving: true });
    const now = Date.now();
    const updatedNotes = get().notes.map((note) =>
      note.id === id ? { ...note, ...updates, updatedAt: now } : note
    );

    set({ notes: updatedNotes, isSaving: false, lastSavedAt: now });
    await AsyncStorage.setItem(STORAGE_KEY_NOTES, JSON.stringify(updatedNotes)).catch(() => {});
  },

  deleteNote: async (id) => {
    const updatedNotes = get().notes.filter((note) => note.id !== id);
    set((state) => ({
      notes: updatedNotes,
      activeNoteId: state.activeNoteId === id ? null : state.activeNoteId,
    }));
    await AsyncStorage.setItem(STORAGE_KEY_NOTES, JSON.stringify(updatedNotes)).catch(() => {});
  },

  togglePin: async (id) => {
    const note = get().notes.find((n) => n.id === id);
    if (!note) return;
    await get().updateNote(id, { isPinned: !note.isPinned });
  },

  moveNote: async (id, folderId) => {
    await get().updateNote(id, { folderId });
  },

  duplicateNote: async (id) => {
    const source = get().notes.find((n) => n.id === id);
    if (!source) return null;
    return get().createNote({
      title: `${source.title} (Copy)`,
      content: source.content,
      folderId: source.folderId,
      tags: source.tags,
      isPinned: false,
    });
  },

  createFolder: async (name, icon = 'folder') => {
    const newFolder: NoteFolder = {
      id: `f_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: name.trim(),
      icon,
      createdAt: Date.now(),
    };
    const updatedFolders = [...get().folders, newFolder];
    set({ folders: updatedFolders });
    await AsyncStorage.setItem(STORAGE_KEY_FOLDERS, JSON.stringify(updatedFolders)).catch(() => {});
    return newFolder;
  },

  renameFolder: async (id, name) => {
    const updatedFolders = get().folders.map((f) => (f.id === id ? { ...f, name: name.trim() } : f));
    set({ folders: updatedFolders });
    await AsyncStorage.setItem(STORAGE_KEY_FOLDERS, JSON.stringify(updatedFolders)).catch(() => {});
  },

  deleteFolder: async (id) => {
    const updatedFolders = get().folders.filter((f) => f.id !== id);
    const updatedNotes = get().notes.map((n) => (n.folderId === id ? { ...n, folderId: null } : n));
    set({
      folders: updatedFolders,
      notes: updatedNotes,
      selectedFolderId: get().selectedFolderId === id ? null : get().selectedFolderId,
    });
    await Promise.all([
      AsyncStorage.setItem(STORAGE_KEY_FOLDERS, JSON.stringify(updatedFolders)),
      AsyncStorage.setItem(STORAGE_KEY_NOTES, JSON.stringify(updatedNotes)),
    ]).catch(() => {});
  },

  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedFolder: (folderId) => set({ selectedFolderId: folderId }),
  setActiveNoteId: (id) => set({ activeNoteId: id }),

  getFilteredNotes: () => {
    const { notes, selectedFolderId, searchQuery } = get();
    return notes
      .filter((note) => {
        const matchesFolder = selectedFolderId === null || note.folderId === selectedFolderId;
        const matchesQuery =
          !searchQuery.trim() ||
          note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          note.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (note.tags && note.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase())));
        return matchesFolder && matchesQuery;
      })
      .sort((a, b) => {
        if (a.isPinned && !b.isPinned) return -1;
        if (!a.isPinned && b.isPinned) return 1;
        return b.updatedAt - a.updatedAt;
      });
  },
}));
```

---

### Task 2: Navigation Integration (Tabs & FluidBottomBar)

**Files:**
- Modify: `delta/mobile/src/components/common/FluidBottomBar.tsx`
- Modify: `delta/mobile/app/(tabs)/_layout.tsx`
- Create: `delta/mobile/app/(tabs)/notes.tsx`

**Interfaces:**
- Consumes: `useThemeColors`, `useNotesStore`
- Produces: Notes tab screen in bottom navigation bar

- [ ] **Step 1: Update `TAB_CONFIG` in `FluidBottomBar.tsx`**

Add `notes` entry:
```typescript
  notes: {
    label: 'Notes',
    activeIcon: 'document-text',
    inactiveIcon: 'document-text-outline',
  },
```

- [ ] **Step 2: Update `TabLayout` in `app/(tabs)/_layout.tsx`**

Include `<Tabs.Screen name="notes" options={{ title: 'Notes' }} />`.

---

### Task 3: Notes UI Components (Header, List, Card, Folder Manager)

**Files:**
- Create: `delta/mobile/src/components/notes/NotesHeader.tsx`
- Create: `delta/mobile/src/components/notes/NoteCard.tsx`
- Create: `delta/mobile/src/components/notes/FolderManagerModal.tsx`
- Create: `delta/mobile/src/components/notes/NewItemSheet.tsx`

**Interfaces:**
- Consumes: `useNotesStore`, `useThemeColors`, `LiquidGlassCard`
- Produces: Note browsing, searching, filtering, and quick creation UI

- [ ] **Step 1: Build `NotesHeader.tsx` with search input, folder pills, and "+" button**
- [ ] **Step 2: Build `NoteCard.tsx` with pinned badge, preview, time formatting, and context actions**
- [ ] **Step 3: Build `FolderManagerModal.tsx` and `NewItemSheet.tsx`**

---

### Task 4: Note Editor & Markdown Viewer

**Files:**
- Create: `delta/mobile/src/components/notes/NoteEditorModal.tsx`
- Create: `delta/mobile/src/components/notes/NoteActionSheet.tsx`
- Modify: `delta/mobile/app/(tabs)/notes.tsx`

**Interfaces:**
- Consumes: `useNotesStore`, `useThemeColors`, `sendChatMessage`
- Produces: Fullscreen note editor with debounced auto-save (400ms), status badge (`Saving...`/`Saved`), Markdown preview toggle, and AI action trigger.

- [ ] **Step 1: Build `NoteActionSheet.tsx` (Summarize, Improve, Expand, Create Tasks, Ask Delta, Pin, Move, Delete)**
- [ ] **Step 2: Build `NoteEditorModal.tsx` with debounced auto-save & status indicator**
- [ ] **Step 3: Assemble `app/(tabs)/notes.tsx`**

---

### Task 5: AI Agent Integration & Chat Message Actions

**Files:**
- Create: `delta/mobile/src/services/notes/noteAgentBridge.ts`
- Modify: `delta/mobile/src/services/router/embeddedRouterEngine.ts`
- Modify: `delta/mobile/src/components/chat/MessageBubble.tsx`
- Create: `delta/mobile/tests/notes_agent.test.ts`

**Interfaces:**
- Consumes: `useNotesStore`, `useChatStore`
- Produces: Agent tools (`create_note`, `search_notes`, `read_note`, `update_note`, `delete_note`, `list_notes`), MessageBubble "Save as Note" action, Note "Ask Delta" contextual chat trigger.

- [ ] **Step 1: Implement `noteAgentBridge.ts` for AI agent tool calling**
- [ ] **Step 2: Register note agent tools in `embeddedRouterEngine.ts` system prompt & execution router**
- [ ] **Step 3: Add "Save as Note" button in `MessageBubble.tsx`**
- [ ] **Step 4: Connect "Ask Delta" to open Chat tab with injected note context**
- [ ] **Step 5: Write unit test in `delta/mobile/tests/notes_agent.test.ts`**

---

### Task 6: Verification & Polish

**Files:**
- Run: `delta/mobile/tests/verify.mjs` / Node test runner
- Run: `npm run typecheck` in `delta/mobile`

- [ ] **Step 1: Run unit tests and type checks**
- [ ] **Step 2: Verify UI theme compatibility (Dark & Light mode)**
- [ ] **Step 3: Verify smooth navigation, auto-save, and chat integration**
