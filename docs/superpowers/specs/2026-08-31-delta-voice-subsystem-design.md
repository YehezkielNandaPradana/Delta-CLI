# Delta Voice Response Subsystem Design

**Date**: 2026-08-31
**Status**: Approved
**Author**: Delta CLI Team

---

## 1. Overview

The Delta Voice Response Subsystem introduces a production-quality, local-first voice output modality to Delta CLI and Web. It operates as an asynchronous consumer of Delta's canonical `EventBus`, keeping agent execution completely non-blocking, modular, and provider-agnostic.

### Key Goals
- **Output Modality Only**: Zero modifications to agent reasoning, planners, workers, or model providers.
- **Local-First & Private**: Defaults to PiperTTS local neural engine, falling back to SystemTTS (pyttsx3 / OS native), and degrading to text-only MockTTS.
- **Female Voice Profile**: Default voice profile prioritizes generic synthetic female voices with Indonesian (`id-ID`) and English (`en-US`) support.
- **Voice Policy**: Only speaks key milestones, final answers, warnings, and task completions. Excludes raw tool calls, code, logs, and secrets.
- **Robust Isolation**: TTS or audio playback failures will NEVER crash or fail an underlying agent task.

---

## 2. Architecture & Module Structure

All voice implementation resides under `delta/voice/`:

```
delta/voice/
├── __init__.py
├── model.py            # Data models, Enums, VoiceProfile, TTSRequest, TTSChunk
├── formatter.py        # VoiceFormatter (markdown stripping, symbol normalization, sentence segmentation)
├── redaction.py        # SecretRedactor integration for voice safety
├── queue.py            # PriorityVoiceQueue with task boundary tracking
├── manager.py          # VoiceManager (EventBus subscription, playback loop, interrupter)
├── audio.py            # AudioOutput abstraction (cross-platform playback without hardware block)
├── events.py           # Voice Event types for global EventBus emission
└── providers/
    ├── __init__.py
    ├── base.py         # TTSProvider ABC (synthesize, stream, health_check, list_voices)
    ├── piper.py        # PiperProvider (Local ONNX neural TTS runner & voice discovery)
    ├── system.py       # SystemTTSProvider (pyttsx3 / SAPI5 / NSSpeechSynthesizer fallback)
    ├── mock.py         # MockTTSProvider (headless / CI text-only provider)
    └── chain.py        # FallbackTTSProviderChain (auto-resolution & graceful degradation)
```

### Data Flow Diagram

```
Agent Execution Event (EventBus)
          ↓
     VoiceManager (Policy Check & Task Filter)
          ↓
     VoiceFormatter + SecretRedactor
          ↓
  Sentence Segmentation / Chunking
          ↓
    PriorityVoiceQueue (CRITICAL / HIGH / NORMAL / LOW)
          ↓
  FallbackTTSProviderChain (Piper -> SystemTTS -> Mock)
          ↓
  AudioOutput (Async Non-blocking Playback)
```

---

## 3. Provider Resolution & Voice Discovery

### Auto Provider Resolution
When `voice.provider` is set to `auto`:
1. **PiperTTS**: Check if `piper` binary and ONNX models exist. If healthy, use `PiperProvider`.
2. **SystemTTS**: If Piper is unavailable/unhealthy, initialize `pyttsx3` / OS native speech synthesizer.
3. **MockTTS**: If both fail or hardware audio is missing, fall back gracefully to silent `MockTTSProvider`.

### Generic Female Voice Discovery
- **Config**:
  ```json
  {
    "voice": {
      "enabled": true,
      "provider": "auto",
      "profile": "female",
      "language": "id-ID",
      "speed": 1.0,
      "pitch": 0.0,
      "volume": 1.0,
      "piper_models_dir": "~/.delta/voice/models"
    }
  }
  ```
- **Discovery Strategy**:
  1. Search local models in `piper_models_dir` for models matching `id_ID` + `female` metadata.
  2. Fall back to `en_US` female Piper models.
  3. Fall back to SystemTTS female voice (filtering voice descriptors for "female", "zira", "hazel", "indonesia").
  4. Fall back to default system voice or silent mock.
- No real person voice cloning or hardcoded file paths.

---

## 4. Voice Policy & Formatting

### Policy Filters
- **Allowed to Speak**:
  - `task_started` (Brief milestone)
  - `plan_created` (Summary milestone)
  - `finding_discovered` (Key warning/vulnerability)
  - `task_completed` (Final answer / completion summary)
  - `task_failed` (High priority error notice)
  - Explicit user requests (`delta voice test`)
- **Forbidden from Speech**:
  - Code blocks (` ```python ... ``` `)
  - Tool invocation logs / file operations
  - Shell command output
  - Debug stack traces & raw JSON
  - Secrets, API keys, passwords (passed through `SecretRedactor`)

### VoiceFormatter Normalization
- Markdown symbols (`#`, `*`, `` ` ``, `>`) stripped.
- Tech symbols normalized: `C#` → "C sharp", `npm` → "N P M", `HTTP` → "H T T P", `API` → "A P I", numbers to words when needed.
- Long text segmented into clean sentence chunks for streaming synthesis.

---

## 5. Queue, Priority & Interruption

### Priority Levels
- `CRITICAL`: System alerts & security block warnings.
- `HIGH`: Task completion / task failure messages.
- `NORMAL`: Important milestones (`plan_created`, `finding_discovered`).
- `LOW`: Optional progress updates (dropped automatically if newer speech arrives).

### Interruption & Task Boundaries
- User sending new command or cancelling task calls `voice_manager.stop()`.
- Flushes pending queue, halts `AudioOutput` immediately, resets state to `IDLE`.
- Discards stale queued speech from previous tasks.

---

## 6. CLI & Web Integration

### CLI Commands
- `delta voice on` / `delta voice off`
- `delta voice status`
- `delta voice list` (lists discovered voices across providers)
- `delta voice set <profile|voice_id>`
- `delta voice test`

### Web UI & EngineBridge
- `EngineBridge` forwards voice events (`voice.started`, `voice.completed`, `voice.speaking_state`) over WebSocket to Web UI.
- Exposes API endpoints:
  - `GET /api/voice/status`
  - `GET /api/voice/voices`
  - `POST /api/voice/config`
  - `POST /api/voice/stop`

---

## 7. Testing Strategy

1. `tests/test_voice_formatter.py`: Tests markdown stripping, sentence segmentation, tech symbol normalization.
2. `tests/test_voice_redaction.py`: Verifies secret keys / credentials are never present in formatted speech.
3. `tests/test_voice_queue.py`: Verifies priority ordering, queue backpressure dropping, task cancellation flushes.
4. `tests/test_voice_providers.py`: Tests `PiperProvider` discovery, `SystemTTSProvider` female filtering, and `FallbackTTSProviderChain`.
5. `tests/test_voice_manager.py`: Tests `EventBus` milestone integration, non-blocking execution, and task error isolation.
6. **CI Requirements**: Runs deterministically using `MockTTSProvider` without requiring physical audio hardware or binaries.
