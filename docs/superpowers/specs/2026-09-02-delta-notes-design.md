# Design Spec: Delta Notes Subsystem for Delta Mobile

**Date:** 2026-09-02  
**Status:** Approved  
**Platform:** React Native / Expo (iOS, Android, Web)  
**Target:** `delta/mobile`  

---

## 1. Overview & Goals

Delta Notes introduces a native, local-first note-taking and knowledge repository into **Delta Mobile**, deeply integrated with the Delta AI Agent (`ag/gemini-3.7-flash-high` & local models). Users can create, organize, search, and pin notes, save chat responses directly into notes, and trigger AI agent actions (Summarize, Improve, Expand, Create Tasks, Ask Delta) or allow Delta Agent tools to search/create/update notes autonomously.

---

## 2. Architecture & Data Model

### 2.1 Types (`src/types/notes.ts`)

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

### 2.2 Zustand Store (`src/store/useNotesStore.ts`)

- **State:**
  - `notes: Note[]`
  - `folders: NoteFolder[]`
  - `selectedFolderId: string | null`
  - `searchQuery: string`
  - `activeNoteId: string | null`
  - `isSaving: boolean`
  - `lastSavedAt: number | null`

- **Actions:**
  - `loadNotes(): Promise<void>`
  - `createNote(initial?: Partial<Note>): Promise<Note>`
  - `updateNote(id: string, updates: Partial<Note>): Promise<void>`
  - `deleteNote(id: string): Promise<void>`
  - `togglePin(id: string): Promise<void>`
  - `moveNote(id: string, folderId: string | null): Promise<void>`
  - `duplicateNote(id: string): Promise<Note>`
  - `createFolder(name: string): Promise<NoteFolder>`
  - `renameFolder(id: string, name: string): Promise<void>`
  - `deleteFolder(id: string): Promise<void>`
  - `setSearchQuery(query: string): void`
  - `setSelectedFolder(folderId: string | null): void`

- **Storage Keys:**
  - `@delta_notes`: Array of `Note` objects.
  - `@delta_folders`: Array of `NoteFolder` objects. Default folders: `Projects`, `Learning`, `Ideas`, `Personal`.

---

## 3. Navigation & Screen Integration

### 3.1 Tabs Navigation (`app/(tabs)/_layout.tsx` & `FluidBottomBar.tsx`)
- Add `notes` tab:
  - Route: `app/(tabs)/notes.tsx`
  - Icon: `document-text` / `document-text-outline`
  - Label: `Notes`
- Tabs order: `Chat (index)` | `Notes (notes)` | `9Router (activity)` | `History (history)` | `Settings (settings)`.

---

## 4. UI Components (`src/components/notes/`)

1. **`NotesHeader.tsx`**: Search bar, folder filter pills, "+ Note" / "+ Folder" quick action trigger.
2. **`NoteCard.tsx`**: Clean liquid glass card showing title, preview snippet, folder tag, updated time, pin indicator. Long-press / context menu.
3. **`NoteEditorModal.tsx` / `NoteEditor.tsx`**: Full-screen modal or sheet editor.
   - Live editable title and content text areas.
   - Top bar: Back, status badge (`Saving...` / `Saved`), AI Action menu button, Pin toggle.
   - Debounced auto-save (400ms delay).
   - Markdown preview toggle mode.
   - Smooth keyboard-avoiding wrapper.
4. **`NoteActionSheet.tsx`**: AI actions trigger bottom sheet (Summarize, Improve, Expand, Create Tasks, Ask Delta, Duplicate, Move, Delete).
5. **`FolderManagerModal.tsx`**: Create, rename, delete folder modal.

---

## 5. Chat & AI Agent Integration

### 5.1 Save Chat Message as Note
- In `MessageBubble.tsx`: Add "Save as Note" action in message options/long-press.
- Automatically generates title from first line / context, sets content, and adds to `useNotesStore`.

### 5.2 Agent Tool Bridge (`src/services/notes/noteAgentBridge.ts`)
- Functions exposed for Delta Agent:
  - `create_note({ title, content, folderId })`
  - `search_notes({ query })`
  - `read_note({ id_or_title })`
  - `update_note({ id, content, title })`
  - `delete_note({ id })`
  - `list_notes({ folderId })`
- Integrated into `embeddedRouterEngine.ts` system tool handler.

### 5.3 Note AI Actions Execution
- Executes prompt with note context via `sendChatMessage` or AI action templates:
  - **Summarize**: Prompts Delta to generate concise bullet-point summary.
  - **Improve**: Refines grammar, formatting, and technical depth.
  - **Expand**: Brainstorms and elaborates on ideas within note.
  - **Create Tasks**: Parses note into actionable markdown checkboxes `[ ]`.
  - **Ask Delta**: Navigates to Chat tab pre-filled or pre-contextualized with the Note.

---

## 6. Verification Plan

1. **Unit Tests**:
   - `delta/mobile/tests/notes_store.test.ts`: Test note & folder CRUD, pin toggle, move, search filter, and AsyncStorage persistence.
   - `delta/mobile/tests/notes_agent.test.ts`: Test note agent bridge tool execution.
2. **Type Check**:
   - Run `npm run typecheck` or `tsc --noEmit` in `delta/mobile`.
3. **App Verification**:
   - Create, edit, auto-save, pin, folder organize, search, save chat message, and trigger AI actions.
