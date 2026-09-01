# Delta Mobile Modern Redesign Spec

**Date:** 2026-09-01  
**Project:** Delta Mobile (React Native + Expo)  
**Status:** Approved  

---

## 1. Overview & Purpose

Revamp Delta Mobile into a modern, responsive, fluid, and clean mobile interface. The design eliminates conventional heavy glassmorphism in favor of a refined **Liquid Glass** aesthetic (glossy specular reflections, clean refraction rims, organic fluid highlights) combined with full **Dark / Light Mode** dual theme support, smooth spring physics animations across all touchpoints, and a floating **Liquid Glass Dynamic Bottom Bar**.

### Core Boundaries
- **In Scope:**
  - Modern Dual Theme (`dark`, `light`, `system`) with runtime switching in `useSettingsStore` and `useThemeColors`.
  - Reusable `LiquidGlassCard` component with specular top highlight, refraction rim, and press spring feedback.
  - Floating `FluidBottomBar` with smooth liquid sliding pill indicator across tabs (Chat, Activity, Voice, Settings).
  - High-performance, smooth animations for message bubbles, status indicators, and screen transitions.
  - Full aesthetic elevation of Chat, Header, Input, and Settings screens.
- **Out of Scope (YAGNI):** Heavy multi-blur backdrop rendering that degrades mobile frame rates.

---

## 2. Design Tokens & Dual Theme Architecture

### 2.1 Theme Modes
- Modes: `'dark' | 'light' | 'system'`
- Persisted in `useSettingsStore` via `@react-native-async-storage/async-storage`.
- Consumed through a reactive theme hook (`src/theme/theme.ts`) returning the active color tokens.

### 2.2 Palette Specification

| Token | Dark Mode (`#0B0F17` Base) | Light Mode (`#F4F6FB` Base) |
|---|---|---|
| `bgPrimary` | `#0B0F17` (Deep Obsidian) | `#F4F6FB` (Crisp Porcelain) |
| `bgSecondary` | `#101726` | `#E8EEF5` |
| `bgSurface` | `#162032` | `#FFFFFF` |
| `cardBg` | `#141C2D` | `#FFFFFF` |
| `cardBorder` | `rgba(255, 255, 255, 0.08)` | `rgba(15, 23, 42, 0.08)` |
| `cardSpecular` | `rgba(255, 255, 255, 0.16)` | `rgba(255, 255, 255, 0.95)` |
| `textPrimary` | `#F8FAFC` | `#0F172A` |
| `textSecondary` | `#94A3B8` | `#475569` |
| `textMuted` | `#64748B` | `#94A3B8` |
| `accentGreen` | `#00F59B` (Liquid Emerald) | `#059669` |
| `accentCyan` | `#00E5FF` (Liquid Cyan) | `#0284C7` |
| `accentPurple` | `#A855F7` | `#7C3AED` |
| `accentRed` | `#FF4D6D` | `#E11D48` |
| `bottomBarBg` | `#111827` | `#FFFFFF` |
| `bottomBarBorder` | `rgba(255, 255, 255, 0.12)` | `rgba(15, 23, 42, 0.08)` |
| `bottomBarActivePill` | `rgba(0, 245, 155, 0.18)` | `rgba(5, 150, 105, 0.12)` |
| `codeBg` | `#0D131F` | `#F1F5F9` |
| `codeBorder` | `rgba(255, 255, 255, 0.06)` | `rgba(15, 23, 42, 0.06)` |

---

## 3. UI Component Specifications

### 3.1 Liquid Glass Container (`LiquidGlassCard`)
- Rounded surface (`borderRadius: 20` or `24`).
- Top specular highlight simulating liquid refraction (`borderTopWidth: 1.5`, `borderTopColor: cardSpecular`).
- Elevation drop-shadow matching light/dark atmosphere.
- Micro-press spring response (`scale: 0.98` with spring restore).

### 3.2 Floating Liquid Glass Bottom Navigation (`FluidBottomBar`)
- Floating pill anchored 16px above bottom safe area, width ~92% screen centered.
- Animated horizontal slider indicator translating smoothly to the active tab index (`Animated.spring`).
- 4 Primary Tabs:
  1. **Chat** (`chatbubble-ellipses-outline` / `chatbubble-ellipses`)
  2. **Activity** (`pulse-outline` / `pulse`)
  3. **Voice** (`mic-outline` / `mic`)
  4. **Settings** (`settings-outline` / `settings`)
- Light selection haptic feedback on tab change.

### 3.3 Modernized Chat & Input Components
- **Header**: Compact floating navigation bar with connection indicator dot and instant Dark/Light mode toggle switch.
- **Message Bubble**:
  - User: Vibrant emerald/gradient bubble with crisp white typography.
  - Delta AI: Refined Liquid Glass surface, formatted text, and high-contrast code snippet cards.
- **Chat Input**: Floating capsule input with smooth auto-expand, clear action triggers, and spring-animated Send/Stop button.

---

## 4. Navigation & Directory Layout

```
delta/mobile/
├── app/
│   ├── _layout.tsx               # Theme provider, safe area, SSE client bootstrap
│   ├── (tabs)/
│   │   ├── _layout.tsx           # Custom Floating Liquid Glass Bottom Tab Bar
│   │   ├── index.tsx             # Chat Screen
│   │   ├── activity.tsx          # Agent Activity & Tools Screen
│   │   ├── voice.tsx             # Voice & Speech Screen
│   │   └── settings.tsx          # Settings & Theme Toggle Screen
│   └── +not-found.tsx
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── LiquidGlassCard.tsx   # Reusable Liquid Glass container
│   │   │   ├── FluidBottomBar.tsx    # Sliding liquid pill bottom bar
│   │   │   └── Header.tsx            # Modern header with theme toggle
│   │   ├── chat/
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── CodeBlock.tsx
│   │   └── agent/
│   │       ├── AgentActivity.tsx
│   │       └── StatusPill.tsx
│   ├── theme/
│   │   ├── colors.ts             # Palette definitions (Dark & Light)
│   │   └── theme.ts              # Theme hook & context utilities
│   ├── store/
│   │   ├── useSettingsStore.ts   # Persisted theme ('dark' | 'light' | 'system')
│   │   ├── useChatStore.ts
│   │   └── useConnectionStore.ts
│   └── services/
└── tests/
```

---

## 5. Verification Plan
- **Theme Switch**: Test instantaneous re-theming across all components between Light and Dark mode.
- **Bottom Navigation**: Verify fluid sliding animation of the active tab pill across all 4 screens.
- **Performance & Smoothness**: Ensure 60fps interaction with no heavy lag or dropped frames.
