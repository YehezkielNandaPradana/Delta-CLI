export interface DeltaSkill {
  id: string;
  name: string;
  category: 'Frontend & UI' | 'Architecture' | 'Testing & QA' | 'Security' | 'DevOps' | 'Custom';
  description: string;
  tags: string[];
  systemPromptSnippet: string;
  isActive: boolean;
  isCustom?: boolean;
}

export const PRESET_SKILLS: DeltaSkill[] = [
  {
    id: 'ui-ux-pro-max',
    name: 'UI/UX Pro Max',
    category: 'Frontend & UI',
    description: 'Prinsip desain produk kelas dunia, visual hierarchy, micro-interactions, dan token styling.',
    tags: ['UI/UX', 'Design System', 'Accessibility'],
    systemPromptSnippet: `[SKILL: UI/UX Pro Max]
- Establish ONE clear visual focal point per screen.
- Order visual hierarchy by importance: size > contrast > weight > spacing.
- Consistent 4px/8px rhythm; never use arbitrary padding.
- Ensure accessible contrast (WCAG AA compliant) and fluid responsive layouts.
- Modern typography, generous whitespace, and subtle tactile motion.`,
    isActive: true,
  },
  {
    id: 'frontend-design',
    name: 'Frontend Design Mastery',
    category: 'Frontend & UI',
    description: 'Spesialisasi arsitektur React / React Native, styling bersih, state atomic, dan zero boilerplate.',
    tags: ['React', 'React Native', 'Tailwind', 'Zustand'],
    systemPromptSnippet: `[SKILL: Frontend Design Mastery]
- Write clean, declarative, production-grade components without unnecessary wrappers.
- State management: prefer minimal local state or Zustand stores.
- Idiomatic mobile interactions with proper touch feedback and high 60fps animations.
- Defensive error boundary handling and robust fallbacks.`,
    isActive: true,
  },
  {
    id: 'clean-architect',
    name: 'Clean Architecture & YAGNI',
    category: 'Architecture',
    description: 'Pola kode modular, minim abstraksi berlebih (YAGNI), pemisahan concern tajam, dan refaktor efisien.',
    tags: ['Architecture', 'Refactoring', 'YAGNI'],
    systemPromptSnippet: `[SKILL: Clean Architecture & YAGNI]
- YAGNI: The best code is the code never written. Never add unrequested abstractions.
- Pure functions and immutable data flows where possible.
- Shortest working diff wins; prioritize clarity over cleverness.`,
    isActive: true,
  },
  {
    id: 'testing-guru',
    name: 'Testing & Verification Guru',
    category: 'Testing & QA',
    description: 'Metodologi TDD, test verifikasi mandiri, edge case handling, dan anti-regresi.',
    tags: ['TDD', 'Unit Test', 'QA'],
    systemPromptSnippet: `[SKILL: Testing Guru]
- Write concise, runnable verification checks for non-trivial logic.
- Verify behavior against edge cases, network failures, and bad inputs.`,
    isActive: false,
  },
  {
    id: 'security-sentinel',
    name: 'Security Sentinel & Pentest',
    category: 'Security',
    description: 'Validasi input ketat, sanitasi XSS/SQLi, autentikasi aman, dan audit kerentanan sistem.',
    tags: ['Cybersecurity', 'OWASP', 'Auditing'],
    systemPromptSnippet: `[SKILL: Security Sentinel]
- Audit all input boundaries, parameters, and tokens.
- Never expose API keys or sensitive payload data.
- Recommend secure defaults (CSRF tokens, parameterized queries, rate limits).`,
    isActive: true,
  },
];
