import { useChatStore } from '../src/store/useChatStore';

describe('useChatStore test', () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages();
  });

  test('should add messages properly', () => {
    const id = useChatStore.getState().addMessage({
      sender: 'user',
      text: 'Scan localhost',
    });

    expect(id).toBeDefined();
    const msgs = useChatStore.getState().messages;
    expect(msgs.length).toBe(1);
    expect(msgs[0].text).toBe('Scan localhost');
    expect(msgs[0].sender).toBe('user');
  });

  test('should update steps and aggregate into execution', () => {
    useChatStore.getState().startExecution('exec_1');
    expect(useChatStore.getState().isGenerating).toBe(true);

    useChatStore.getState().updateStep({
      id: 'step_1',
      status: 'running',
      label: 'Analyzing request',
    });

    expect(useChatStore.getState().activeSteps['step_1'].label).toBe('Analyzing request');

    useChatStore.getState().finishExecution();
    expect(useChatStore.getState().isGenerating).toBe(false);
  });
});
