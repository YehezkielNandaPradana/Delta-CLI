import assert from 'node:assert';
import { useNotesStore, DEFAULT_FOLDERS } from '../src/store/useNotesStore.js';
import { noteAgentBridge } from '../src/services/notes/noteAgentBridge.js';

console.log('🧪 Running Delta Notes Unit Tests...');

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
console.log('✅ Create Note passed');

// 3. Pin & Update
await useNotesStore.getState().togglePin(note1.id);
assert.strictEqual(useNotesStore.getState().notes[0].isPinned, true, 'Note pinned');

await useNotesStore.getState().updateNote(note1.id, {
  title: 'Updated Architecture',
});
assert.strictEqual(useNotesStore.getState().notes[0].title, 'Updated Architecture', 'Note title updated');
console.log('✅ Update & Pin Note passed');

// 4. Duplicate Note
const copyNote = await useNotesStore.getState().duplicateNote(note1.id);
assert.ok(copyNote, 'Copy note exists');
assert.strictEqual(copyNote.title, 'Updated Architecture (Copy)', 'Copy title matches');
assert.strictEqual(useNotesStore.getState().notes.length, 2, 'Two notes in store');
console.log('✅ Duplicate Note passed');

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
console.log('✅ Folder management & Move Note passed');

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
console.log('✅ Search and Folder Filtering passed');

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

console.log('🎉 All Delta Notes tests passed successfully!');
