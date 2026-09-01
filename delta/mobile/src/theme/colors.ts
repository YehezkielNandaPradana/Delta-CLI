export interface ThemePalette {
  bgPrimary: string;
  bgSecondary: string;
  bgSurface: string;

  cardBg: string;
  cardBorder: string;
  cardSpecular: string;

  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textDim: string;

  // Primary Navy Brand Accents
  accentGreen: string; // Brand Primary (Navy / Royal)
  accentGreenSubtle: string;
  accentGreenGlow: string;

  accentNavy: string;
  accentNavyLight: string;
  accentNavyDark: string;

  accentCyan: string;
  accentCyanSubtle: string;

  accentPurple: string;
  accentPurpleSubtle: string;

  accentRed: string;
  accentRedSubtle: string;

  accentYellow: string;
  accentYellowSubtle: string;

  bottomBarBg: string;
  bottomBarBorder: string;
  bottomBarActivePill: string;
  bottomBarActiveGlow: string;

  codeBg: string;
  codeBorder: string;

  // Compatibility tokens
  bgCard: string;
  bgCardHover: string;
  border: string;
  borderActive: string;
}

export const DARK_THEME: ThemePalette = {
  // Deep Navy Cosmic Base
  bgPrimary: '#070d19',
  bgSecondary: '#0c1629',
  bgSurface: '#12203a',

  cardBg: '#0f1c35',
  cardBorder: 'rgba(59, 130, 246, 0.16)',
  cardSpecular: 'rgba(147, 197, 253, 0.28)',

  textPrimary: '#f8fafc',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',
  textDim: '#3b4d6b',

  // Primary Brand Accent -> Electric Navy / Royal Blue
  accentGreen: '#3b82f6',
  accentGreenSubtle: 'rgba(59, 130, 246, 0.16)',
  accentGreenGlow: 'rgba(59, 130, 246, 0.35)',

  accentNavy: '#1d4ed8',
  accentNavyLight: '#60a5fa',
  accentNavyDark: '#0a192f',

  accentCyan: '#38bdf8',
  accentCyanSubtle: 'rgba(56, 189, 248, 0.16)',

  accentPurple: '#818cf8',
  accentPurpleSubtle: 'rgba(129, 140, 248, 0.16)',

  accentRed: '#f43f5e',
  accentRedSubtle: 'rgba(244, 63, 94, 0.16)',

  accentYellow: '#fbbf24',
  accentYellowSubtle: 'rgba(251, 191, 36, 0.16)',

  bottomBarBg: 'rgba(10, 20, 38, 0.94)',
  bottomBarBorder: 'rgba(59, 130, 246, 0.22)',
  bottomBarActivePill: 'rgba(37, 99, 235, 0.22)',
  bottomBarActiveGlow: 'rgba(59, 130, 246, 0.45)',

  codeBg: '#060a14',
  codeBorder: 'rgba(59, 130, 246, 0.14)',

  bgCard: '#0f1c35',
  bgCardHover: '#17284a',
  border: 'rgba(59, 130, 246, 0.16)',
  borderActive: 'rgba(59, 130, 246, 0.45)',
};

export const LIGHT_THEME: ThemePalette = {
  // Crisp Porcelain & Ice Navy Base
  bgPrimary: '#f0f5fc',
  bgSecondary: '#e2ebf7',
  bgSurface: '#ffffff',

  cardBg: '#ffffff',
  cardBorder: 'rgba(30, 58, 138, 0.12)',
  cardSpecular: 'rgba(255, 255, 255, 0.95)',

  textPrimary: '#0f172a',
  textSecondary: '#334155',
  textMuted: '#64748b',
  textDim: '#94a3b8',

  // Primary Brand Accent -> Deep Royal Navy Blue
  accentGreen: '#1d4ed8',
  accentGreenSubtle: 'rgba(29, 78, 216, 0.12)',
  accentGreenGlow: 'rgba(29, 78, 216, 0.25)',

  accentNavy: '#1e3a8a',
  accentNavyLight: '#3b82f6',
  accentNavyDark: '#0f172a',

  accentCyan: '#0284c7',
  accentCyanSubtle: 'rgba(2, 132, 199, 0.12)',

  accentPurple: '#6366f1',
  accentPurpleSubtle: 'rgba(99, 102, 241, 0.12)',

  accentRed: '#e11d48',
  accentRedSubtle: 'rgba(225, 29, 72, 0.12)',

  accentYellow: '#d97706',
  accentYellowSubtle: 'rgba(217, 119, 6, 0.12)',

  bottomBarBg: 'rgba(255, 255, 255, 0.95)',
  bottomBarBorder: 'rgba(30, 58, 138, 0.12)',
  bottomBarActivePill: 'rgba(29, 78, 216, 0.12)',
  bottomBarActiveGlow: 'rgba(29, 78, 216, 0.25)',

  codeBg: '#f8fafc',
  codeBorder: 'rgba(30, 58, 138, 0.08)',

  bgCard: '#ffffff',
  bgCardHover: '#f8fafc',
  border: 'rgba(30, 58, 138, 0.12)',
  borderActive: 'rgba(29, 78, 216, 0.35)',
};

export const THEME_PALETTES = {
  dark: DARK_THEME,
  light: LIGHT_THEME,
} as const;

// Backward-compatible default colors
export const COLORS = DARK_THEME;
