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

### 3. Menjalankan di Android
- Buka **Android Emulator** atau sambungkan perangkat Android via USB (USB Debugging aktif).
- Jalankan:
  ```bash
  npm run android
  ```
- Atau scan QR Code menggunakan aplikasi **Expo Go** di perangkat Android.
- Masuk ke tab **Settings** di aplikasi dan pastikan URL server diatur ke `http://10.0.2.2:8080` (untuk Android Emulator) atau `http://<IP_LAN_KOMPUTER>:8080` (untuk HP fisik).
