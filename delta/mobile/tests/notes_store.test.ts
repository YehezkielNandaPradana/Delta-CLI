import { useNotesStore, DEFAULT_FOLDERS } from '../src/store/useNotesStore';

describe('useNotesStore', () => {
  beforeEach(() => {
    useNotesStore.setState({
      notes: [],
      folders: DEFAULT_FOLDERS,
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
    expect(useNotesStore.getState().folders.some((f) => f.name === 'Security Audits')).toBe(true);

    const note = await useNotesStore.getState().createNote({
      title: 'Audit Report',
      content: 'Vuln summary',
      folderId: folder.id,
    });

    await useNotesStore.getState().deleteFolder(folder.id);
    // Note should have folderId reset to null/unassigned
    const updatedNote = useNotesStore.getState().notes.find((n) => n.id === note.id);
    expect(updatedNote?.folderId).toBeNull();
  });

  test('should filter notes by search query and folder', async () => {
    await useNotesStore.getState().createNote({
      title: 'Delta Mobile Security',
      content: 'Authentication and tokens',
      folderId: 'f_projects',
    });
    await useNotesStore.getState().createNote({
      title: 'Ideas for Voice',
      content: 'Whisper and TTS pipeline',
      folderId: 'f_ideas',
    });

    useNotesStore.getState().setSearchQuery('security');
    let filtered = useNotesStore.getState().getFilteredNotes();
    expect(filtered.length).toBe(1);
    expect(filtered[0].title).toBe('Delta Mobile Security');

    useNotesStore.getState().setSearchQuery('');
    useNotesStore.getState().setSelectedFolder('f_ideas');
    filtered = useNotesStore.getState().getFilteredNotes();
    expect(filtered.length).toBe(1);
    expect(filtered[0].title).toBe('Ideas for Voice');
  });
});
