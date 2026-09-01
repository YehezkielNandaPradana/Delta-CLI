import { useSettingsStore } from '../src/store/useSettingsStore';

describe('useSettingsStore cloud & multi-account', () => {
  beforeEach(() => {
    useSettingsStore.setState({
      connectionMode: 'cloud',
      accounts: [],
      activeAccountId: '',
      cloudModel: 'ag/gemini-3.7-flash-high',
    });
  });

  test('should add, switch, and delete Antigravity accounts', async () => {
    const acc1Id = await useSettingsStore.getState().addAccount({
      name: 'Primary Account',
      apiKey: 'ag-key-12345',
      baseUrl: 'https://api.antigravity.ai/v1',
      defaultModel: 'ag/gemini-3.7-flash-high',
    });

    expect(acc1Id).toBeDefined();
    expect(useSettingsStore.getState().accounts.length).toBe(1);
    expect(useSettingsStore.getState().activeAccountId).toBe(acc1Id);

    const activeAcc = useSettingsStore.getState().getActiveAccount();
    expect(activeAcc?.apiKey).toBe('ag-key-12345');

    const acc2Id = await useSettingsStore.getState().addAccount({
      name: 'Backup Account',
      apiKey: 'ag-key-67890',
      baseUrl: 'https://api.antigravity.ai/v1',
      defaultModel: 'gemini-3.7-flash-high',
    });

    expect(useSettingsStore.getState().accounts.length).toBe(2);
    await useSettingsStore.getState().setActiveAccount(acc2Id);
    expect(useSettingsStore.getState().getActiveAccount()?.name).toBe('Backup Account');

    await useSettingsStore.getState().deleteAccount(acc1Id);
    expect(useSettingsStore.getState().accounts.length).toBe(1);
  });

  test('should toggle connection mode between cloud and local', async () => {
    await useSettingsStore.getState().setConnectionMode('local');
    expect(useSettingsStore.getState().connectionMode).toBe('local');

    await useSettingsStore.getState().setConnectionMode('cloud');
    expect(useSettingsStore.getState().connectionMode).toBe('cloud');
  });
});
