# Design Spec: Delta Mobile Direct Antigravity Cloud & Multi-Account Management

**Date:** 2026-09-01  
**Status:** Approved  
**Author:** Delta CLI & Mobile Core Team  

---

## 1. Objective & Scope

Allow the Delta Mobile App (Expo/React Native) to operate anywhere with internet access **without requiring a local Delta server or local 9Router instance**, by executing direct OpenAI-compatible API calls to Antigravity endpoints hosting `gemini-3.7-flash-high`.

### Core Requirements
1. **Dual Connection Mode**: Switch seamlessly between **Direct Cloud** (Internet only) and **Local Server** (FastAPI backend).
2. **Antigravity Multi-Account Management**: Store, add, edit, delete, and switch between multiple Antigravity API accounts directly in mobile storage (`AsyncStorage`).
3. **Direct Cloud Chat Engine**: Direct streaming and standard chat completions via HTTPS OpenAI-compatible endpoint with Delta system prompt and history.
4. **Resilient UI**: Suppress local 9Router offline warnings when in Cloud mode; provide clear account and model status indicators.

---

## 2. Architecture & Data Structures

### 2.1 Types (`src/types/cloud.ts` & `src/types/settings.ts`)

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

### 2.2 Store Extension (`src/store/useSettingsStore.ts`)

New State Properties:
- `connectionMode: ConnectionMode` (Default: `'cloud'`)
- `accounts: AntigravityAccount[]`
- `activeAccountId: string`
- `cloudModel: string` (Default: `'ag/gemini-3.7-flash-high'`)

Actions:
- `setConnectionMode(mode: ConnectionMode): Promise<void>`
- `addAccount(account: Omit<AntigravityAccount, 'id'>): Promise<string>`
- `updateAccount(id: string, updates: Partial<AntigravityAccount>): Promise<void>`
- `deleteAccount(id: string): Promise<void>`
- `setActiveAccount(id: string): Promise<void>`
- `setCloudModel(model: string): Promise<void>`
- Helper getter: `getActiveAccount(): AntigravityAccount | undefined`

---

## 3. Direct Cloud API Client (`src/services/api/directCloudClient.ts`)

### 3.1 Flow & Execution
1. Fetch active account from `useSettingsStore`.
2. Fallback check: If no account or missing API key, raise descriptive error directing user to Settings.
3. Construct OpenAI-compatible Chat Completion Payload:
   - `model`: Selected cloud model (`ag/gemini-3.7-flash-high` or `gemini-3.7-flash-high`).
   - `messages`: Delta System Prompt (`DELTA_CAPABILITIES`) + formatted user conversation history.
   - `temperature`: 0.7
   - `stream`: false (or fetch streaming reader with callback).
4. Send request via standard `fetch` with `Authorization: Bearer <apiKey>` to `${baseUrl}/chat/completions`.
5. Return formatted text output or throw readable error.

---

## 4. UI & Screen Updates

### 4.1 Settings Screen (`app/(tabs)/settings.tsx`)
- **Connection Mode Selector**: Top segmented control [ Cloud Direct (Internet) ] vs [ Local Server ].
- **Antigravity Accounts Card**:
  - List of saved accounts with active radio/checkmark.
  - Quick tap to switch active account.
  - "Add Account" button opening modal/form (Name, API Key, Base URL, Model).
  - Edit and Delete action buttons per account.
- **Model Selection for Cloud**:
  - Default preset: `ag/gemini-3.7-flash-high`, `gemini-3.7-flash-high`, `google/gemini-3.7-flash`.
  - Custom model ID input.

### 4.2 Chat Screen (`app/(tabs)/index.tsx` & `src/services/api/chatApi.ts`)
- `chatApi.ts` detects `connectionMode`.
  - In `cloud` mode: delegates directly to `directCloudClient.sendDirectCloudMessage()`.
  - In `local` mode: delegates to `apiRequest('/api/chat')`.
- Suppress `RouterAlertModal` auto-popup when in `cloud` mode since local 9Router is not needed.

---

## 5. Security & Persistence

- Accounts and Keys stored in device's local `AsyncStorage` with key `@delta_settings`.
- No local backend or external intermediary server required.
- API keys masked in UI (`••••••••`) with toggle to show/hide.

---

## 6. Verification Plan

1. **Unit Tests**:
   - Verify account CRUD actions in `useSettingsStore`.
   - Verify active account fallback logic and switching.
   - Verify request payload construction in `directCloudClient`.
2. **Integration Checks**:
   - Send chat message in Cloud Mode -> confirms direct payload output.
   - Switch active account -> confirms subsequent requests use updated API key.
   - Switch back to Local Mode -> confirms local server routing untouched.
