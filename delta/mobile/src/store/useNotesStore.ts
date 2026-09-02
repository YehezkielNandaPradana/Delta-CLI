import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Note, NoteFolder } from '../types/notes';

const STORAGE_KEY_NOTES = '@delta_notes';
const STORAGE_KEY_FOLDERS = '@delta_folders';

export const DEFAULT_FOLDERS: NoteFolder[] = [
  { id: 'f_projects', name: 'Projects', icon: 'briefcase', createdAt: 1700000000000 },
  { id: 'f_learning', name: 'Learning', icon: 'book', createdAt: 1700000000000 },
  { id: 'f_ideas', name: 'Ideas', icon: 'bulb', createdAt: 1700000000000 },
  { id: 'f_personal', name: 'Personal', icon: 'person', createdAt: 1700000000000 },
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
      folderId: initial.folderId !== undefined ? initial.folderId : get().selectedFolderId,
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
      tags: source.tags ? [...source.tags] : [],
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
