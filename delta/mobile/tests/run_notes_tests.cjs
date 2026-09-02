const assert = require('assert');

// In-memory mock of AsyncStorage for Node.js test environment
const mockStorage = new Map();
const AsyncStorage = {
  getItem: async (key) => mockStorage.get(key) || null,
  setItem: async (key, value) => { mockStorage.set(key, value); },
  removeItem: async (key) => { mockStorage.delete(key); },
  clear: async () => { mockStorage.clear(); },
};

// Mock zustand create
function create(fn) {
  let state;
  const listeners = new Set();
  const set = (partial) => {
    const nextState = typeof partial === 'function' ? partial(state) : partial;
    state = Object.assign({}, state, nextState);
    listeners.forEach((l) => l(state));
  };
  const get = () => state;
  state = fn(set, get);
  const store = {
    getState: get,
    setState: set,
    subscribe: (fn) => { listeners.add(fn); return () => listeners.delete(fn); },
  };
  return store;
}

const DEFAULT_FOLDERS = [
  { id: 'f_projects', name: 'Projects', icon: 'briefcase', createdAt: 1700000000000 },
  { id: 'f_learning', name: 'Learning', icon: 'book', createdAt: 1700000000000 },
  { id: 'f_ideas', name: 'Ideas', icon: 'bulb', createdAt: 1700000000000 },
  { id: 'f_personal', name: 'Personal', icon: 'person', createdAt: 1700000000000 },
];

const useNotesStore = create((set, get) => ({
  notes: [],
  folders: DEFAULT_FOLDERS,
  selectedFolderId: null,
  searchQuery: '',
  activeNoteId: null,
  isSaving: false,
  lastSavedAt: null,
  isLoading: false,

  createNote: async (initial = {}) => {
    const now = Date.now();
    const newNote = {
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
    await AsyncStorage.setItem('@delta_notes', JSON.stringify(updatedNotes));
    return newNote;
  },

  updateNote: async (id, updates) => {
    set({ isSaving: true });
    const now = Date.now();
    const updatedNotes = get().notes.map((note) =>
      note.id === id ? { ...note, ...updates, updatedAt: now } : note
    );
    set({ notes: updatedNotes, isSaving: false, lastSavedAt: now });
    await AsyncStorage.setItem('@delta_notes', JSON.stringify(updatedNotes));
  },

  deleteNote: async (id) => {
    const updatedNotes = get().notes.filter((note) => note.id !== id);
    set((state) => ({
      notes: updatedNotes,
      activeNoteId: state.activeNoteId === id ? null : state.activeNoteId,
    }));
    await AsyncStorage.setItem('@delta_notes', JSON.stringify(updatedNotes));
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
    const newFolder = {
      id: `f_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: name.trim(),
      icon,
      createdAt: Date.now(),
    };
    const updatedFolders = [...get().folders, newFolder];
    set({ folders: updatedFolders });
    await AsyncStorage.setItem('@delta_folders', JSON.stringify(updatedFolders));
    return newFolder;
  },

  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedFolder: (folderId) => set({ selectedFolderId: folderId }),

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

// noteAgentBridge simulation using the store
const noteAgentBridge = {
  async createNote(params) {
    const { folders, createNote, createFolder } = useNotesStore.getState();
    let targetFolderId = params.folderId || null;
    if (!targetFolderId && params.folderName) {
      const existing = folders.find((f) => f.name.toLowerCase() === params.folderName.toLowerCase());
      if (existing) {
        targetFolderId = existing.id;
      } else {
        const created = await createFolder(params.folderName);
        targetFolderId = created.id;
      }
    }
    const note = await createNote({
      title: params.title || 'Note',
      content: params.content || '',
      folderId: targetFolderId,
      tags: params.tags || [],
    });
    return { success: true, data: note };
  },

  async searchNotes(params) {
    const { notes } = useNotesStore.getState();
    const q = (params.query || '').toLowerCase().trim();
    const matches = notes.filter(
      (n) =>
        n.title.toLowerCase().includes(q) ||
        n.content.toLowerCase().includes(q) ||
        (n.tags && n.tags.some((t) => t.toLowerCase().includes(q)))
    );
    return { success: true, data: matches };
  },

  async readNote(params) {
    const { notes } = useNotesStore.getState();
    const note = notes.find(
      (n) =>
        (params.id && n.id === params.id) ||
        (params.title && n.title.toLowerCase() === params.title.toLowerCase())
    );
    return { success: !!note, data: note };
  },
};

async function testSuite() {
  console.log('🧪 Running Delta Notes E2E Logic Test Suite...');

  // 1. Initial State
  assert.strictEqual(useNotesStore.getState().notes.length, 0, 'Initial notes empty');
  assert.strictEqual(useNotesStore.getState().folders.length, 4, 'Default 4 folders present');

  // 2. Create Note
  const note1 = await useNotesStore.getState().createNote({
    title: 'Architecture Overview',
    content: 'Delta Mobile local-first notes design.',
    folderId: 'f_ideas',
    tags: ['architecture', 'mobile'],
  });

  assert.ok(note1.id.startsWith('note_'), 'Note ID generated properly');
  assert.strictEqual(useNotesStore.getState().notes.length, 1, 'Note added to store');
  assert.strictEqual(useNotesStore.getState().notes[0].title, 'Architecture Overview');
  console.log('✅ Note creation passed');

  // 3. Pin & Update
  await useNotesStore.getState().togglePin(note1.id);
  assert.strictEqual(useNotesStore.getState().notes[0].isPinned, true, 'Note pinned');

  await useNotesStore.getState().updateNote(note1.id, {
    title: 'Updated Architecture',
  });
  assert.strictEqual(useNotesStore.getState().notes[0].title, 'Updated Architecture', 'Note title updated');
  console.log('✅ Note update & pin passed');

  // 4. Duplicate Note
  const copyNote = await useNotesStore.getState().duplicateNote(note1.id);
  assert.ok(copyNote, 'Copy note exists');
  assert.strictEqual(copyNote.title, 'Updated Architecture (Copy)', 'Copy title matches');
  assert.strictEqual(useNotesStore.getState().notes.length, 2, 'Two notes in store');
  console.log('✅ Note duplication passed');

  // 5. Folder Creation & Move
  const newFolder = await useNotesStore.getState().createFolder('Security Research');
  assert.ok(newFolder.id.startsWith('f_'), 'Folder ID generated');
  assert.strictEqual(useNotesStore.getState().folders.length, 5, '5 folders in store');

  await useNotesStore.getState().moveNote(copyNote.id, newFolder.id);
  assert.strictEqual(
    useNotesStore.getState().notes.find((n) => n.id === copyNote.id).folderId,
    newFolder.id,
    'Note moved to new folder'
  );
  console.log('✅ Folder creation and Note moving passed');

  // 6. Search Filtering
  useNotesStore.getState().setSearchQuery('local-first');
  let filtered = useNotesStore.getState().getFilteredNotes();
  assert.strictEqual(filtered.length, 2, 'Found 2 notes matching local-first');

  useNotesStore.getState().setSearchQuery('Updated Architecture (Copy)');
  filtered = useNotesStore.getState().getFilteredNotes();
  assert.strictEqual(filtered.length, 1, 'Found 1 note matching exact title');

  useNotesStore.getState().setSearchQuery('');
  useNotesStore.getState().setSelectedFolder('f_ideas');
  filtered = useNotesStore.getState().getFilteredNotes();
  assert.strictEqual(filtered.length, 1, 'Folder filter working');
  console.log('✅ Search and Folder filtering passed');

  // 7. Agent Bridge Tools
  const agentCreate = await noteAgentBridge.createNote({
    title: 'Agent Generated Findings',
    content: 'Found vulnerability in auth token storage.',
    folderName: 'Learning',
    tags: ['cve', 'vuln'],
  });
  assert.strictEqual(agentCreate.success, true, 'Agent create note succeeded');

  const agentSearch = await noteAgentBridge.searchNotes({ query: 'vulnerability' });
  assert.strictEqual(agentSearch.success, true, 'Agent search succeeded');
  assert.strictEqual(agentSearch.data.length, 1, 'Found 1 matching note in agent search');

  const agentRead = await noteAgentBridge.readNote({ title: 'Agent Generated Findings' });
  assert.strictEqual(agentRead.success, true, 'Agent read note succeeded');
  assert.strictEqual(agentRead.data.tags[0], 'cve', 'Tags present in read data');
  console.log('✅ Agent Bridge Tools passed');

  console.log('🎉 All Delta Notes logic and integration tests PASSED!');
}

testSuite().catch((err) => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
