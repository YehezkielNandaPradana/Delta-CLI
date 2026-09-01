import { DARK_THEME, LIGHT_THEME, THEME_PALETTES } from '../src/theme/colors';

describe('Theme System', () => {
  it('should have complete tokens in DARK_THEME with Navy palette', () => {
    expect(DARK_THEME.bgPrimary).toBe('#070d19');
    expect(DARK_THEME.cardBg).toBe('#0f1c35');
    expect(DARK_THEME.cardSpecular).toBeDefined();
    expect(DARK_THEME.bottomBarBg).toBeDefined();
    expect(DARK_THEME.bottomBarActivePill).toBeDefined();
    expect(DARK_THEME.accentGreen).toBe('#3b82f6');
    expect(DARK_THEME.textPrimary).toBe('#f8fafc');
  });

  it('should have complete tokens in LIGHT_THEME with Navy palette', () => {
    expect(LIGHT_THEME.bgPrimary).toBe('#f0f5fc');
    expect(LIGHT_THEME.cardBg).toBe('#ffffff');
    expect(LIGHT_THEME.cardSpecular).toBeDefined();
    expect(LIGHT_THEME.bottomBarBg).toBeDefined();
    expect(LIGHT_THEME.bottomBarActivePill).toBeDefined();
    expect(LIGHT_THEME.accentGreen).toBe('#1d4ed8');
    expect(LIGHT_THEME.textPrimary).toBe('#0f172a');
  });

  it('should expose THEME_PALETTES map', () => {
    expect(THEME_PALETTES.dark).toBe(DARK_THEME);
    expect(THEME_PALETTES.light).toBe(LIGHT_THEME);
  });
});
