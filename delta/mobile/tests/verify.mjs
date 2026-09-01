import assert from 'node:assert';
import { DARK_THEME, LIGHT_THEME, THEME_PALETTES } from '../src/theme/colors.js';
import { formatDuration, cleanAnsiCodes, truncateText } from '../src/utils/formatters.js';

console.log('🧪 Running Delta Mobile Verification Tests...');

// 1. Test Themes
assert.strictEqual(DARK_THEME.bgPrimary, '#0b0f17', 'DARK_THEME bgPrimary match');
assert.strictEqual(LIGHT_THEME.bgPrimary, '#f4f6fb', 'LIGHT_THEME bgPrimary match');
assert.strictEqual(DARK_THEME.accentGreen, '#00f59b', 'DARK_THEME accentGreen match');
assert.strictEqual(LIGHT_THEME.accentGreen, '#059669', 'LIGHT_THEME accentGreen match');
assert.ok(DARK_THEME.cardSpecular, 'DARK_THEME specular highlight exists');
assert.ok(LIGHT_THEME.cardSpecular, 'LIGHT_THEME specular highlight exists');
assert.strictEqual(THEME_PALETTES.dark, DARK_THEME, 'THEME_PALETTES.dark match');
assert.strictEqual(THEME_PALETTES.light, LIGHT_THEME, 'THEME_PALETTES.light match');
console.log('✅ Theme Palette tests passed');

// 2. Test Formatters
assert.strictEqual(formatDuration(500), '500ms', 'formatDuration 500ms');
assert.strictEqual(formatDuration(1500), '1.5s', 'formatDuration 1.5s');
assert.strictEqual(cleanAnsiCodes('\x1b[32mDelta\x1b[0m'), 'Delta', 'cleanAnsiCodes stripped');
assert.strictEqual(truncateText('Hello World', 5), 'Hello...', 'truncateText works');
console.log('✅ Formatter utility tests passed');

console.log('🎉 All mobile unit assertions passed successfully!');
