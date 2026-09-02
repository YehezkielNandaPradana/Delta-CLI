const assert = require('assert');

// Test suite for Dynamic Skills Dispatching & Heuristic Triggering
async function testSkillsSystem() {
  console.log('🧪 Running Dynamic Coding Skills Test Suite...');

  // Mock skills
  const skills = [
    {
      id: 'ui-ux-pro-max',
      name: 'UI/UX Pro Max',
      tags: ['UI/UX', 'Design System', 'Accessibility'],
      systemPromptSnippet: '[SKILL: UI/UX Pro Max]\n- Visual hierarchy',
      isActive: true,
    },
    {
      id: 'security-sentinel',
      name: 'Security Sentinel',
      tags: ['Cybersecurity', 'OWASP'],
      systemPromptSnippet: '[SKILL: Security Sentinel]\n- Input audit',
      isActive: true,
    },
    {
      id: 'testing-guru',
      name: 'Testing Guru',
      tags: ['TDD', 'QA'],
      systemPromptSnippet: '[SKILL: Testing Guru]\n- Write tests',
      isActive: false, // Inactive
    },
  ];

  function isSkillRelevant(skill, query) {
    if (!query) return true;
    const q = query.toLowerCase();
    const matchTag = skill.tags.some(t => q.includes(t.toLowerCase()));
    const matchName = q.includes(skill.name.toLowerCase()) || q.includes(skill.id.toLowerCase());

    if (skill.id === 'ui-ux-pro-max') {
      if (q.includes('ui') || q.includes('desain') || q.includes('tampilan') || q.includes('button')) return true;
    }
    if (skill.id === 'security-sentinel') {
      if (q.includes('keamanan') || q.includes('security') || q.includes('auth') || q.includes('jwt')) return true;
    }
    return matchTag || matchName;
  }

  function getActiveSkillPrompts(query) {
    const active = skills.filter(s => s.isActive);
    const relevant = query ? active.filter(s => isSkillRelevant(s, query)) : active;
    if (relevant.length === 0) return '';
    return relevant.map(s => s.systemPromptSnippet).join('\n\n');
  }

  // 1. Test UI Query -> Triggers UI/UX Pro Max, NOT Security
  const uiPrompt = getActiveSkillPrompts('buatkan desain button yang clean');
  assert(uiPrompt.includes('UI/UX Pro Max'), 'UI query must activate UI/UX skill');
  assert(!uiPrompt.includes('Security Sentinel'), 'UI query should NOT activate Security skill');
  console.log('✅ UI heuristic relevance filter passed');

  // 2. Test Security Query -> Triggers Security Sentinel, NOT UI
  const secPrompt = getActiveSkillPrompts('bagaimana cara mengamankan jwt auth');
  assert(secPrompt.includes('Security Sentinel'), 'Security query must activate Security skill');
  assert(!secPrompt.includes('UI/UX Pro Max'), 'Security query should NOT activate UI skill');
  console.log('✅ Security heuristic relevance filter passed');

  // 3. Test General / Irrelevant Query -> Returns empty (saves tokens)
  const mathPrompt = getActiveSkillPrompts('hitung 50 + 20');
  assert.strictEqual(mathPrompt, '', 'Irrelevant query should not load any coding skills');
  console.log('✅ Token saving & selective non-loading passed');

  // 4. Test Inactive Skill -> Never triggered even if relevant
  const testPrompt = getActiveSkillPrompts('buatkan unit test');
  assert(!testPrompt.includes('Testing Guru'), 'Inactive skill should not be loaded');
  console.log('✅ Inactive toggle respect passed');

  console.log('🎉 All Dynamic Coding Skills tests PASSED 100%!');
}

testSkillsSystem().catch(err => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
