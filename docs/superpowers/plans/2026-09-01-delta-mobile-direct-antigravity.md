# Delta Mobile Direct Antigravity & Multi-Account Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Direct Antigravity Cloud execution (`ag/gemini-3.7-flash-high`) and Multi-Account API Key management in Delta Mobile App without requiring a local server.

**Architecture:** Extend Zustand `useSettingsStore` to store Antigravity accounts & dual-mode connection state (`cloud` vs `local`). Create `directCloudClient.ts` to construct OpenAI/Antigravity-compatible completion requests. Wire `chatApi.ts` and `app/(tabs)/settings.tsx` to allow adding/switching accounts and selecting models seamlessly.

**Tech Stack:** React Native / Expo, TypeScript, Zustand, AsyncStorage, Fetch API.

## Global Constraints
- Target platform: iOS, Android, Web (Expo)
- Model identifier: `ag/gemini-3.7-flash-high` and `gemini-3.7-flash-high`
- Default Antigravity Base URL: `https://api.antigravity.ai/v1`
- Storage Key: `@delta_settings`

---

### Task 1: Add Cloud & Multi-Account Types and Extend Settings Store

**Files:**
- Create: `delta/mobile/src/types/cloud.ts`
- Modify: `delta/mobile/src/store/useSettingsStore.ts`
- Test: `delta/mobile/tests/settings_store.test.ts`

**Interfaces:**
- Consumes: `@react-native-async-storage/async-storage`, `zustand`
- Produces: `AntigravityAccount`, `ConnectionMode`, `useSettingsStore` actions (`setConnectionMode`, `addAccount`, `updateAccount`, `deleteAccount`, `setActiveAccount`, `getActiveAccount`)

- [ ] **Step 1: Write test for multi-account and connection mode management**

Create `delta/mobile/tests/settings_store.test.ts`:
```typescript
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
```

- [ ] **Step 2: Create type definitions in `delta/mobile/src/types/cloud.ts`**

```typescript
export interface AntigravityAccount {
  id: string;
  name: string;
  apiKey: string;
  baseUrl: string;
  defaultModel: string;
}

export type ConnectionMode = 'cloud' | 'local';
```

- [ ] **Step 3: Update `delta/mobile/src/store/useSettingsStore.ts` with account management actions**

Implement the state interface, default account creation, and persistence logic.

- [ ] **Step 4: Run typecheck and tests**

Run: `npm --prefix delta/mobile run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/mobile/src/types/cloud.ts delta/mobile/src/store/useSettingsStore.ts delta/mobile/tests/settings_store.test.ts
git commit -m "feat(mobile): add direct cloud and multi-account state management in useSettingsStore"
```

---

### Task 2: Implement Direct Cloud AI Client

**Files:**
- Create: `delta/mobile/src/services/api/directCloudClient.ts`
- Modify: `delta/mobile/src/services/api/chatApi.ts`
- Test: `delta/mobile/tests/direct_cloud_client.test.ts`

**Interfaces:**
- Consumes: `useSettingsStore`, `AntigravityAccount`, `ChatResponse`
- Produces: `sendDirectCloudMessage(message: string, executionId?: string): Promise<ChatResponse>`

- [ ] **Step 1: Write test for directCloudClient payload and response handling**

Create `delta/mobile/tests/direct_cloud_client.test.ts`:
```typescript
import { formatDirectChatPayload } from '../src/services/api/directCloudClient';

describe('directCloudClient payload formatter', () => {
  test('should construct valid OpenAI-compatible chat completion payload', () => {
    const payload = formatDirectChatPayload('Hello Delta', 'ag/gemini-3.7-flash-high');
    expect(payload.model).toBe('ag/gemini-3.7-flash-high');
    expect(payload.messages.length).toBeGreaterThanOrEqual(2);
    expect(payload.messages[0].role).toBe('system');
    expect(payload.messages[payload.messages.length - 1].content).toBe('Hello Delta');
  });
});
```

- [ ] **Step 2: Implement `delta/mobile/src/services/api/directCloudClient.ts`**

Include:
- System prompt for Delta Security Analyst.
- `formatDirectChatPayload(message, model)` helper.
- `sendDirectCloudMessage(message, executionId)` using standard `fetch` with Bearer Auth against active account's `baseUrl`.
- Robust error handling for rate limits, invalid keys, and network issues.

- [ ] **Step 3: Update `delta/mobile/src/services/api/chatApi.ts`**

Route requests based on `connectionMode`:
- If `cloud` -> call `sendDirectCloudMessage()`.
- If `local` -> call `apiRequest<ChatResponse>('/api/chat')`.

- [ ] **Step 4: Run typecheck**

Run: `npm --prefix delta/mobile run typecheck`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/mobile/src/services/api/directCloudClient.ts delta/mobile/src/services/api/chatApi.ts delta/mobile/tests/direct_cloud_client.test.ts
git commit -m "feat(mobile): implement direct cloud client for Antigravity gemini-3.7-flash-high"
```

---

### Task 3: Build Account Management UI & Dual-Mode Toggle in Settings

**Files:**
- Create: `delta/mobile/src/components/settings/AccountManagerModal.tsx`
- Modify: `delta/mobile/app/(tabs)/settings.tsx`
- Modify: `delta/mobile/app/(tabs)/index.tsx`

**Interfaces:**
- Consumes: `useSettingsStore`, `AntigravityAccount`, `LiquidGlassCard`
- Produces: Visual account switcher, Add/Edit Account Modal, Connection mode switch.

- [ ] **Step 1: Create `AccountManagerModal.tsx`**

Modal supporting:
- Input for Account Name, API Key (with secure text toggle), Base URL (preset to `https://api.antigravity.ai/v1`), and Default Model.
- Add / Update / Cancel actions.

- [ ] **Step 2: Update `delta/mobile/app/(tabs)/settings.tsx`**

- Add Top segmented control: **[ Direct Cloud (Internet) ]** vs **[ Local Server ]**.
- If in **Direct Cloud** mode:
  - Render **Antigravity Accounts Card**: list saved accounts with active checkmark, "Add Account" button, switch account on tap, edit/delete actions.
  - Render **Cloud Model Selector**: options `ag/gemini-3.7-flash-high`, `gemini-3.7-flash-high`, and custom model input.
- If in **Local Server** mode:
  - Render existing 9Router Diagnostics & Local Server URL controls.

- [ ] **Step 3: Update `delta/mobile/app/(tabs)/index.tsx`**

- Check `connectionMode`. If `connectionMode === 'cloud'`, suppress the automatic 9Router offline warning modal so the user can chat freely over internet.

- [ ] **Step 4: Run typecheck & validation**

Run: `npm --prefix delta/mobile run typecheck`
Expected: PASS with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add delta/mobile/src/components/settings/AccountManagerModal.tsx delta/mobile/app/\(tabs\)/settings.tsx delta/mobile/app/\(tabs\)/index.tsx
git commit -m "feat(mobile): add Antigravity multi-account management UI and connection mode switcher"
```
