# Design Spec: Sidebar Kanan (Inspector Panel) Loop Animations

## Executive Summary
Menambahkan animasi loop CSS visual (Dynamic Mini Meters/Bars & Cyber Futuristic Orbit/Glow) pada sidebar kanan (`Right Inspector Panel`) di `delta/web/index.html` untuk meningkatkan estetika real-time monitoring tanpa mengganggu performa atau keterbacaan data.

---

## 1. Scope & Components

### 1.1 Cyber Orbit Header
- Ring berputar (`animate-spin-slow` / CSS keyframe `orbitRotate`) mengelilingi ikon *Analytics & Metrics*.
- Ambient gradient backdrop glow pada header panel inspector.

### 1.2 Dynamic Equalizer & Live Meters
- **Equalizer Mini Bars**: Bar chart 4-5 kolom mini dengan animasi `barBounce` naik-turun berkala menggunakan staggered `animation-delay`.
- **Shimmer Resource Progress**: Bar indikator penggunaan memori/token dengan efek aliran kilau (*shimmer/wave*) menggunakan gradient shift.

### 1.3 Ambient Background Glow
- Subtle pulse light pada latar belakang Inspector Panel (`cyberAmbientPulse`).

---

## 2. Technical Implementation

### CSS Keyframes (`delta/web/index.html` `<style>`)
- `@keyframes barBounce`: Variasi tinggi bar `20%` ke `90%`.
- `@keyframes orbitRotate`: Rotasi 360-derajat halus pada ring orbit SVG/span.
- `@keyframes shimmerWave`: Pergeseran `background-position` linier untuk efek energi mengalir.
- `@keyframes cyberAmbientPulse`: Variasi opacity 0.3 ke 0.7 pada radial gradient layer.

### HTML Elements Update
- Menambahkan elemen SVG/CSS ring pada header inspector panel.
- Menambahkan container equalizer mini bar pada kartu *Token Latency*.
- Menambahkan shimmer overlay pada progress bar metrics.

---

## 3. Performance & Accessibility
- **CSS GPU Acceleration**: Menggunakan `transform` dan `opacity` saja.
- **Prefers Reduced Motion**: Semua animasi dinonaktifkan jika media query `@media (prefers-reduced-motion: reduce)` aktif.
