import { formatDuration, cleanAnsiCodes, truncateText } from '../src/utils/formatters';

describe('formatters utility test', () => {
  test('formatDuration should convert ms to clean string', () => {
    expect(formatDuration(500)).toBe('500ms');
    expect(formatDuration(1500)).toBe('1.5s');
    expect(formatDuration(2340)).toBe('2.3s');
    expect(formatDuration(null)).toBe('');
  });

  test('cleanAnsiCodes should remove terminal escape codes', () => {
    const raw = '\x1b[32mDelta\x1b[0m Security';
    expect(cleanAnsiCodes(raw)).toBe('Delta Security');
  });

  test('truncateText should clamp string length', () => {
    expect(truncateText('Hello World', 5)).toBe('Hello...');
    expect(truncateText('Short', 10)).toBe('Short');
  });
});
