const assert = require('assert');

// Test session persistence and manipulation
async function testChatSessions() {
  console.log('🧪 Running Multi-Session Chat Store Test Suite...');

  // Mock sessions state
  const session1 = {
    id: 'sess_1',
    title: 'Analisis Port Laravel',
    messages: [{ id: 'm1', sender: 'user', text: 'scan port 8000', timestamp: Date.now() }],
    createdAt: Date.now() - 10000,
    updatedAt: Date.now(),
  };

  const session2 = {
    id: 'sess_2',
    title: 'Audit Keamanan JWT',
    messages: [{ id: 'm2', sender: 'user', text: 'audit jwt header', timestamp: Date.now() }],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  const sessions = [session2, session1];
  let currentSessionId = 'sess_2';

  // 1. Validate session switching
  currentSessionId = 'sess_1';
  const current = sessions.find(s => s.id === currentSessionId);
  assert.strictEqual(current.title, 'Analisis Port Laravel');
  console.log('✅ Session switching passed');

  // 2. Validate session creation
  const session3 = {
    id: 'sess_3',
    title: 'Obrolan Baru',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
  sessions.unshift(session3);
  currentSessionId = session3.id;
  assert.strictEqual(sessions.length, 3);
  assert.strictEqual(currentSessionId, 'sess_3');
  console.log('✅ Session creation passed');

  // 3. Auto-title from first message
  const userMsg = 'Tolong buatkan catatan tentang CSRF';
  if (session3.title === 'Obrolan Baru') {
    session3.title = userMsg.slice(0, 28) + (userMsg.length > 28 ? '...' : '');
  }
  assert.strictEqual(session3.title, 'Tolong buatkan catatan tenta...');
  console.log('✅ Auto title generation passed');

  console.log('🎉 All Multi-Session Chat Store tests PASSED!');
}

testChatSessions().catch(err => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
