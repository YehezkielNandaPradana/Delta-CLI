import { formatDirectChatPayload } from '../src/services/api/directCloudClient';

describe('directCloudClient payload formatting', () => {
  test('should construct valid OpenAI-compatible chat completion payload with system prompt', () => {
    const payload = formatDirectChatPayload('Scan target 192.168.1.1', 'ag/gemini-3.7-flash-high');

    expect(payload.model).toBe('ag/gemini-3.7-flash-high');
    expect(payload.stream).toBe(false);
    expect(payload.messages.length).toBe(2);
    expect(payload.messages[0].role).toBe('system');
    expect(payload.messages[0].content).toContain('Delta is an AI-powered Cyber Security');
    expect(payload.messages[1].role).toBe('user');
    expect(payload.messages[1].content).toBe('Scan target 192.168.1.1');
  });

  test('should maintain conversation history', () => {
    const history = [
      { role: 'user' as const, content: 'Who are you?' },
      { role: 'assistant' as const, content: 'I am Delta.' },
    ];
    const payload = formatDirectChatPayload('Tell me more', 'gemini-3.7-flash-high', history);

    expect(payload.model).toBe('gemini-3.7-flash-high');
    expect(payload.messages.length).toBe(4);
    expect(payload.messages[1].content).toBe('Who are you?');
    expect(payload.messages[2].content).toBe('I am Delta.');
    expect(payload.messages[3].content).toBe('Tell me more');
  });
});
