---
name: Delta Technical Minimalist
version: 2.0.0
archetype: Operate & Monitor
colors:
  surface-base: '#09090b'
  surface-card: '#111114'
  surface-elevated: '#18181b'
  surface-high: '#222226'
  border-subtle: 'rgba(255, 255, 255, 0.08)'
  border-active: 'rgba(255, 255, 255, 0.16)'
  border-accent: 'rgba(44, 203, 238, 0.40)'
  text-primary: '#ededed'
  text-secondary: '#a1a1aa'
  text-muted: '#71717a'
  text-dim: '#52525b'
  accent: '#2ccbee'
  accent-dim: 'rgba(44, 203, 238, 0.12)'
  accent-hover: '#22b5d4'
  status-success: '#34d399'
  status-warning: '#fbbf24'
  status-danger: '#f87171'
  status-info: '#38bdf8'
typography:
  font-sans: Geist, -apple-system, BlinkMacSystemFont, sans-serif
  font-mono: JetBrains Mono, SF Mono, monospace
  sizes:
    title-sm:
      fontSize: 14px
      fontWeight: '600'
      lineHeight: 20px
      letterSpacing: '-0.01em'
    body-sm:
      fontSize: 13px
      fontWeight: '400'
      lineHeight: 18px
    code-sm:
      fontSize: 12px
      fontWeight: '400'
      lineHeight: 16px
    label-caps:
      fontSize: 10px
      fontWeight: '500'
      lineHeight: 14px
      letterSpacing: '0.05em'
      textTransform: uppercase
radii:
  sm: 2px
  DEFAULT: 4px
  md: 6px
  lg: 8px
motion:
  easing: 'cubic-bezier(0.16, 1, 0.3, 1)'
  duration-micro: 75ms
  duration-transition: 150ms
  hardware-compositor: 'transform, opacity only'
---

# Delta CLI Workstation Design System (Anti-Slop Edition)

## 1. Zero AI Slop Doctrine
Delta is an AI-powered Cybersecurity Assessment CLI and operational workstation. The design adheres strictly to the **Anti-Slop UI & Motion Craft Doctrine**:

- **No AI Clichés:** No generic purple/indigo gradients, no unearned glassmorphism (`backdrop-filter: blur`), no puffy 16px–24px candy radii, and no fake AI cheerleading terms (e.g. "Thinking...", "Analyzing request...", or "Delta Agent Ready").
- **Surface Archetype (Operate & Monitor):** Real estate is dedicated to high-density operational telemetry, execution logs, packet streams, and structured tool outputs. No promotional marketing heros or arbitrary 3-card feature grids.
- **Architectural Dark Palette:** Built upon solid, calm architectural surfaces:
  - Base: `#09090b`
  - Card/Panels: `#111114`
  - Elevated/Modals: `#18181b`
  - Separators: Crisp 1px hairline borders (`rgba(255, 255, 255, 0.08)`) instead of diffuse drop shadows.
- **Restrained Monochrome with Single Technical Accent:** Pure monochrome foundation paired exclusively with Delta Cyan (`#2ccbee`) for active indicators and operational badges.

## 2. Layout Structure (3-Column Precision Workstation)
1. **Header (36px–44px):** Minimal status telemetry, active target badge, scope verification indicator, and quick command palette trigger (`⌘K`).
2. **Left Navigation (w-52):** Compact operational routing (Stream, Network, Vulnerabilities, Evidence Files, Reports) and workspace environment context.
3. **Center Execution Canvas:** Unified operational stream. Integrates live activity telemetry, real-time tool execution cards, raw output collapsible blocks, and terminal-style command input (`> `).
4. **Right Inspector Panel (w-72):** Real-time target metadata (Host, IPv4, TLS, Web Server), finding severity inventory, and minimal line telemetry chart.

## 3. Hardware-Accelerated 60 FPS Motion
- **Compositor Invariant:** Strictly animate ONLY `transform` and `opacity`. Layout properties (`width`, `height`, `margin`, `padding`) must never be animated.
- **Spring Curves:** Fast entrance with gentle deceleration using `cubic-bezier(0.16, 1, 0.3, 1)` within 75ms to 150ms.
- **Tactile Response:** Interactive buttons and chips utilize `active:scale-[0.98]` micro-feedback for instant physical confirmation.
