# DELTA Mobile App

Cross-platform AI assistant mobile client built with **React Native**, **Expo SDK 51**, **Expo Router**, and **TypeScript** for Delta AI Agent.

---

## Fitur Utama

- 💬 **Live Chat with Delta**: Kirim instruksi/perintah keamanan atau percakapan langsung ke Delta AI engine.
- ⚡ **Realtime SSE Streaming**: Dukungan Server-Sent Events (`/api/events`) dengan auto-reconnect & ping tracking.
- 🧠 **Live Thinking & Agent Activity**: Visualisasi status berpikir agent (`AgentStep` tree) dengan rincian durasi, tool, dan command yang dieksekusi.
- 📜 **Conversation History**: Sinkronisasi riwayat obrolan dari server Delta.
- ⚙️ **Configurable Connection & Model**: Pengaturan dynamic host IP (Android Emulator `10.0.2.2`, Localhost, atau LAN IP) dan pemilihan model AI.
- 🎨 **Minimal & Dark-First UI**: Tema monokromatik modern beraksen emerald & cyan, tanpa elemen AI generik.

---

## Struktur Folder

```
delta/mobile/
├── app/
│   ├── _layout.tsx           # Root provider, Safe area, SSE bootstrap
│   ├── (tabs)/
│   │   ├── _layout.tsx       # Bottom tabs navigation
│   │   ├── index.tsx         # Chat Screen
│   │   ├── history.tsx       # Conversation History Screen
│   │   └── settings.tsx      # Connection & AI Model Settings
│   └── +not-found.tsx
├── src/
│   ├── components/
│   │   ├── chat/             # MessageList, MessageBubble, ChatInput, CodeBlock
│   │   ├── agent/            # AgentActivity, StatusPill
│   │   └── common/           # Header
│   ├── services/
│   │   ├── api/              # apiClient, chatApi, systemApi, sessionApi
│   │   └── realtime/         # sseClient
│   ├── store/                # useChatStore, useConnectionStore, useSettingsStore
│   ├── theme/                # colors
│   ├── types/                # events, chat, system
│   └── utils/                # formatters
├── tests/                    # Unit tests
├── package.json
├── tsconfig.json
└── app.json
```

---

## Cara Menjalankan Delta Mobile

### 1. Jalankan Backend Delta terlebih dahulu
Di root repository `Delta-CLI`:
```bash
python -m delta.web.server
```
*(Server akan berjalan di port `8080` / `8000`)*.

### 2. Jalankan Mobile App (Expo)
Pindah ke direktori `delta/mobile`:
```bash
cd delta/mobile
npm install
npm start
```

### 3. Menjalankan di Android (Expo Prebuild / Development Build)
Fitur **Camera Monitoring** menggunakan native WebRTC (`react-native-webrtc`) dan Foreground Service, sehingga membutuhkan **Expo Development Build**:

1. Lakukan prebuild native project:
   ```bash
   npx expo prebuild
   ```
2. Jalankan development client di Android Emulator atau HP fisik:
   ```bash
   npx expo run:android
   ```
3. Atau bangun APK development via EAS Build:
   ```bash
   eas build --profile development --platform android
   ```

Masuk ke tab **Settings** di aplikasi dan pastikan URL server diatur ke IP host Delta Web Anda.

---

## Fitur Camera Monitoring & Privasi

- **Explicit Consent**: Kamera hanya aktif setelah pengguna menyetujui popup izin khusus Delta dan dialog izin sistem Android.
- **Persistent Notification**: Status monitoring ditampilkan jelas melalui notifikasi foreground dan indikator status melayang.
- **WebRTC Remote Streaming**: Transmisi video langsung melalui WebRTC (STUN/TURN) ke Delta Web tanpa transmisi base64.
- **Instant Revocation**: Menekan tombol **Hentikan** / **Stop Monitoring** akan langsung mematikan track kamera dan membatalkan sesi.
