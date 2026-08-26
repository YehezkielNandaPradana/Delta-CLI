---
name: Delta
colors:
  surface: '#101416'
  surface-dim: '#101416'
  surface-bright: '#363a3c'
  surface-container-lowest: '#0b0f11'
  surface-container-low: '#191c1e'
  surface-container: '#1d2022'
  surface-container-high: '#272a2d'
  surface-container-highest: '#323538'
  on-surface: '#e0e3e6'
  on-surface-variant: '#bbc9ce'
  inverse-surface: '#e0e3e6'
  inverse-on-surface: '#2d3133'
  outline: '#869398'
  outline-variant: '#3c494d'
  surface-tint: '#41d7fa'
  primary: '#84e4ff'
  on-primary: '#003641'
  primary-container: '#2ccbee'
  on-primary-container: '#005262'
  inverse-primary: '#00687b'
  secondary: '#c5c6cb'
  on-secondary: '#2e3134'
  secondary-container: '#494c4f'
  on-secondary-container: '#babcc0'
  tertiary: '#ffcd9c'
  on-tertiary: '#492900'
  tertiary-container: '#ffa73f'
  on-tertiary-container: '#6d4000'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#afecff'
  primary-fixed-dim: '#41d7fa'
  on-primary-fixed: '#001f27'
  on-primary-fixed-variant: '#004e5d'
  secondary-fixed: '#e1e2e7'
  secondary-fixed-dim: '#c5c6cb'
  on-secondary-fixed: '#191c1f'
  on-secondary-fixed-variant: '#44474a'
  tertiary-fixed: '#ffdcbd'
  tertiary-fixed-dim: '#ffb86d'
  on-tertiary-fixed: '#2c1600'
  on-tertiary-fixed-variant: '#683c00'
  background: '#101416'
  on-background: '#e0e3e6'
  surface-variant: '#323538'
typography:
  headline-sm:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  sidebar-width: 240px
  inspector-width: 320px
  gutter: 1px
---

## Brand & Style

The design system is a high-utility, developer-centric framework built for speed, precision, and deep focus. It targets power users who prioritize information density and system transparency over decorative elements.

The aesthetic is **Technical Minimalism**. It draws inspiration from high-performance productivity tools like modern IDEs and command-line interfaces. The emotional response should be one of "quiet competence"—the UI stays out of the way, providing a stable, low-distraction environment for complex AI-assisted workflows.

Visual principles:
- **Density:** High information density with compact spacing and reduced visual noise.
- **Precision:** Mathematical alignment, 1px strokes, and monospaced accents.
- **Subtlety:** Interaction feedback is communicated through slight tonal shifts rather than heavy shadows or vibrant colors.
- **Utility:** Every element serves a functional purpose; decorative flourishes are strictly avoided.

## Colors

The palette is a strictly "dark-first" implementation designed for long-duration use without eye strain. 

- **Primary Background:** #0B0D0F is the foundation, providing a deep, near-black canvas.
- **Secondary Background:** #111417 is used for structural panels (sidebars, inspector, footer).
- **Accents:** A restrained technical teal (#2CCBEE) represents Delta’s presence. It is used sparingly for active states, notifications, and success indicators.
- **Borders:** #24282D provides structural definition without high-contrast distraction.
- **Typography:** Three tiers of grey ensure a clear information hierarchy, moving from high-contrast white (#E6E8EB) to a deeply muted charcoal (#5F6670) for non-essential metadata.

## Typography

This design system utilizes a dual-font strategy to balance readability with a technical feel.

- **Primary UI (Geist):** Used for most interface elements, navigation, and primary content. It provides excellent legibility at small sizes.
- **Technical/Code (JetBrains Mono):** Used for execution logs, file paths, terminal blocks, and status indicators. 

Avoid large font sizes; the maximum size for typical headers is 18px. Data-heavy views should default to `body-sm` (13px) to maximize screen real estate. Use `label-caps` for metadata headers and sidebar categories to provide distinct visual separation.

## Layout & Spacing

The layout follows a strict **Fixed-Panel Grid** system. The workspace is divided into functional regions (Sidebar, Editor/Main, Inspector, Terminal) separated by 1px borders.

- **Sidebar:** Fixed width (240px), collapsible.
- **Main Area:** Fluid, adapts to fill remaining space between panels.
- **Gutter:** Use the 1px border (#24282D) as the primary divider between all major components.
- **Rhythm:** An 8px base unit is used for padding and margins, but 4px increments are allowed for tight technical components like status bars or terminal lines.

Elements should be aligned to the pixel grid to maintain the crisp, "engineered" appearance.

## Elevation & Depth

This design system rejects traditional shadows and depth. It uses a **Tonal Layering** approach to convey hierarchy.

- **Surface 0 (Base):** #0B0D0F for the main background.
- **Surface 1 (Panels):** #111417 for sidebars, headers, and footer bars.
- **Surface 2 (Active/Popup):** #1C2025 for tooltips, menus, and modals.

Instead of shadows, use 1px solid borders (#24282D) to define boundaries. Active states or focused inputs may use a 1px teal border or a subtle background tint, but never a glow or blur effect.

## Shapes

The shape language is industrial and geometric.

- **Base Radius:** 4px to 6px is used for buttons, input fields, and container corners.
- **Interactive Elements:** Use a consistent 4px radius (`rounded-sm`).
- **Outer Containers:** Large modal or panel containers use a 6px radius (`rounded-lg`).
- **Icons:** Use sharp or minimally rounded 16px icons with a 1.5pt stroke weight.

## Components

### Buttons
- **Primary:** Solid teal background with black text. No gradients.
- **Secondary:** Subtle border (#24282D) with high-contrast text. Background fills slightly on hover.
- **Ghost:** No border or background. Teal text only on hover or active state.

### Input Fields (Command-Line Style)
- Inputs should be flush with the bottom of the workspace or panel.
- Use a prompt prefix (e.g., `>`) in JetBrains Mono.
- No heavy focus rings; use a 1px teal border on focus.

### Terminal & Execution Blocks
- Use the secondary background (#111417).
- Content must be monospaced.
- Use distinct colors for log levels: `dim` for verbose, `teal` for info, `amber` for warnings, and `red` for errors.

### Sidebar & Lists
- Compact list items (28px - 32px height).
- Icons should be 16px and muted (#8B929A), turning white on hover.
- Active items are indicated by a 2px vertical teal line on the left edge.

### Status Indicators
- Small, uppercase, monospaced text.
- Use dot indicators for status (Teal for "Active/Running", Dim for "Idle").