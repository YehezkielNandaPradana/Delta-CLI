import { noteAgentBridge } from '../src/services/notes/noteAgentBridge';
import { useNotesStore, DEFAULT_FOLDERS } from '../src/store/useNotesStore';

describe('noteAgentBridge', () => {
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

  test('should create note through agent tool', async () => {
    const res = await noteAgentBridge.createNote({
      title: 'Agent Created Note',
      content: 'Delta created this via natural language prompt',
      folderName: 'Ideas',
      tags: ['agent', 'cyber'],
    });

    expect(res.success).toBe(true);
    expect(res.data.id).toBeDefined();
    expect(useNotesStore.getState().notes.length).toBe(1);
    expect(useNotesStore.getState().notes[0].title).toBe('Agent Created Note');
  });

  test('should search notes through agent tool', async () => {
    await noteAgentBridge.createNote({
      title: 'Penetration Testing Checklist',
      content: 'Reconnaissance, Scanning, Exploitation',
    });
    await noteAgentBridge.createNote({
      title: 'API Security Guide',
      content: 'OAuth2, JWT, Rate Limiting',
    });

    const res = await noteAgentBridge.searchNotes({ query: 'scanning' });
    expect(res.success).toBe(true);
    expect(res.data.length).toBe(1);
    expect(res.data[0].title).toBe('Penetration Testing Checklist');
  });

  test('should read note by title', async () => {
    const created = await noteAgentBridge.createNote({
      title: 'Target Scope',
      content: 'example.com and subdomains',
    });

    const res = await noteAgentBridge.readNote({ title: 'Target Scope' });
    expect(res.success).toBe(true);
    expect(res.data.content).toBe('example.com and subdomains');
  });

  test('should update and append note content', async () => {
    const created = await noteAgentBridge.createNote({
      title: 'Vulnerability Log',
      content: 'Finding 1: XSS on /login',
    });

    const res = await noteAgentBridge.updateNote({
      id: created.data.id,
      appendContent: 'Finding 2: SQLi on /search',
    });

    expect(res.success).toBe(true);
    const updated = useNotesStore.getState().notes.find((n) => n.id === created.data.id);
    expect(updated?.content).toContain('Finding 1: XSS on /login');
    expect(updated?.content).toContain('Finding 2: SQLi on /search');
  });

  test('should delete note through agent tool', async () => {
    const created = await noteAgentBridge.createNote({
      title: 'Temporary Note',
      content: 'To be removed',
    });

    const res = await noteAgentBridge.deleteNote({ id: created.data.id });
    expect(res.success).toBe(true);
    expect(useNotesStore.getState().notes.length).toBe(0);
  });
});
