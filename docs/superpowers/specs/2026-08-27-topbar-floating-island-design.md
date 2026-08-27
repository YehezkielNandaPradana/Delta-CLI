# Design Spec: TopBar Floating Island HUD Redesign

## 1. Executive Summary
Transformasi TopBar `delta/web/index.html` dan `delta/web/static/index.html` dari header datar konvensional menjadi **Floating Island HUD (Heads-Up Display)** bernuansa Cyberpunk & Modern Glassmorphism. Desain ini membagi top bar menjadi tiga kapsul mengambang (*floating islands*) independen di atas area kerja canvas.

---

## 2. Arsitektur & Struktur Komponen

TopBar disusun dalam container mengambang dengan 3 island independen (`pointer-events-auto`):

```text
+---------------------------------------------------------------------------------------------------+
|  [ ISLAND 1: Brand & Context ]      [ ISLAND 2: Omnibar ⌘K ]      [ ISLAND 3: Telemetry & Pod ]   |
|  (Δ DELTA • SOC | dir: localhost)   (🔍 Search command... ⌘K)     (● ONLINE 24ms | ⎇ main | ⚙ 🌙)  |
+---------------------------------------------------------------------------------------------------+
```

### 2.1 Container Wrapper
- Container non-blocking: `fixed top-0 left-0 right-0 w-full px-4 pt-3 pb-1.5 flex justify-between items-center z-50 pointer-events-none`.
- Mengizinkan klik tembus ke elemen canvas di sela-sela antar island.
- Kompensasi padding canvas utama: penyesuaian layout container bawah (`pt-16` atau layout flex terintegrasi).

### 2.2 Island 1: Brand & Project Context (Left)
- **Container**: `bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-800/80 rounded-2xl shadow-lg px-3.5 py-1.5 flex items-center gap-3 pointer-events-auto hover:border-indigo-500/40 transition-base`.
- **Logo Emblem**: Squircle gradient indigo-ke-violet dengan karakter **`Δ`** putih, efek shadow berpendar dan hover scale.
- **Brand Typography**: `DELTA CORE` (bold, tracking-wide) + mini badge `HUD` / `SOC`.
- **Workspace Badge**: Pill direktori kerja aktif (`localhost` / working directory dinamis) dengan ikon `folder_open` / `dns`.

### 2.3 Island 2: Interactive Floating Omnibar (Center)
- **Container**: `bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-800/80 hover:border-indigo-500/50 hover:shadow-indigo-500/10 rounded-2xl shadow-lg px-4 py-1.5 flex items-center gap-2.5 w-72 md:w-96 cursor-pointer pointer-events-auto transition-base group`.
- **Search Icon**: Material icon `search` dengan hover glow warna indigo.
- **Placeholder Text**: `Search actions, tools, files...` (font inter/mono, muted zinc).
- **Shortcut Chip**: `<kbd>` element dengan border dan subtle glass background: `⌘K` / `Ctrl+K`.
- **Action**: Membuka `toggleModal('command-palette')`.

### 2.4 Island 3: Telemetry & Controls Pod (Right)
- **Container**: `bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-800/80 rounded-2xl shadow-lg px-3 py-1.5 flex items-center gap-2.5 pointer-events-auto hover:border-indigo-500/40 transition-base`.
- **Connection & Latency Telemetry**:
  - Indicator dot bernapas: `w-2 h-2 rounded-full bg-emerald-500 animate-pulse`.
  - Status label: `ONLINE` (tracking-wider, font-mono text-[10px]).
  - Mini latency tag: pill indikator ping real-time (contoh `24ms`).
- **Branch Selector**: Chip tombol `branch-modal` dengan icon `account_tree` dan label branch `main`.
- **Quick Action Buttons**:
  - Notifications button (dengan unread red/indigo indicator dot).
  - Settings button (`settings-modal`).
  - Theme Toggle switch (`cycleTheme()`) dengan icon auto-sync `dark_mode` / `light_mode`.

---

## 3. Visual & Motion Styling

### 3.1 Glassmorphism & Cyber Aesthetics
- Efek latar belakang: `backdrop-filter: blur(20px) saturate(180%)`.
- Layer Shadow: `shadow-[0_8px_30px_rgb(0,0,0,0.06)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.4)]`.
- Border gradient glow pada hover: transisi halus border color ke `indigo-500/40` dan subtle ambient ring.

### 3.2 Responsive & Accessibility Rules
- **Mobile breakpoint (< 768px)**:
  - Island tengah (Omnibar) mengecil menjadi icon button atau menyatu dengan pod kanan.
  - Teks brand dipadatkan menjadi logo icon + telemetry.
- **Prefers Reduced Motion**:
  - Semua keyframe animasi pulse dan transform hover dinonaktifkan jika pengguna mengaktifkan mode reduced motion.

---

## 4. Rencana File yang Diubah
1. `delta/web/index.html`: Update markup `<header>` dan styling TopBar Island, sinkronisasi script handler (`updateHeaderStatus`, `checkBackendHealth`, `cycleTheme`).
2. `delta/web/static/index.html`: Sinkronisasi versi static agar identik dengan template utama.
