# VTuber Architecture (Phase 1 to Phase 9 Complete)

## 1. Overview & Tujuan

Modul `delta.vtuber` menyediakan fondasi komprehensif AI VTuber & Personal Companion untuk Delta:
- **Phase 1**: Event-driven state machine & lifecycle transitions.
- **Phase 2A–2D**: Adapter core, speech pipeline, Edge-TTS synthesis, browser audio player, emotion engine deterministik, dan mood modulation.
- **Phase 3A–3C**: Avatar controller abstraction, Live2D WebGL parameter mapper, VTube Studio desktop bridge, dan realtime audio lip-sync DSP.
- **Phase 4**: Voice input microphone capture on-demand, Web Audio VAD, automatic barge-in interrupts, dan full conversational loop.
- **Phase 5**: Persona profiling, dynamic mood decay, SQLite long-term memory dengan credential secret filtering, dan natural speech formatting.
- **Phase 6**: Personal VTuber experience workspace (`#/vtuber`), unified `PersonalVTuberRuntime`, `IdleBehaviorManager`, `AnimationPrioritySystem`, serta mode layout (Split View, Compact, Avatar Only).
- **Phase 7**: Personal Presence System, greeting & farewell lifecycle, non-blocking contextual micro-reactions, memory expiration & privacy controls, platform-independent desktop integration adapters, dan settings hub (`#/vtuber/settings`).
- **Phase 8**: Personal Desktop Intelligence, on-demand active window detection, workspace context resolution, ephemeral screenshot capture (zero persistence), sanitized clipboard reader, global quick summon hotkey, desktop overlay route (`#/vtuber/overlay`), dan agent context tools (`get_desktop_context`, `read_clipboard_context`, `capture_screen_context`).
- **Phase 9**: Advanced VTuber Expressiveness & Physics, local expression dynamics (`ExpressionIntensityModulator`), spring-damper secondary physics simulator (`PhysicsController` & `PhysicsSpring`), speech prosody modulation (`ProsodyModulator` via Edge-TTS SSML tags), smooth eye gaze tracking, dan organic blinking.

## 2. Struktur Modul

```text
delta/vtuber/
├── __init__.py          # Export publik package
├── runtime.py           # PersonalVTuberRuntime master coordinator
├── events.py            # Event types, payload models, dan emotion enums
├── event_bus.py         # Async EventBus dengan isolasi error subscriber
├── state_machine.py     # State Machine lifecycle & validasi transisi
├── adapter.py           # Delta Agent -> VTuber Event integration bridge
├── desktop_legacy.py    # Backward-compatible desktop integration adapters
├── desktop/             # Desktop Intelligence & Privacy System
│   ├── __init__.py      # Desktop package exports
│   ├── schemas.py       # DesktopContext, ActiveWindow, ProjectContext, ScreenshotData, ClipboardData
│   ├── permissions.py   # DesktopPermissionManager (Opt-in granular privacy gates)
│   ├── active_window.py # ActiveWindowProvider (Windows ctypes, Linux, Noop fallback)
│   ├── context.py       # ProjectContextProvider (Single source of truth workspace metadata)
│   ├── screenshot.py    # ScreenshotProvider (Ephemeral memory buffer, zero persistence)
│   ├── clipboard.py     # ClipboardProvider (Sanitized text with SecretFilter)
│   ├── hotkey.py        # GlobalHotkeyProvider (System hotkey Quick Summon)
│   ├── overlay.py       # DesktopOverlayController (Transparent minimal companion overlay)
│   └── manager.py       # DesktopManager (Central coordinator for desktop capabilities)
├── presence/            # Personal Presence & Awareness Subpackage
│   ├── __init__.py      # Presence exports
│   ├── schemas.py       # PresenceState, PresenceActivity, NotificationEvent
│   ├── scheduler.py     # PresenceScheduler (idle duration & attention decay)
│   ├── reactions.py     # MicroReactionEngine (O(1) contextual reactions)
│   ├── notifications.py # NotificationManager (internal companion notifications)
│   └── manager.py       # PresenceManager (greeting, farewell, lifecycle)
├── behavior/            # Idle Behavior & Procedural Motion
│   ├── __init__.py      # Behavior package exports
│   └── idle.py          # IdleBehaviorManager (Breathing, Sway, Blinking)
├── personality/         # Persona & Mood Subpackage
│   ├── __init__.py      # Personality exports
│   ├── schemas.py       # PersonaProfile, MoodState models
│   ├── behavior.py      # PersonalityBehavior (speech text vs display text)
│   └── manager.py       # PersonalityManager (mood updates, emotion bias)
├── memory/              # Conversation Memory Subpackage
│   ├── __init__.py      # Memory exports
│   ├── schemas.py       # MemoryEntry, MemoryType, ShortTermMemoryBuffer
│   ├── security.py      # SecretFilter (API key / credential redaction & rejection)
│   ├── store.py         # SQLiteMemoryStore (persistent durable facts & expiration)
│   └── manager.py       # MemoryManager (short-term, long-term, remember/forget)
├── emotion/             # Emotion & Expression Engine
│   ├── __init__.py      # Emotion package exports
│   ├── schemas.py       # VTuberEmotion, VTuberExpression, EmotionResult, EmotionChangedEvent
│   ├── rules.py         # Deterministic O(1) context-aware rule resolver & mapping
│   └── engine.py        # EmotionEngine lifecycle & duplicate transition suppression
├── voice/               # Voice, TTS, STT & Prosody Pipeline
│   ├── __init__.py      # Voice package exports
│   ├── schemas.py       # SpeechChunk, AudioData, SpeechLifecycleEvent models
│   ├── sentence_chunker.py # Natural boundary sentence splitter & token accumulator
│   ├── tts.py           # TTSProvider protocol & MockTTSProvider implementation
│   ├── edge_tts_provider.py # Concrete Microsoft Edge-TTS provider (Prosody modulated)
│   ├── audio.py         # AudioPlayer protocol & MockAudioPlayer implementation
│   ├── browser_player.py # Browser Audio Player & WebSocket/SSE Relay
│   ├── speech_manager.py # Speech queue, playback orchestrator, & barge-in interrupt
│   ├── prosody/         # Phase 9 Speech Prosody & SSML Modulation Subpackage
│   │   ├── __init__.py  # Prosody exports
│   │   ├── schemas.py   # ProsodyProfile, EMOTION_PROSODY_DEFAULTS
│   │   └── controller.py # ProsodyModulator, ProsodyController
│   └── stt/             # Speech-to-Text & Voice Input Subpackage
│       ├── __init__.py  # STT package exports
│       ├── schemas.py   # STTResult, STTPartialResult, STTFinalResult, VADState
│       ├── provider.py  # STTProvider protocol
│       ├── mock.py      # MockSTTProvider implementation
│       ├── vad.py       # VoiceActivityDetector (RMS energy & hangover debounce)
│       └── manager.py   # STTManager (VAD trigger, barge-in, conversational loop)
└── avatar/              # Avatar Controller, Live2D, Physics & VTS Subpackage
    ├── __init__.py      # Avatar package exports
    ├── schemas.py       # AvatarState (renderer-agnostic model)
    ├── priority.py      # AnimationPrioritySystem (IDLE < EMOTION < SPEAKING < ERROR)
    ├── physics.py       # Phase 9 Spring-Damper Physics Simulator (Hair, Clothing, Accessories)
    ├── expression/      # Phase 9 Expression Dynamics & Intensity Modulation
    │   ├── __init__.py  # Expression dynamics exports
    │   └── dynamics.py  # ExpressionIntensityModulator, ExpressionTransitionController
    ├── expressions.py   # ExpressionController (Emotion -> Expression state)
    ├── lip_sync.py      # LipSyncController protocol & DefaultLipSyncController
    ├── lip_sync_analyzer.py # AudioAmplitudeAnalyzer (RMS, Noise Gate, Attack/Release DSP)
    ├── renderer.py      # AvatarRenderer protocol & MockAvatarRenderer
    ├── live2d_mapper.py # Live2DExpressionMapper & Live2DParameterMapper (Cubism 4 Physics)
    ├── live2d_renderer.py # Live2DCanvasRenderer (Realtime transport dispatcher)
    ├── vts_renderer.py  # VTSRenderer (Desktop VTube Studio integration)
    ├── controller.py    # AvatarController (state coordinator & render dispatcher)
    └── vts/             # VTube Studio WebSocket protocol & client bridge
        ├── __init__.py  # VTS exports
        ├── protocol.py  # VTS WebSocket message schemas
        ├── mapper.py    # VTS parameter injection payload mapper
        └── client.py    # Robust asynchronous VTS WebSocket client
```

---

## 3. Phase 9 — Advanced Expressiveness, Physics & Prosody Architecture

### Arsitektur Aliran Fisika & Prosody Suara
```text
Agent / Emotion Event
         │
    ┌────┴──────────────────────────┐
    ▼                               ▼
ProsodyModulator            ExpressionDynamics
(Rate, Pitch SSML tags)     (Mood & Presence Modulation)
    │                               │
    ▼                               ▼
Edge-TTS Synthesis           AvatarController
    │                               │
    ▼                               ▼
Audio Chunk (MP3)           Live2DParameterMapper
    │                               │
    │                    PhysicsController (Spring-Damper)
    │                    ├── ParamHairFront, ParamHairSide, ParamHairBack
    │                    ├── ParamEyeBallX, ParamEyeBallY (Gaze tracking)
    │                    └── ParamBreath (Natural breathing float)
    │                               │
    └───────────────┬───────────────┘
                    ▼
           DeltaAvatarView (WebGL Canvas)
           [60 FPS Client LERP + Inertia Hair Sway + Lip-Sync]
```

### Parameter Fisika Cubism 4 & Prosody Suara
1. **Spring-Damper Secondary Hair Physics (`PhysicsSpring`)**:
   - Persamaan gerak teredam kritis: $F = -k(x - x_{\text{target}}) - d \cdot v$
   - Menghasilkan efek inersia rambut depan, samping, belakang, dan aksesoris yang berayun mengikuti percepatan kepala avatar secara realistis.
2. **Gaze & Eye Contact Tracking**:
   - Mata avatar secara halus mengikuti pergerakan kursor mouse pengguna pada kanvas (`ParamEyeBallX`, `ParamEyeBallY`), kembali ke posisi netral atau melirik saat berpikir.
3. **Audio Prosody Modulation (`ProsodyModulator`)**:
   - `HAPPY` $\rightarrow$ Rate $+5\%$, Pitch $+4\text{Hz}$
   - `EXCITED` $\rightarrow$ Rate $+12\%$, Pitch $+8\text{Hz}$
   - `THINKING` $\rightarrow$ Rate $-6\%$, Pitch $-2\text{Hz}$
   - `SAD` $\rightarrow$ Rate $-12\%$, Pitch $-6\text{Hz}$
