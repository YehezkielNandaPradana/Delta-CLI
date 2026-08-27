# Right Sidebar Loop Animations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dynamic CSS loop animations (cyber orbit header glow, equalizer bars, shimmer gauges, ambient glow) to the right sidebar (Inspector Panel) in `delta/web/index.html`.

**Architecture:** Add keyframes and utility classes in the `<style>` block of `delta/web/index.html` and update HTML structure of the Right Inspector Panel to render animated elements.

**Tech Stack:** HTML5, CSS3 Animations / Keyframes, Tailwind CSS, Google Material Symbols.

## Global Constraints

- Pure CSS animations for zero JS runtime overhead on animation loops.
- GPU accelerated properties (`transform`, `opacity`, `background-position`).
- Full respect for `@media (prefers-reduced-motion: reduce)`.

---

### Task 1: Add CSS Keyframes & Animation Utility Classes

**Files:**
- Modify: `delta/web/index.html:120-137`

- [ ] **Step 1: Add keyframes and utility classes to `<style>` in `delta/web/index.html`**

Add the keyframes for `cyberOrbit`, `barBounce`, `shimmerWave`, and `cyberAmbientPulse`, plus reduced-motion handling.

```css
        @keyframes cyberOrbit {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .animate-cyber-orbit {
            animation: cyberOrbit 8s linear infinite;
        }

        @keyframes barBounce {
            0%, 100% { height: 25%; }
            50% { height: 95%; }
        }
        .animate-bar-bounce-1 { animation: barBounce 1.2s ease-in-out infinite; }
        .animate-bar-bounce-2 { animation: barBounce 1.4s ease-in-out infinite 0.2s; }
        .animate-bar-bounce-3 { animation: barBounce 1.1s ease-in-out infinite 0.4s; }
        .animate-bar-bounce-4 { animation: barBounce 1.5s ease-in-out infinite 0.1s; }

        @keyframes shimmerWave {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        .animate-shimmer {
            background: linear-gradient(90deg, rgba(99,102,241,0.1) 0%, rgba(99,102,241,0.4) 50%, rgba(99,102,241,0.1) 100%);
            background-size: 200% 100%;
            animation: shimmerWave 2.5s linear infinite;
        }

        @keyframes cyberAmbientPulse {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.05); }
        }
        .animate-cyber-ambient {
            animation: cyberAmbientPulse 4s ease-in-out infinite;
        }
```

- [ ] **Step 2: Commit CSS updates**

```bash
git add delta/web/index.html
git commit -m "style(web): add keyframes and animation utility classes for sidebar"
```

---

### Task 2: Inject Animated Elements into Right Inspector Panel HTML

**Files:**
- Modify: `delta/web/index.html:375-410`

- [ ] **Step 1: Update Inspector Panel Header with Cyber Orbit & Equalizer**

Update the header in `<aside>` (Right Inspector Panel) to include:
1. Cyber Orbit SVG ring around `analytics` icon.
2. Equalizer mini bars next to Token Latency metric card.
3. Ambient background glow element.

```html
        <!-- Right Inspector Panel -->
        <aside class="bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 w-80 shrink-0 flex flex-col h-full z-40 hidden lg:flex relative overflow-hidden">
            <!-- Cyber Ambient Background Glow -->
            <div class="absolute -top-20 -right-20 w-48 h-48 bg-indigo-500/10 dark:bg-indigo-500/15 rounded-full blur-2xl pointer-events-none animate-cyber-ambient"></div>

            <div class="h-11 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-4 bg-white dark:bg-zinc-900 shrink-0 relative z-10">
                <h2 class="text-sm font-semibold text-zinc-800 dark:text-zinc-100 flex items-center gap-2">
                    <div class="relative flex items-center justify-center w-6 h-6">
                        <div class="absolute inset-0 border border-indigo-500/40 rounded-full animate-cyber-orbit border-t-transparent"></div>
                        <span class="material-symbols-outlined text-[18px] text-indigo-500">analytics</span>
                    </div>
                    Analytics & Metrics
                </h2>
                ...
```

And update the Token Latency card header to include mini equalizer bars:

```html
                    <div class="flex justify-between items-center">
                        <span class="text-[11px] font-semibold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
                            <span class="material-symbols-outlined text-[15px] text-indigo-500">show_chart</span> Token Latency (ms)
                        </span>
                        <div class="flex items-end gap-0.5 h-3 px-1">
                            <span class="w-0.5 bg-indigo-500 rounded-full animate-bar-bounce-1"></span>
                            <span class="w-0.5 bg-indigo-500 rounded-full animate-bar-bounce-2"></span>
                            <span class="w-0.5 bg-indigo-500 rounded-full animate-bar-bounce-3"></span>
                            <span class="w-0.5 bg-indigo-500 rounded-full animate-bar-bounce-4"></span>
                        </div>
                        <span class="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold" id="current-latency-display">~24ms</span>
                    </div>
```

- [ ] **Step 2: Commit HTML updates**

```bash
git add delta/web/index.html
git commit -m "feat(web): add cyber orbit ring, mini equalizer bars, and ambient glow to right sidebar"
```
