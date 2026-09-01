import { useColorScheme } from 'react-native';
import { useSettingsStore } from '../store/useSettingsStore';
import { DARK_THEME, LIGHT_THEME, ThemePalette, THEME_PALETTES } from './colors';

export function useThemeColors(): {
  colors: ThemePalette;
  isDark: boolean;
  theme: 'dark' | 'light' | 'system';
  setTheme: (theme: 'dark' | 'light' | 'system') => void;
  toggleTheme: () => void;
} {
  const systemScheme = useColorScheme();
  const theme = useSettingsStore((state) => state.theme);
  const setTheme = useSettingsStore((state) => state.setTheme);

  const isDark = theme === 'system' ? systemScheme !== 'light' : theme === 'dark';
  const colors = isDark ? DARK_THEME : LIGHT_THEME;

  const toggleTheme = () => {
    if (theme === 'dark') {
      setTheme('light');
    } else if (theme === 'light') {
      setTheme('system');
    } else {
      setTheme('dark');
    }
  };

  return {
    colors,
    isDark,
    theme,
    setTheme,
    toggleTheme,
  };
}

export { DARK_THEME, LIGHT_THEME, THEME_PALETTES };
