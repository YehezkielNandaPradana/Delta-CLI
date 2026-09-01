# Delta Mobile Modern Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Delta Mobile into a modern, responsive, fluid, and clean mobile interface featuring a Liquid Glass aesthetic, dynamic Dark/Light dual themes, smooth spring physics animations, and a floating Liquid Glass Dynamic Bottom Navigation Bar.

**Architecture:** A standalone React Native + Expo app located at `delta/mobile/`. Centralizes theme palette state in `src/theme/colors.ts` and `src/theme/theme.ts` coupled to Zustand `useSettingsStore`. Implements reusable `LiquidGlassCard` and `FluidBottomBar` with pure React Native `Animated` physics for 60fps cross-platform performance.

**Tech Stack:** React Native 0.74+, Expo SDK 51+, Expo Router, TypeScript, Zustand, `@react-native-async-storage/async-storage`, `@expo/vector-icons`, Jest for testing.

## Global Constraints
- Target Location: `delta/mobile/`
- Zero external native animation library dependencies (pure React Native `Animated` / `LayoutAnimation` for maximum reliability on Web, Android, iOS).
- Dual Theme: `dark` (Cosmic Obsidian `#0B0F17`), `light` (Crisp Porcelain `#F4F6FB`), `system`.
- Branding rule: Strict `DELTA` text (no `Δ` character replacements).
- Non-breaking backend compatibility with `delta/web/server.py`.

---

### Task 1: Dual Theme System & Theme Hook

**Files:**
- Create/Modify: `delta/mobile/src/theme/colors.ts`
- Create: `delta/mobile/src/theme/theme.ts`
- Modify: `delta/mobile/src/store/useSettingsStore.ts`
- Test: `delta/mobile/tests/theme.test.ts`

**Interfaces:**
- Produces:
  - `THEME_PALETTES`: `{ dark: ThemePalette, light: ThemePalette }`
  - `useThemeColors()`: returns `{ colors: ThemePalette, isDark: boolean, theme: 'dark'|'light'|'system', toggleTheme: () => void }`
  - `useSettingsStore.setTheme(theme: 'dark'|'light'|'system')`

- [ ] **Step 1: Write unit test for theme resolution**

Create `delta/mobile/tests/theme.test.ts` testing dark/light color resolution and toggling.

- [ ] **Step 2: Implement `src/theme/colors.ts` with Dark & Light palettes**

Implement full token definitions for both modes.

- [ ] **Step 3: Update `src/store/useSettingsStore.ts` with `theme` state and persistence**

Add `theme: 'dark' | 'light' | 'system'` to settings store with default `'dark'`.

- [ ] **Step 4: Create `src/theme/theme.ts` with `useThemeColors` hook**

Resolves active colors considering system color scheme and store preference.

- [ ] **Step 5: Run test to verify it passes**

Run `npm --prefix delta/mobile test tests/theme.test.ts`.

- [ ] **Step 6: Commit**

```bash
git add delta/mobile/src/theme/ delta/mobile/src/store/useSettingsStore.ts delta/mobile/tests/theme.test.ts
git commit -m "feat(mobile): add dual theme system and useThemeColors hook"
```

---

### Task 2: Liquid Glass Card & Modern Header

**Files:**
- Create: `delta/mobile/src/components/common/LiquidGlassCard.tsx`
- Modify: `delta/mobile/src/components/common/Header.tsx`

**Interfaces:**
- Consumes: `useThemeColors()` from `src/theme/theme.ts`
- Produces:
  - `<LiquidGlassCard specular={true} onPress={...}>{children}</LiquidGlassCard>`
  - `<Header title="DELTA" showThemeToggle={true} />`

- [ ] **Step 1: Implement `LiquidGlassCard.tsx`**

Build container with specular top border reflection, ambient drop-shadow, and spring scale touch feedback (`Animated.spring`).

- [ ] **Step 2: Update `Header.tsx`**

Update Header with connection status indicator dot and animated theme toggle button (Sun/Moon).

- [ ] **Step 3: Commit**

```bash
git add delta/mobile/src/components/common/
git commit -m "feat(mobile): create LiquidGlassCard and modernize Header"
```

---

### Task 3: Floating Liquid Glass Bottom Navigation Bar

**Files:**
- Create: `delta/mobile/src/components/common/FluidBottomBar.tsx`
- Modify: `delta/mobile/app/(tabs)/_layout.tsx`

**Interfaces:**
- Consumes: Expo Router `BottomTabBarProps`, `useThemeColors()`, `useSettingsStore()` (for haptic feedback)
- Produces:
  - Custom floating bottom tab bar with animated sliding liquid pill indicator.

- [ ] **Step 1: Implement `FluidBottomBar.tsx`**

Implement floating capsule anchored 16px above bottom safe area with 4 tabs (Chat, Activity, Voice, Settings) and horizontal translation spring animation for the active pill indicator.

- [ ] **Step 2: Configure `app/(tabs)/_layout.tsx`**

Wire `tabBar={(props) => <FluidBottomBar {...props} />}` into Expo Router `Tabs`.

- [ ] **Step 3: Commit**

```bash
git add delta/mobile/src/components/common/FluidBottomBar.tsx delta/mobile/app/\(tabs\)/_layout.tsx
git commit -m "feat(mobile): implement floating Liquid Glass bottom navigation bar"
```

---

### Task 4: Modernized Chat & Agent Activity Components

**Files:**
- Modify: `delta/mobile/src/components/chat/MessageBubble.tsx`
- Modify: `delta/mobile/src/components/chat/ChatInput.tsx`
- Modify: `delta/mobile/src/components/chat/MessageList.tsx`
- Modify: `delta/mobile/src/components/chat/CodeBlock.tsx`
- Modify: `delta/mobile/src/components/agent/StatusPill.tsx`
- Modify: `delta/mobile/src/components/agent/AgentActivity.tsx`

**Interfaces:**
- Consumes: `useThemeColors()`
- Produces:
  - Adaptive Dark/Light chat bubbles with Liquid Glass styling for assistant responses.
  - Floating pill ChatInput with spring send/stop action button.
  - Smooth pulsating status indicators and collapsible activity execution logs.

- [ ] **Step 1: Update `MessageBubble.tsx` and `CodeBlock.tsx`**

Apply liquid card styling to assistant message, vibrant emerald bubble to user, and copyable high-contrast code snippets.

- [ ] **Step 2: Update `ChatInput.tsx`**

Style as floating rounded input capsule with dynamic mic/send toggle, multiline expanding height, and spring feedback.

- [ ] **Step 3: Update `StatusPill.tsx` and `AgentActivity.tsx`**

Add pulsing beacon and collapsible agent step cards.

- [ ] **Step 4: Commit**

```bash
git add delta/mobile/src/components/chat/ delta/mobile/src/components/agent/
git commit -m "feat(mobile): modernize chat, input, and agent activity components"
```

---

### Task 5: Tab Screens (Chat, Activity, Voice, Settings) & Root Layout

**Files:**
- Modify: `delta/mobile/app/_layout.tsx`
- Modify: `delta/mobile/app/(tabs)/index.tsx` (Chat Screen)
- Create: `delta/mobile/app/(tabs)/activity.tsx` (Activity / Logs Screen)
- Create: `delta/mobile/app/(tabs)/voice.tsx` (Voice / VTuber Screen)
- Create: `delta/mobile/app/(tabs)/settings.tsx` (Settings & Theme Screen)

**Interfaces:**
- Consumes: `useThemeColors()`, `useSettingsStore()`, `useChatStore()`, `useConnectionStore()`

- [ ] **Step 1: Update `app/_layout.tsx`**

Sync `StatusBar` style (light/dark) dynamically with theme mode and wrap `SafeAreaProvider` background.

- [ ] **Step 2: Update `app/(tabs)/index.tsx` (Chat)**

Adopt dynamic theme colors and clean padding to accommodate floating bottom bar.

- [ ] **Step 3: Create `app/(tabs)/activity.tsx` (Activity & Logs)**

Display detailed timeline of agent thought chains, tool operations, and system events.

- [ ] **Step 4: Create `app/(tabs)/voice.tsx` (Voice Interaction)**

Display animated audio wave pulse, connection status, and voice mode trigger.

- [ ] **Step 5: Create `app/(tabs)/settings.tsx` (Settings & Theme Switcher)**

Interactive Dark/Light/System theme selector cards, server host configuration, and haptics toggle.

- [ ] **Step 6: Commit**

```bash
git add delta/mobile/app/
git commit -m "feat(mobile): build complete tab screens with dual theme support"
```

---

### Task 6: Verification & Test Suite

**Files:**
- Modify: `delta/mobile/tests/store.test.ts`
- Modify: `delta/mobile/tests/formatters.test.ts`

- [ ] **Step 1: Run all unit tests**

Run `npm --prefix delta/mobile test`.
Expected: All tests PASS.

- [ ] **Step 2: Run TypeScript typecheck**

Run `npm --prefix delta/mobile run typecheck` (or `tsc --noEmit`).
Expected: Zero TypeScript errors.

- [ ] **Step 3: Commit final updates**

```bash
git add delta/mobile/tests/
git commit -m "test(mobile): verify theme and store suites"
```
