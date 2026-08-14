---
name: Cognitive Minimalist
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#ffafd3'
  on-tertiary: '#620040'
  tertiary-container: '#e364a7'
  on-tertiary-container: '#560038'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#ffd8e7'
  tertiary-fixed-dim: '#ffafd3'
  on-tertiary-fixed: '#3d0026'
  on-tertiary-fixed-variant: '#85145a'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  code-snippet:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '450'
    lineHeight: 22px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 800px
  edge-margin-desktop: 40px
  edge-margin-mobile: 16px
  bubble-padding: 16px 20px
  stack-gap: 24px
  section-gap: 48px
---

## Brand & Style
The design system is built on a foundation of **Modern Minimalism** infused with **Glassmorphism** to reflect the ethereal yet precise nature of artificial intelligence. It targets high-productivity users who require a focused, distraction-free environment that feels both high-tech and human-centric.

The visual narrative centers on "The Intelligent Void"—using deep, expansive backgrounds contrasted with vibrant, glowing elements that represent AI activity. The emotional goal is to evoke feelings of clarity, calm, and limitless potential. Interfaces should feel lightweight, using subtle transparency and motion to communicate state changes rather than heavy borders or solid fills.

## Colors
The palette utilizes a "Deep Space" foundation to minimize eye strain and maximize the impact of accent colors. 

- **Primary (Electric Indigo):** Used for primary actions and the user's presence. It represents intent and direction.
- **Secondary (Cyber Cyan):** Reserved for AI response states, highlights, and "thinking" indicators.
- **Tertiary (Soft Rose):** An accent for delicate interactions, error states, or special features.
- **Neutrals:** A range of Slate and Zinc grays from `#020617` (background) to `#94A3B8` (secondary text) are used to build depth.

Backgrounds should use a subtle radial gradient of the primary color at 5% opacity to prevent the UI from feeling "dead" black.

## Typography
The typography strategy prioritizes technical precision and effortless readability. 

**Geist** is used for headlines to provide a sharp, geometric feel that aligns with modern developer tools. **Inter** handles the bulk of conversational text, chosen for its exceptional legibility at various weights in digital interfaces. **JetBrains Mono** is utilized for labels, metadata, and code blocks to reinforce the high-tech, systematic nature of the product.

For mobile devices, `display-lg` should scale down to 32px to maintain visual balance within the narrower viewport.

## Layout & Spacing
The layout follows a **Centered Fluid** model. Chat threads are constrained to a maximum width of 800px to ensure optimal line lengths for reading. 

Horizontal white space is used aggressively to separate the user's intent from the AI's response. A consistent 8px grid governs all spacing increments. 

- **Desktop:** A three-pane layout (History Sidebar / Active Chat / Contextual Panel) where the Sidebar and Panel can be collapsed to focus entirely on the conversation.
- **Mobile:** A single-column view with a floating input bar. Sidebars transition to full-screen overlays or bottom sheets.

## Elevation & Depth
Depth is conveyed through **Tonal Layers** and **Backdrop Blurs**. Shadows are avoided in favor of subtle inner borders that simulate light catching the edge of a glass pane.

1.  **Level 0 (Base):** The main background (`#020617`).
2.  **Level 1 (Surface):** Chat bubbles and sidebars use a semi-transparent fill (`rgba(30, 41, 59, 0.5)`) with a `20px` backdrop blur.
3.  **Level 2 (Active):** Hovered states or active inputs increase the opacity of the surface fill and add a `1px` stroke of the primary color at 20% opacity.
4.  **Floating Elements:** Modals and tooltips use a more opaque background with a very subtle, large-radius ambient glow in the primary color (shadow-spread: 20px, blur: 40px, opacity: 0.1).

## Shapes
The shape language is "Soft-Modern." While the system is precise, the `0.5rem` (8px) base radius ensures the interface feels approachable and "cushioned."

- **Chat Bubbles:** Use `rounded-lg` (16px). User bubbles are traditionally aligned with sharp bottom-right corners, while AI bubbles have a sharp bottom-left corner.
- **Input Fields:** Use `rounded-xl` (24px) to create a soft, pill-like container for text entry.
- **Buttons:** Use `rounded-md` (8px) for a slightly more structured, "tool-like" appearance.

## Components
### Chat Bubbles
User bubbles should be secondary-neutral backgrounds with white text. AI bubbles use the glassmorphic style (low-opacity fill + blur) with a subtle vertical accent border on the left side in the `secondary_color`.

### Buttons
Primary buttons are solid `primary_color` with white text. Secondary buttons are ghost-style (no fill) with a white `1px` border at 10% opacity.

### Input Bar
A persistent floating bar at the bottom of the screen. It should use a `Level 2` elevation. The send button remains disabled and low-contrast until text is detected, then glows with the `primary_color`.

### Chips / Suggestions
Small, pill-shaped triggers used for "quick replies." These should have a `1px` border of `primary_color_hex` at 30% opacity and no fill, turning solid on hover.

### Code Blocks
Deep black backgrounds (`#000000`) with syntax highlighting using the full accent palette (Cyan, Indigo, Rose). Include a "Copy" button in the top-right corner that appears only on hover.

### Typing Indicator
Three oscillating dots using the `secondary_color_hex`, rendered with a soft outer glow to simulate the AI "breathing" or thinking.