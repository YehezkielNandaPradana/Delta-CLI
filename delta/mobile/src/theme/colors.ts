export interface ThemePalette {
  // Surfaces
  bgPrimary: string;       // Layer 0: Screen background
  bgSecondary: string;     // Layer 1: Primary container / Header / Tab bar
  bgSurface: string;       // Layer 2: Elevated surface / Cards
  surfaceElevated: string; // Layer 3: Modal / Dropdown / Sheet
  surfaceHover: string;    // Interactive item surface / pill background
  
  // Cards & Legacy Surface Aliases
  cardBg: string;
  cardBorder: string;
  cardSpecular: string;
  bgCard: string;
  bgCardHover: string;
  background: string;

  // Borders
  border: string;          // Subtle separation line
  borderStrong: string;    // Highlight / active border
  borderActive: string;    // Focused border

  // Typography
  textPrimary: string;     // High contrast main text
  textSecondary: string;   // Secondary descriptions
  textMuted: string;       // Metadata / timestamps
  textDim: string;         // Low contrast labels
  textDisabled: string;    // Inactive / disabled states

  // Pure Monochrome Accent
  accent: string;          // Primary monochrome accent
  accentStrong: string;
  accentMuted: string;
  accentSurface: string;
  accentGreen: string;     // Backward-compatible alias
  accentGreenSubtle: string;
  accentGreenGlow: string;

  // Semantic Status Colors (Clean & Restrained)
  success: string;
  successSubtle: string;
  warning: string;
  warningSubtle: string;
  error: string;
  errorSubtle: string;
  info: string;
  infoSubtle: string;

  // Backward-compatible semantic aliases
  accentCyan: string;
  accentCyanSubtle: string;
  accentPurple: string;
  accentPurpleSubtle: string;
  accentRed: string;
  accentRedSubtle: string;
  accentYellow: string;
  accentYellowSubtle: string;
  accentNavy: string;
  accentNavyLight: string;
  accentNavyDark: string;

  // Navigation & Interactive Bars
  bottomBarBg: string;
  bottomBarBorder: string;
  bottomBarActivePill: string;
  bottomBarActiveGlow: string;

  // Code & Terminal
  codeBg: string;
  codeBorder: string;
}

export const DARK_THEME: ThemePalette = {
  // Pure Pitch Black & Clean Grayscale System
  bgPrimary: '#000000',
  bgSecondary: '#0A0A0A',
  bgSurface: '#121212',
  surfaceElevated: '#171717',
  surfaceHover: '#262626',

  cardBg: '#121212',
  cardBorder: '#262626',
  cardSpecular: '#404040',
  bgCard: '#121212',
  bgCardHover: '#171717',
  background: '#000000',

  border: '#262626',
  borderStrong: '#404040',
  borderActive: '#FFFFFF',

  // Typography Hierarchy
  textPrimary: '#FFFFFF',
  textSecondary: '#A3A3A3',
  textMuted: '#737373',
  textDim: '#525252',
  textDisabled: '#404040',

  // Pure White Accent
  accent: '#FFFFFF',
  accentStrong: '#F5F5F5',
  accentMuted: '#D4D4D4',
  accentSurface: 'rgba(255, 255, 255, 0.10)',
  accentGreen: '#FFFFFF',
  accentGreenSubtle: 'rgba(255, 255, 255, 0.08)',
  accentGreenGlow: 'rgba(255, 255, 255, 0.20)',

  // Clean Restrained Status
  success: '#E5E5E5',
  successSubtle: 'rgba(255, 255, 255, 0.08)',
  warning: '#D4D4D4',
  warningSubtle: 'rgba(255, 255, 255, 0.08)',
  error: '#EF4444',
  errorSubtle: 'rgba(239, 68, 68, 0.12)',
  info: '#FFFFFF',
  infoSubtle: 'rgba(255, 255, 255, 0.08)',

  // Aliases
  accentCyan: '#FFFFFF',
  accentCyanSubtle: 'rgba(255, 255, 255, 0.08)',
  accentPurple: '#E5E5E5',
  accentPurpleSubtle: 'rgba(255, 255, 255, 0.08)',
  accentRed: '#EF4444',
  accentRedSubtle: 'rgba(239, 68, 68, 0.12)',
  accentYellow: '#D4D4D4',
  accentYellowSubtle: 'rgba(255, 255, 255, 0.08)',
  accentNavy: '#FFFFFF',
  accentNavyLight: '#F5F5F5',
  accentNavyDark: '#000000',

  // Navigation
  bottomBarBg: 'rgba(0, 0, 0, 0.95)',
  bottomBarBorder: '#262626',
  bottomBarActivePill: 'rgba(255, 255, 255, 0.12)',
  bottomBarActiveGlow: 'rgba(255, 255, 255, 0.18)',

  // Code
  codeBg: '#0A0A0A',
  codeBorder: '#262626',
};

export const LIGHT_THEME: ThemePalette = {
  // Pure White & Deep Charcoal System
  bgPrimary: '#FFFFFF',
  bgSecondary: '#FAFAFA',
  bgSurface: '#FFFFFF',
  surfaceElevated: '#FFFFFF',
  surfaceHover: '#F5F5F5',

  cardBg: '#FFFFFF',
  cardBorder: '#E5E5E5',
  cardSpecular: '#D4D4D4',
  bgCard: '#FFFFFF',
  bgCardHover: '#FAFAFA',
  background: '#FFFFFF',

  border: '#E5E5E5',
  borderStrong: '#A3A3A3',
  borderActive: '#000000',

  // Typography Hierarchy
  textPrimary: '#000000',
  textSecondary: '#525252',
  textMuted: '#737373',
  textDim: '#A3A3A3',
  textDisabled: '#D4D4D4',

  // Pure Black Accent
  accent: '#000000',
  accentStrong: '#171717',
  accentMuted: '#404040',
  accentSurface: 'rgba(0, 0, 0, 0.06)',
  accentGreen: '#000000',
  accentGreenSubtle: 'rgba(0, 0, 0, 0.06)',
  accentGreenGlow: 'rgba(0, 0, 0, 0.12)',

  // Clean Restrained Status
  success: '#171717',
  successSubtle: 'rgba(0, 0, 0, 0.06)',
  warning: '#404040',
  warningSubtle: 'rgba(0, 0, 0, 0.06)',
  error: '#DC2626',
  errorSubtle: 'rgba(220, 38, 38, 0.08)',
  info: '#000000',
  infoSubtle: 'rgba(0, 0, 0, 0.06)',

  // Aliases
  accentCyan: '#000000',
  accentCyanSubtle: 'rgba(0, 0, 0, 0.06)',
  accentPurple: '#171717',
  accentPurpleSubtle: 'rgba(0, 0, 0, 0.06)',
  accentRed: '#DC2626',
  accentRedSubtle: 'rgba(220, 38, 38, 0.08)',
  accentYellow: '#404040',
  accentYellowSubtle: 'rgba(0, 0, 0, 0.06)',
  accentNavy: '#000000',
  accentNavyLight: '#404040',
  accentNavyDark: '#000000',

  // Navigation
  bottomBarBg: 'rgba(255, 255, 255, 0.96)',
  bottomBarBorder: '#E5E5E5',
  bottomBarActivePill: 'rgba(0, 0, 0, 0.08)',
  bottomBarActiveGlow: 'rgba(0, 0, 0, 0.12)',

  // Code
  codeBg: '#F5F5F5',
  codeBorder: '#E5E5E5',
};

export const THEME_PALETTES = {
  dark: DARK_THEME,
  light: LIGHT_THEME,
} as const;

export const COLORS = DARK_THEME;
