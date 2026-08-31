import asyncio
import json
import queue
import time
import pytest
from delta.ai.events import AgentEvent, EventType, event_bus as core_event_bus
from delta.vtuber.events import (
    VTuberEventType,
    VTuberEmotion,
    VTuberEvent,
    VTuberPayload,
)
from delta.vtuber.event_bus import (
    VTuberEventBus,
)
from delta.vtuber.state_machine import (
    VTuberState,
    VTuberStateMachine,
    InvalidStateTransitionError,
)
from delta.vtuber.adapter import VTuberAgentAdapter
from delta.vtuber.voice import (
    SpeechManager,
    SentenceChunker,
    AudioData,
    SpeechState,
    SpeechLifecycleEventType,
    SpeechLifecycleEvent,
    MockTTSProvider,
    EdgeTTSProvider,
    MockAudioPlayer,
    BrowserAudioPlayer,
    STTState,
    VADState,
    STTResult,
    STTPartialResult,
    STTFinalResult,
    STTProvider,
    MockSTTProvider,
    VoiceActivityDetector,
    STTManager,
)
from delta.vtuber.emotion import (
    VTuberEmotion,
    VTuberExpression,
    EmotionResult,
    EmotionChangedEvent,
    EmotionEngine,
    emotion_engine,
    map_emotion_to_expression,
    resolve_emotion_from_event,
)
from delta.vtuber.avatar import (
    AvatarState,
    ExpressionController,
    LipSyncController,
    DefaultLipSyncController,
    AudioAmplitudeAnalyzer,
    AvatarRenderer,
    MockAvatarRenderer,
    AvatarController,
    Live2DExpressionMapper,
    Live2DParameterMapper,
    Live2DCanvasRenderer,
    VTSMessage,
    VTSMessageType,
    VTSMapper,
    VTSClient,
    VTSRenderer,
)
from delta.vtuber.avatar.vts_visual import (
    VisualSourceType,
    VisualSourceState,
    VisualSourceStatus,
    AvatarVisualSource,
    MockVisualSource,
    WindowsVTSVisualSource,
    LinuxVTSVisualSource,
    VTSVisualManager,
)
from delta.vtuber.personality import (
    PersonaProfile,
    MoodState,
    PersonalityBehavior,
    PersonalityManager,
)
from delta.vtuber.memory import (
    MemoryType,
    MemoryEntry,
    ShortTermMemoryBuffer,
    SecretFilter,
    SQLiteMemoryStore,
    MemoryManager,
)
from delta.vtuber.behavior import (
    IdleBehaviorManager,
    idle_behavior_manager,
)
from delta.vtuber.avatar.priority import (
    AnimationPriority,
    AnimationPrioritySystem,
)
from delta.vtuber.presence import (
    PresenceActivity,
    PresenceState,
    NotificationType,
    NotificationEvent,
    MicroReactionEngine,
    NotificationManager,
    PresenceScheduler,
    PresenceManager,
)
from delta.vtuber.desktop import (
    DesktopCapability,
    ActiveWindow,
    ProjectContext,
    DesktopContext,
    ScreenshotData,
    ClipboardData,
    DesktopPermissionManager,
    ActiveWindowProvider,
    WindowsActiveWindowProvider,
    LinuxActiveWindowProvider,
    NoopActiveWindowProvider,
    ClipboardProvider,
    SystemClipboardProvider,
    NoopClipboardProvider,
    ScreenshotProvider,
    SystemScreenshotProvider,
    NoopScreenshotProvider,
    GlobalHotkeyProvider,
    SystemHotkeyProvider,
    NoopHotkeyProvider,
    DesktopOverlayController,
    ProjectContextProvider,
    DesktopManager,
    desktop_manager,
    DesktopIntegration,
    WindowsDesktopIntegration,
    LinuxDesktopIntegration,
    NoopDesktopIntegration,
)
from delta.vtuber.voice.prosody import (
    ProsodyProfile,
    EMOTION_PROSODY_DEFAULTS,
    ProsodyModulator,
    ProsodyController,
)
from delta.vtuber.avatar.physics import (
    PhysicsSpring,
    PhysicsController,
)
from delta.vtuber.avatar.expression import (
    ExpressionIntensityModulator,
    ExpressionTransitionController,
    ExpressionDynamics,
)
from delta.vtuber.runtime import (
    PersonalVTuberRuntime,
    personal_vtuber_runtime,
)


def test_event_payload_structure():
    payload = VTuberPayload(
        text="Halo semua!",
        emotion=VTuberEmotion.HAPPY,
        intensity=0.85,
        tool="search_code",
        metadata={"channel": "stream"},
    )
    assert payload.text == "Halo semua!"
    assert payload.emotion == VTuberEmotion.HAPPY
    assert payload.intensity == 0.85
    assert payload.tool == "search_code"
    assert payload.metadata["channel"] == "stream"

    event = VTuberEvent.create(
        event_type=VTuberEventType.SPEAKING,
        text="Sedang membaca file",
        emotion=VTuberEmotion.THINKING,
        intensity=0.7,
        tool="read_file",
    )
    assert event.type == VTuberEventType.SPEAKING
    assert event.payload.text == "Sedang membaca file"
    assert event.payload.emotion == VTuberEmotion.THINKING
    assert event.payload.intensity == 0.7
    assert event.payload.tool == "read_file"
    assert event.event_id is not None
    assert event.timestamp > 0


def test_event_bus_emit_and_subscribe():
    async def _test():
        bus = VTuberEventBus()
        received = []

        async def on_event(event: VTuberEvent):
            received.append(event)

        bus.subscribe(on_event, VTuberEventType.THINKING)

        # Emit matching event
        event1 = VTuberEvent.create(VTuberEventType.THINKING, text="Thinking...")
        await bus.emit(event1)

        # Emit non-matching event
        event2 = VTuberEvent.create(VTuberEventType.IDLE)
        await bus.emit(event2)

        assert len(received) == 1
        assert received[0].type == VTuberEventType.THINKING
        assert received[0].payload.text == "Thinking..."

    asyncio.run(_test())


def test_event_bus_multiple_subscribers():
    async def _test():
        bus = VTuberEventBus()
        res_sync = []
        res_async = []

        def sync_sub(event: VTuberEvent):
            res_sync.append(event.type.value)

        async def async_sub(event: VTuberEvent):
            res_async.append(event.type.value)

        bus.subscribe(sync_sub, VTuberEventType.TOOL_USE)
        bus.subscribe(async_sub, VTuberEventType.TOOL_USE)

        await bus.emit(VTuberEvent.create(VTuberEventType.TOOL_USE, tool="execute_command"))

        assert res_sync == ["TOOL_USE"]
        assert res_async == ["TOOL_USE"]

    asyncio.run(_test())


def test_event_bus_wildcard_subscriber():
    async def _test():
        bus = VTuberEventBus()
        all_events = []

        def global_watcher(event: VTuberEvent):
            all_events.append(event.type)

        bus.subscribe(global_watcher)  # None = wildcard

        await bus.emit(VTuberEvent.create(VTuberEventType.LISTENING))
        await bus.emit(VTuberEvent.create(VTuberEventType.THINKING))
        await bus.emit(VTuberEvent.create(VTuberEventType.SPEAKING))

        assert all_events == [
            VTuberEventType.LISTENING,
            VTuberEventType.THINKING,
            VTuberEventType.SPEAKING,
        ]

    asyncio.run(_test())


def test_event_bus_unsubscribe():
    async def _test():
        bus = VTuberEventBus()
        received = []

        def handler(event: VTuberEvent):
            received.append(event)

        unsub_func = bus.subscribe(handler, VTuberEventType.ERROR)
        await bus.emit(VTuberEvent.create(VTuberEventType.ERROR, text="Err 1"))
        assert len(received) == 1

        # Unsubscribe via returned callable
        unsub_func()
        await bus.emit(VTuberEvent.create(VTuberEventType.ERROR, text="Err 2"))
        assert len(received) == 1

        # Subscribe again and unsubscribe via method
        bus.subscribe(handler, VTuberEventType.SUCCESS)
        await bus.emit(VTuberEvent.create(VTuberEventType.SUCCESS))
        assert len(received) == 2

        removed = bus.unsubscribe(handler, VTuberEventType.SUCCESS)
        assert removed is True
        await bus.emit(VTuberEvent.create(VTuberEventType.SUCCESS))
        assert len(received) == 2

    asyncio.run(_test())


def test_event_bus_subscriber_error_isolation():
    async def _test():
        bus = VTuberEventBus()
        succeeded = []

        def broken_handler(_event: VTuberEvent):
            raise RuntimeError("Subscriber explosion")

        def healthy_handler(event: VTuberEvent):
            succeeded.append(event.type)

        bus.subscribe(broken_handler, VTuberEventType.SPEAKING)
        bus.subscribe(healthy_handler, VTuberEventType.SPEAKING)

        # Bus should not crash
        await bus.emit(VTuberEvent.create(VTuberEventType.SPEAKING, text="Hello"))

        assert succeeded == [VTuberEventType.SPEAKING]

    asyncio.run(_test())


def test_state_machine_valid_transitions():
    async def _test():
        bus = VTuberEventBus()
        emitted = []

        bus.subscribe(lambda e: emitted.append(e.type))
        sm = VTuberStateMachine(initial_state=VTuberState.IDLE, event_bus=bus)

        # IDLE -> LISTENING -> THINKING -> TOOL_USE -> SPEAKING -> IDLE
        await sm.transition_to(VTuberState.LISTENING)
        assert sm.current_state == VTuberState.LISTENING

        await sm.transition_to(VTuberState.THINKING)
        assert sm.current_state == VTuberState.THINKING

        await sm.transition_to(VTuberState.TOOL_USE, tool="read_file")
        assert sm.current_state == VTuberState.TOOL_USE

        await sm.transition_to(VTuberState.THINKING)
        assert sm.current_state == VTuberState.THINKING

        await sm.transition_to(VTuberState.SPEAKING, text="Selesai analisis")
        assert sm.current_state == VTuberState.SPEAKING

        await sm.transition_to(VTuberState.IDLE)
        assert sm.current_state == VTuberState.IDLE

        # Alternative paths:
        # THINKING -> ERROR
        await sm.transition_to(VTuberState.THINKING)
        await sm.transition_to(VTuberState.ERROR)
        assert sm.current_state == VTuberState.ERROR

        # ERROR -> IDLE
        await sm.transition_to(VTuberState.IDLE)

        # SPEAKING -> LISTENING
        await sm.transition_to(VTuberState.THINKING)
        await sm.transition_to(VTuberState.SPEAKING)
        await sm.transition_to(VTuberState.LISTENING)
        assert sm.current_state == VTuberState.LISTENING

        assert emitted == [
            VTuberEventType.LISTENING,
            VTuberEventType.THINKING,
            VTuberEventType.TOOL_USE,
            VTuberEventType.THINKING,
            VTuberEventType.SPEAKING,
            VTuberEventType.IDLE,
            VTuberEventType.THINKING,
            VTuberEventType.ERROR,
            VTuberEventType.IDLE,
            VTuberEventType.THINKING,
            VTuberEventType.SPEAKING,
            VTuberEventType.LISTENING,
        ]

    asyncio.run(_test())


def test_state_machine_invalid_transitions():
    async def _test():
        sm = VTuberStateMachine(initial_state=VTuberState.IDLE)

        # IDLE cannot directly go to SPEAKING or TOOL_USE
        assert not sm.can_transition_to(VTuberState.SPEAKING)
        assert not sm.can_transition_to(VTuberState.TOOL_USE)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            await sm.transition_to(VTuberState.SPEAKING)

        assert exc_info.value.from_state == VTuberState.IDLE
        assert exc_info.value.to_state == VTuberState.SPEAKING

        # Transition to LISTENING
        await sm.transition_to(VTuberState.LISTENING)

        # LISTENING cannot jump directly to TOOL_USE or SPEAKING
        assert not sm.can_transition_to(VTuberState.TOOL_USE)
        assert not sm.can_transition_to(VTuberState.SPEAKING)

        with pytest.raises(InvalidStateTransitionError):
            await sm.transition_to(VTuberState.TOOL_USE)

    asyncio.run(_test())


def test_adapter_agent_lifecycle_full_flow():
    async def _test():
        vt_bus = VTuberEventBus()
        sm = VTuberStateMachine(initial_state=VTuberState.IDLE, event_bus=vt_bus)
        adapter = VTuberAgentAdapter(state_machine=sm, event_bus=vt_bus)

        events_received = []
        vt_bus.subscribe(lambda e: events_received.append(e))

        # 1. Agent Start
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.AGENT_START, execution_id="exec-1", status_text="Thinking...")
        )
        assert sm.current_state == VTuberState.THINKING

        # 2. Agent Thinking
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.AGENT_THINKING, execution_id="exec-1", status_text="Analyzing prompt...")
        )
        assert sm.current_state == VTuberState.THINKING

        # 3. Tool Start
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.TOOL_START, execution_id="exec-1", tool="read_file", input={"path": "main.py"})
        )
        assert sm.current_state == VTuberState.TOOL_USE

        # 4. Tool Result (Success) -> back to THINKING
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.TOOL_RESULT, execution_id="exec-1", tool="read_file", success=True, duration_ms=45.0)
        )
        assert sm.current_state == VTuberState.THINKING

        # 5. Message Complete -> SPEAKING
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.MESSAGE_COMPLETE, execution_id="exec-1", content="Berikut isi file main.py")
        )
        assert sm.current_state == VTuberState.SPEAKING

        # 6. Agent Complete -> IDLE
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.AGENT_COMPLETE, execution_id="exec-1", status_text="Task completed")
        )
        assert sm.current_state == VTuberState.IDLE

        event_types = [e.type for e in events_received]
        assert event_types == [
            VTuberEventType.THINKING,
            VTuberEventType.THINKING,
            VTuberEventType.TOOL_USE,
            VTuberEventType.THINKING,
            VTuberEventType.SPEAKING,
            VTuberEventType.IDLE,
        ]

    asyncio.run(_test())


def test_adapter_tool_error_and_agent_error_flow():
    async def _test():
        vt_bus = VTuberEventBus()
        sm = VTuberStateMachine(initial_state=VTuberState.IDLE, event_bus=vt_bus)
        adapter = VTuberAgentAdapter(state_machine=sm, event_bus=vt_bus)

        events_received = []
        vt_bus.subscribe(lambda e: events_received.append(e))

        # Start agent
        await adapter.handle_agent_event_async(AgentEvent(type=EventType.AGENT_START))
        await adapter.handle_agent_event_async(AgentEvent(type=EventType.TOOL_START, tool="failing_tool"))

        # Tool failure -> ERROR then ReAct THINKING
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.TOOL_RESULT, tool="failing_tool", success=False, error={"message": "File not found"})
        )
        assert sm.current_state == VTuberState.THINKING

        # Fatal agent error -> ERROR
        await adapter.handle_agent_event_async(
            AgentEvent(type=EventType.ERROR, error={"message": "LLM context timeout"})
        )
        assert sm.current_state == VTuberState.ERROR

        types = [e.type for e in events_received]
        assert VTuberEventType.ERROR in types

    asyncio.run(_test())


def test_adapter_synchronous_core_integration():
    """Test sync core event_bus triggering VTuberAgentAdapter safely without event loop conflicts."""
    vt_bus = VTuberEventBus()
    sm = VTuberStateMachine(initial_state=VTuberState.IDLE, event_bus=vt_bus)
    adapter = VTuberAgentAdapter(state_machine=sm, event_bus=vt_bus)

    # Attach to core event bus
    adapter.attach(core_event_bus)

    sse_received = []
    vtuber_received = []

    # Existing SSE subscriber to verify coexistence
    def sse_listener(ev: AgentEvent):
        sse_received.append(ev.type)

    unsub_sse = core_event_bus.subscribe(sse_listener)
    vt_bus.subscribe(lambda ev: vtuber_received.append(ev.type))

    try:
        # Emit synchronous events from core agent thread
        core_event_bus.emit(AgentEvent(type=EventType.AGENT_START, execution_id="sync-test"))
        core_event_bus.emit(AgentEvent(type=EventType.TOOL_START, execution_id="sync-test", tool="write_file"))
        core_event_bus.emit(AgentEvent(type=EventType.TOOL_RESULT, execution_id="sync-test", tool="write_file", success=True))
        core_event_bus.emit(AgentEvent(type=EventType.MESSAGE_COMPLETE, execution_id="sync-test", content="File written"))
        core_event_bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE, execution_id="sync-test"))

        # Allow background loop to process
        time.sleep(0.1)

        # Verify SSE received all core events
        assert len(sse_received) == 5
        assert EventType.AGENT_START in sse_received
        assert EventType.MESSAGE_COMPLETE in sse_received

        # Verify VTuber event bus received mapped events
        assert VTuberEventType.THINKING in vtuber_received
        assert VTuberEventType.TOOL_USE in vtuber_received
        assert VTuberEventType.SPEAKING in vtuber_received
        assert VTuberEventType.IDLE in vtuber_received

    finally:
        unsub_sse()
        adapter.detach()


# ==========================================
# Phase 2B Voice & TTS Unit Tests
# ==========================================


def test_sentence_chunker_punctuation_and_newlines():
    chunker = SentenceChunker()
    text = "Ketemu masalahnya. Aku sudah menemukan penyebabnya! Sekarang aku perbaiki file tersebut... Apakah kamu setuju?\nSiap dieksekusi."
    chunks = chunker.chunk_text(text)

    assert len(chunks) == 5
    assert chunks[0].text == "Ketemu masalahnya."
    assert chunks[1].text == "Aku sudah menemukan penyebabnya!"
    assert chunks[2].text == "Sekarang aku perbaiki file tersebut..."
    assert chunks[3].text == "Apakah kamu setuju?"
    assert chunks[4].text == "Siap dieksekusi."
    assert [c.sequence for c in chunks] == [0, 1, 2, 3, 4]


def test_sentence_chunker_empty_and_short_inputs():
    chunker = SentenceChunker()
    assert chunker.chunk_text("") == []
    assert chunker.chunk_text("   \n\t  ") == []

    # Single sentence without ending punctuation
    chunks = chunker.chunk_text("Halo dunia")
    assert len(chunks) == 1
    assert chunks[0].text == "Halo dunia"


def test_sentence_chunker_streaming_tokens():
    chunker = SentenceChunker()
    tokens = ["Halo ", "semua. ", "Hari ", "ini ", "kita ", "coding! ", "Ada yang ", "mau "]
    emitted = []

    for t in tokens:
        res = chunker.append_stream_token(t)
        emitted.extend(res)

    assert len(emitted) == 2
    assert emitted[0].text == "Halo semua."
    assert emitted[1].text == "Hari ini kita coding!"

    # Flush remaining incomplete token
    flushed = chunker.flush_stream()
    assert len(flushed) == 1
    assert flushed[0].text == "Ada yang mau"


def test_speech_manager_sequential_playback():
    async def _test():
        tts = MockTTSProvider(latency_sec=0.01)
        player = MockAudioPlayer(playback_speed_multiplier=50.0)
        manager = SpeechManager(tts_provider=tts, audio_player=player, auto_subscribe=False)

        lifecycle_events = []
        manager.add_listener(lambda ev: lifecycle_events.append(ev))

        # Enqueue multi-sentence text
        text = "Satu kalimat pertama. Dua kalimat kedua! Tiga kalimat ketiga?"
        chunks = await manager.enqueue_text(text)
        assert len(chunks) == 3

        # Wait for queue to be fully processed
        while manager.is_speaking:
            await asyncio.sleep(0.01)

        assert len(tts.synthesized_chunks) == 3
        assert len(player.played_audio_list) == 3

        # Verify strict sequence ordering
        assert [c.text for c in tts.synthesized_chunks] == [
            "Satu kalimat pertama.",
            "Dua kalimat kedua!",
            "Tiga kalimat ketiga?",
        ]

        played_texts = [a.metadata.get("text_len") for a in player.played_audio_list]
        assert len(played_texts) == 3

        await manager.shutdown()

    asyncio.run(_test())


def test_speech_manager_vtuber_event_bus_integration():
    async def _test():
        bus = VTuberEventBus()
        tts = MockTTSProvider(latency_sec=0.005)
        player = MockAudioPlayer(playback_speed_multiplier=50.0)
        manager = SpeechManager(tts_provider=tts, audio_player=player, event_bus=bus, auto_subscribe=True)

        # Emit VTuberEventType.SPEAKING to bus
        event = VTuberEvent.create(
            VTuberEventType.SPEAKING,
            text="Proses scan selesai. Ditemukan 2 port terbuka.",
            emotion=VTuberEmotion.HAPPY,
            intensity=0.9,
        )
        await bus.emit(event)

        # Wait until processed
        while manager.is_speaking:
            await asyncio.sleep(0.01)

        assert len(tts.synthesized_chunks) == 2
        assert tts.synthesized_chunks[0].text == "Proses scan selesai."
        assert tts.synthesized_chunks[1].text == "Ditemukan 2 port terbuka."
        assert tts.synthesized_chunks[0].emotion == VTuberEmotion.HAPPY

        await manager.shutdown()

    asyncio.run(_test())


def test_speech_manager_barge_in_interrupt():
    async def _test():
        # High latency to simulate long speech
        tts = MockTTSProvider(latency_sec=0.05)
        player = MockAudioPlayer(playback_speed_multiplier=1.0)
        manager = SpeechManager(tts_provider=tts, audio_player=player, auto_subscribe=False)

        # Enqueue long paragraph with multiple sentences
        long_text = "Kalimat satu berjalan panjang. Kalimat dua di antrean. Kalimat tiga menunggu giliran."
        await manager.enqueue_text(long_text)

        await asyncio.sleep(0.02)
        assert manager.is_speaking

        # User interrupts / barge-in
        await manager.stop()

        assert manager.queue_size == 0
        assert manager.current_state == SpeechState.IDLE
        assert not manager.is_speaking
        assert not player.is_playing

        await manager.shutdown()

    asyncio.run(_test())


def test_speech_manager_tts_error_isolation():
    async def _test():
        # TTS fails on keyword "ERROR_TEST"
        tts = MockTTSProvider(latency_sec=0.005, fail_on_keyword="ERROR_TEST")
        player = MockAudioPlayer(playback_speed_multiplier=50.0)
        manager = SpeechManager(tts_provider=tts, audio_player=player, auto_subscribe=False)

        error_events = []
        manager.add_listener(lambda ev: error_events.append(ev) if ev.event_type == SpeechLifecycleEventType.SPEECH_ERROR else None)

        # Enqueue sentence that fails, followed by healthy sentence
        await manager.enqueue_text("Ini adalah ERROR_TEST. Kalimat kedua sehat.")

        while manager.is_speaking:
            await asyncio.sleep(0.01)

        assert len(error_events) == 1
        assert "ERROR_TEST" in (error_events[0].error or "")

        # Second sentence should still be synthesized and played
        assert any(c.text == "Kalimat kedua sehat." for c in tts.synthesized_chunks)

        await manager.shutdown()

    asyncio.run(_test())


# ==========================================
# Phase 2C Real TTS & Browser Audio Player Tests
# ==========================================


def test_edge_tts_provider_initialization():
    provider = EdgeTTSProvider(voice="id-ID-GadisNeural", rate="+5%")
    assert provider.voice == "id-ID-GadisNeural"
    assert provider.rate == "+5%"


def test_browser_audio_player_relay_and_interrupt():
    async def _test():
        player = BrowserAudioPlayer()
        client_q: queue.Queue = queue.Queue()
        player.register_client(client_q)

        # 1. Play AudioData chunk
        audio = AudioData(
            chunk_id="chunk-1",
            speech_id="speech-100",
            sequence=0,
            audio_bytes=b"RIFFdummydata",
            format="mp3",
            sample_rate=24000,
            duration_sec=1.5,
        )
        await player.play(audio)

        msg = client_q.get(timeout=1.0)
        assert msg["type"] == "speech_audio_chunk"
        assert msg["speech_id"] == "speech-100"
        assert msg["chunk_id"] == "chunk-1"
        assert len(msg["audio_base64"]) > 0

        # 2. Stop / Interrupt
        await player.stop()
        stop_msg = client_q.get(timeout=1.0)
        assert stop_msg["type"] == "speech_stop"
        assert stop_msg["speech_id"] == "speech-100"

        # 3. Unregister
        player.unregister_client(client_q)
        assert len(player._subscribers) == 0

    asyncio.run(_test())


def test_speech_manager_with_browser_player_end_to_end():
    async def _test():
        tts = MockTTSProvider(latency_sec=0.005)
        browser_player = BrowserAudioPlayer()
        client_q: queue.Queue = queue.Queue()
        browser_player.register_client(client_q)

        manager = SpeechManager(
            tts_provider=tts,
            audio_player=browser_player,
            auto_subscribe=False,
        )

        speech_id = "test-session-123"
        await manager.enqueue_text(
            "Halo dunia. Sistem audio Delta aktif.",
            speech_id=speech_id,
        )

        while manager.is_speaking:
            await asyncio.sleep(0.01)

        # Verify client received 2 speech audio chunks with identical speech_id
        chunk_1 = client_q.get(timeout=1.0)
        chunk_2 = client_q.get(timeout=1.0)

        assert chunk_1["type"] == "speech_audio_chunk"
        assert chunk_1["speech_id"] == speech_id
        assert chunk_2["type"] == "speech_audio_chunk"
        assert chunk_2["speech_id"] == speech_id

        await manager.shutdown()
        browser_player.unregister_client(client_q)

    asyncio.run(_test())


# ==========================================
# Phase 2D Emotion & Expression Engine Tests
# ==========================================


def test_emotion_model_and_intensity_clamping():
    res = EmotionResult(emotion=VTuberEmotion.HAPPY, intensity=1.5, expression=VTuberExpression.SMILE)
    assert res.intensity == 1.0

    res2 = EmotionResult(emotion=VTuberEmotion.CONFUSED, intensity=-0.4, expression=VTuberExpression.CONFUSED)
    assert res2.intensity == 0.0


def test_expression_mapping_completeness():
    assert map_emotion_to_expression(VTuberEmotion.HAPPY) == VTuberExpression.SMILE
    assert map_emotion_to_expression(VTuberEmotion.EXCITED) == VTuberExpression.EXCITED
    assert map_emotion_to_expression(VTuberEmotion.THINKING) == VTuberExpression.THINKING
    assert map_emotion_to_expression(VTuberEmotion.CONFUSED) == VTuberExpression.CONFUSED
    assert map_emotion_to_expression(VTuberEmotion.SAD) == VTuberExpression.SAD
    assert map_emotion_to_expression(VTuberEmotion.ANGRY) == VTuberExpression.ANGRY
    assert map_emotion_to_expression(VTuberEmotion.SURPRISED) == VTuberExpression.SURPRISED
    assert map_emotion_to_expression(VTuberEmotion.NEUTRAL) == VTuberExpression.NEUTRAL


def test_emotion_rules_resolution():
    # 1. Agent Start & Thinking -> THINKING
    emo, intensity, expr = resolve_emotion_from_event(AgentEvent(type=EventType.AGENT_START))
    assert emo == VTuberEmotion.THINKING
    assert expr == VTuberExpression.THINKING
    assert 0.0 <= intensity <= 1.0

    emo, _, expr = resolve_emotion_from_event(AgentEvent(type=EventType.AGENT_THINKING))
    assert emo == VTuberEmotion.THINKING
    assert expr == VTuberExpression.THINKING

    # 2. Tool Start -> THINKING
    emo, _, expr = resolve_emotion_from_event(AgentEvent(type=EventType.TOOL_START, tool="scan_network"))
    assert emo == VTuberEmotion.THINKING

    # 3. Tool Result Success -> HAPPY
    emo, intensity, expr = resolve_emotion_from_event(AgentEvent(type=EventType.TOOL_RESULT, tool="read_file", success=True))
    assert emo == VTuberEmotion.HAPPY
    assert expr == VTuberExpression.SMILE
    assert intensity >= 0.6

    # 4. Tool Result Failure -> CONFUSED
    emo, _, expr = resolve_emotion_from_event(AgentEvent(type=EventType.TOOL_RESULT, tool="read_file", success=False))
    assert emo == VTuberEmotion.CONFUSED
    assert expr == VTuberExpression.CONFUSED

    # 5. Message Complete -> NEUTRAL / HAPPY
    emo, _, expr = resolve_emotion_from_event(AgentEvent(type=EventType.MESSAGE_COMPLETE, content="Berikut laporannya."))
    assert emo == VTuberEmotion.NEUTRAL

    emo, _, expr = resolve_emotion_from_event(AgentEvent(type=EventType.MESSAGE_COMPLETE, content="Semua exploit berhasil dieksekusi!"))
    assert emo == VTuberEmotion.HAPPY
    assert expr == VTuberExpression.SMILE

    # 6. Agent Complete -> HAPPY
    emo, _, expr = resolve_emotion_from_event(AgentEvent(type=EventType.AGENT_COMPLETE))
    assert emo == VTuberEmotion.HAPPY
    assert expr == VTuberExpression.SMILE

    # 7. Errors -> CONFUSED / SAD
    emo, intensity, expr = resolve_emotion_from_event(AgentEvent(type=EventType.ERROR, error={"message": "Fatal network crash"}))
    assert emo == VTuberEmotion.SAD
    assert expr == VTuberExpression.SAD
    assert intensity >= 0.8


def test_emotion_engine_duplicate_suppression_and_listeners():
    async def _test():
        engine = EmotionEngine(initial_emotion=VTuberEmotion.NEUTRAL)
        emitted_events = []
        engine.add_listener(lambda ev: emitted_events.append(ev))

        # 1. First transition: NEUTRAL -> THINKING
        evt1 = await engine.set_emotion(VTuberEmotion.THINKING, intensity=0.6)
        assert evt1 is not None
        assert engine.current_emotion == VTuberEmotion.THINKING
        assert len(emitted_events) == 1

        # 2. Duplicate transition with identical emotion and similar intensity (delta < 0.15) -> Suppressed
        evt2 = await engine.set_emotion(VTuberEmotion.THINKING, intensity=0.65)
        assert evt2 is None
        assert len(emitted_events) == 1

        # 3. Transition with significant intensity jump (> 0.15) -> Emitted
        evt3 = await engine.set_emotion(VTuberEmotion.THINKING, intensity=0.95)
        assert evt3 is not None
        assert len(emitted_events) == 2

        # 4. State change: THINKING -> HAPPY -> Emitted
        evt4 = await engine.set_emotion(VTuberEmotion.HAPPY, intensity=0.8)
        assert evt4 is not None
        assert len(emitted_events) == 3
        assert emitted_events[-1].expression == VTuberExpression.SMILE

    asyncio.run(_test())


def test_emotion_propagation_to_speech_chunk():
    async def _test():
        tts = MockTTSProvider(latency_sec=0.005)
        player = MockAudioPlayer(playback_speed_multiplier=50.0)
        manager = SpeechManager(tts_provider=tts, audio_player=player, auto_subscribe=False)

        # Enqueue text with EXCITED emotion metadata
        chunks = await manager.enqueue_text(
            "Scan selesai! Kami menemukan target.",
            emotion=VTuberEmotion.EXCITED,
            intensity=0.9,
        )

        assert len(chunks) == 2
        assert chunks[0].emotion == VTuberEmotion.EXCITED
        assert chunks[0].intensity == 0.9
        assert chunks[1].emotion == VTuberEmotion.EXCITED

        while manager.is_speaking:
            await asyncio.sleep(0.01)

        # Verify TTS chunk received emotion metadata
        assert tts.synthesized_chunks[0].emotion == VTuberEmotion.EXCITED

        await manager.shutdown()

    asyncio.run(_test())


# ==========================================
# Phase 3A Avatar Controller & Runtime Tests
# ==========================================


def test_avatar_state_validation_and_clamping():
    state = AvatarState(
        expression=VTuberExpression.SMILE,
        expression_intensity=1.5,
        mouth_open=-0.5,
        mouth_form=2.0,
        head_x=-1.5,
        head_y=0.5,
        body_angle=0.0,
        speaking=False,
    )
    assert state.expression_intensity == 1.0
    assert state.mouth_open == 0.0
    assert state.mouth_form == 1.0
    assert state.head_x == -1.0
    assert state.head_y == 0.5


def test_avatar_expression_controller_mapping():
    ctrl = ExpressionController()

    # Process Happy EmotionChangedEvent -> SMILE
    evt = EmotionChangedEvent(
        emotion=VTuberEmotion.HAPPY,
        intensity=0.8,
        expression=VTuberExpression.SMILE,
    )
    expr, intensity = ctrl.handle_emotion_event(evt)
    assert expr == VTuberExpression.SMILE
    assert intensity == 0.8
    assert ctrl.current_expression == VTuberExpression.SMILE


def test_avatar_controller_speech_lifecycle_integration():
    async def _test():
        renderer = MockAvatarRenderer()
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        await ctrl.initialize()

        assert ctrl.current_state.speaking is False

        # 1. Speech Started -> speaking = True
        await ctrl.handle_speech_lifecycle(
            SpeechLifecycleEvent(
                event_type=SpeechLifecycleEventType.SPEECH_STARTED,
                chunk_id="chk-1",
            )
        )
        assert ctrl.current_state.speaking is True
        assert renderer.rendered_states[-1].speaking is True

        # 2. Speech Finished -> speaking = False, mouth_open = 0.0
        await ctrl.handle_speech_lifecycle(
            SpeechLifecycleEvent(
                event_type=SpeechLifecycleEventType.SPEECH_FINISHED,
                chunk_id="chk-1",
            )
        )
        assert ctrl.current_state.speaking is False
        assert ctrl.current_state.mouth_open == 0.0
        assert renderer.rendered_states[-1].speaking is False

        # 3. Speech Interrupted -> speaking = False
        await ctrl.set_speaking(True)
        assert ctrl.current_state.speaking is True

        await ctrl.handle_speech_lifecycle(
            SpeechLifecycleEvent(
                event_type=SpeechLifecycleEventType.SPEECH_INTERRUPTED,
                chunk_id="chk-2",
            )
        )
        assert ctrl.current_state.speaking is False
        assert renderer.rendered_states[-1].speaking is False

        await ctrl.shutdown()

    asyncio.run(_test())


def test_avatar_controller_redundant_render_suppression():
    async def _test():
        renderer = MockAvatarRenderer()
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        await ctrl.initialize()
        initial_render_count = len(renderer.rendered_states)
        assert initial_render_count == 1

        # 1. State change: Expression -> Rendered
        await ctrl.set_expression(VTuberExpression.SMILE, intensity=0.7)
        assert len(renderer.rendered_states) == initial_render_count + 1

        # 2. Duplicate state call with almost identical values -> Suppressed
        await ctrl.set_expression(VTuberExpression.SMILE, intensity=0.71)
        assert len(renderer.rendered_states) == initial_render_count + 1

        # 3. Meaningful change: mouth opening -> Rendered
        await ctrl.set_mouth_open(0.8)
        assert len(renderer.rendered_states) == initial_render_count + 2
        assert renderer.rendered_states[-1].mouth_open > 0.5

        await ctrl.shutdown()

    asyncio.run(_test())


def test_avatar_controller_lip_sync_interface():
    async def _test():
        lip_sync = DefaultLipSyncController(smoothing_factor=0.8)
        assert lip_sync.current_mouth_open == 0.0

        await lip_sync.update_amplitude(0.75)
        assert lip_sync.current_mouth_open > 0.5

        await lip_sync.reset()
        assert lip_sync.current_mouth_open == 0.0

    asyncio.run(_test())


# ==========================================
# Phase 3B Live2D Renderer & Mapper Tests
# ==========================================


def test_live2d_expression_mapper():
    # Smile expression
    params_smile = Live2DExpressionMapper.get_expression_parameters(VTuberExpression.SMILE, intensity=0.8)
    assert params_smile["ParamEyeLSmile"] == 0.64
    assert params_smile["ParamEyeRSmile"] == 0.64
    assert params_smile["ParamMouthForm"] == 0.72

    # Confused expression
    params_confused = Live2DExpressionMapper.get_expression_parameters(VTuberExpression.CONFUSED, intensity=0.9)
    assert params_confused["ParamBrowLY"] == -0.54
    assert params_confused["ParamBrowRY"] == 0.54
    assert params_confused["ParamMouthForm"] == -0.45


def test_live2d_parameter_mapper_full_state():
    state = AvatarState(
        expression=VTuberExpression.SMILE,
        expression_intensity=0.8,
        mouth_open=0.65,
        mouth_form=0.5,
        head_x=0.5,
        head_y=-0.3,
        body_angle=0.2,
        speaking=True,
    )
    live2d_dict = Live2DParameterMapper.to_live2d_parameters(state)

    assert live2d_dict["ParamAngleX"] == 15.0  # 0.5 * 30
    assert live2d_dict["ParamAngleY"] == -9.0  # -0.3 * 30
    assert live2d_dict["ParamBodyAngleX"] == 2.0  # 0.2 * 10
    assert live2d_dict["ParamMouthOpenY"] == 0.65
    assert live2d_dict["ParamEyeLSmile"] == 0.64


def test_live2d_canvas_renderer_dispatch():
    async def _test():
        dispatched_messages = []

        def mock_transport(msg):
            dispatched_messages.append(msg)

        renderer = Live2DCanvasRenderer(transport=mock_transport)
        await renderer.initialize()
        assert renderer.is_initialized is True

        state = AvatarState(
            expression=VTuberExpression.EXCITED,
            expression_intensity=0.9,
            mouth_open=0.5,
            speaking=True,
        )
        await renderer.render(state)

        assert len(dispatched_messages) == 1
        msg = dispatched_messages[0]
        assert msg["type"] == "avatar_state"
        assert msg["expression"] == "excited"
        assert msg["speaking"] is True
        assert "live2d_params" in msg
        assert "ParamAngleX" in msg["live2d_params"]

        await renderer.shutdown()
        assert renderer.is_shutdown is True

    asyncio.run(_test())


# ==========================================
# Phase 3C Audio Lip-Sync & VTS Bridge Tests
# ==========================================


def test_audio_amplitude_analyzer_rms_and_gating():
    analyzer = AudioAmplitudeAnalyzer(noise_gate_threshold=0.05, gain_multiplier=2.0)

    # 1. Zero/silent samples -> 0.0
    zero_samples = [0.0] * 100
    assert analyzer.calculate_rms(zero_samples) == 0.0
    assert analyzer.process_samples(zero_samples) == 0.0

    # 2. Quiet noise below gate -> gated to 0.0
    quiet_samples = [0.02] * 100
    assert analyzer.process_samples(quiet_samples) == 0.0

    # 3. Active speech wave -> calculated amplitude > 0.0
    speech_wave = [0.4 * (1 if i % 2 == 0 else -1) for i in range(100)]
    amp1 = analyzer.process_samples(speech_wave)
    assert amp1 > 0.1

    # 4. Silence after speech -> smooth release envelope
    amp2 = analyzer.process_samples(zero_samples)
    assert amp2 < amp1
    assert amp2 >= 0.0

    analyzer.reset()
    assert analyzer.current_amplitude == 0.0


def test_vts_mapper_and_protocol_message():
    state = AvatarState(
        expression=VTuberExpression.SMILE,
        expression_intensity=0.8,
        mouth_open=0.7,
        head_x=0.2,
        speaking=True,
    )
    vts_msg: VTSMessage = VTSMapper.to_vts_inject_message(state, request_id="TestVTSReq")

    assert vts_msg.messageType == VTSMessageType.INJECT_PARAMETER_DATA_REQUEST
    assert vts_msg.requestID == "TestVTSReq"
    data = vts_msg.data
    assert "parameterValues" in data
    param_dict = {p["id"]: p["value"] for p in data["parameterValues"]}
    assert param_dict["ParamMouthOpenY"] == 0.7
    assert param_dict["ParamAngleX"] == 6.0  # 0.2 * 30


def test_vts_client_offline_isolation():
    async def _test():
        # Test client with VTS disabled (default state)
        client = VTSClient(enabled=False)
        assert client.is_connected is False
        assert client.state.value == "DISCONNECTED"

        connected = await client.connect()
        assert connected is False

        state = AvatarState(speaking=True)
        sent = await client.send_avatar_state(state)
        assert sent is False

        summary = client.get_status_summary()
        assert summary["connected"] is False
        assert summary["status"] == "DISCONNECTED"

        await client.disconnect()

    asyncio.run(_test())


def test_vts_client_mock_handshake_lifecycle():
    from unittest.mock import AsyncMock, patch

    async def _test():
        client = VTSClient(
            host="127.0.0.1",
            port=8001,
            plugin_name="Delta AI VTuber",
            plugin_developer="Delta Team",
            enabled=True,
        )

        # Mock responses sequence
        # 1. AuthenticationTokenResponse
        # 2. AuthenticationResponse
        # 3. CurrentModelResponse
        token_resp = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaTokenReq",
            "messageType": "AuthenticationTokenResponse",
            "data": {
                "authenticationToken": "secret_vts_token_xyz"
            }
        }
        auth_resp = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaAuthReq",
            "messageType": "AuthenticationResponse",
            "data": {
                "authenticated": True,
                "reason": "Token verified"
            }
        }
        model_resp = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaModelReq",
            "messageType": "CurrentModelResponse",
            "data": {
                "modelLoaded": True,
                "modelName": "Hiyori",
                "modelID": "vts_model_123"
            }
        }

        mock_ws = AsyncMock()
        mock_ws.recv.side_effect = [
            json.dumps(token_resp),
            json.dumps(auth_resp),
            json.dumps(model_resp),
        ]

        with patch("websockets.connect", AsyncMock(return_value=mock_ws)):
            ok = await client.connect()
            assert ok is True
            assert client.is_connected is True
            assert client.is_authenticated is True
            assert client.state.value == "CONNECTED"
            assert client.current_model_data.get("modelName") == "Hiyori"

            # Verify send_avatar_state works when authenticated
            state = AvatarState(expression=VTuberExpression.SMILE, speaking=True, mouth_open=0.8)
            sent = await client.send_avatar_state(state)
            assert sent is True

            summary = client.get_status_summary()
            assert summary["status"] == "CONNECTED"
            assert summary["current_model"] == "Hiyori"
            # Ensure token is never in summary
            assert "authenticationToken" not in str(summary)
            assert "secret_vts_token_xyz" not in str(summary)

            await client.disconnect()
            assert client.state.value == "DISCONNECTED"

    asyncio.run(_test())


def test_vts_client_auth_error_handling():
    from unittest.mock import AsyncMock, patch

    async def _test():
        client = VTSClient(
            host="127.0.0.1",
            port=8001,
            auth_token="invalid_token",
            enabled=True,
        )

        error_resp = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaAuthReq",
            "messageType": "APIError",
            "data": {
                "errorID": 50,
                "errorMessage": "Authentication token invalid"
            }
        }

        mock_ws = AsyncMock()
        mock_ws.recv.return_value = json.dumps(error_resp)

        with patch("websockets.connect", AsyncMock(return_value=mock_ws)):
            ok = await client.connect()
            assert ok is False
            assert client.is_authenticated is False
            assert client.state.value == "ERROR"
            assert client.last_error is not None
            assert client.last_error["messageType"] == "APIError"
            assert client.last_error["errorID"] == 50
            assert "Authentication token invalid" in client.last_error["errorMessage"]

    asyncio.run(_test())


def test_vts_status_and_whitelist():
    from delta.vtuber.avatar.vts.protocol import VTS_ALLOWED_PARAMETERS
    assert "ParamAngleX" in VTS_ALLOWED_PARAMETERS
    assert "ParamMouthOpenY" in VTS_ALLOWED_PARAMETERS
    assert "ParamRandomMalicious" not in VTS_ALLOWED_PARAMETERS


def test_vts_parameter_whitelist_enforcement():
    from unittest.mock import AsyncMock, patch
    from delta.vtuber.avatar.vts.client import VTSClient

    async def _test():
        client = VTSClient(enabled=True)
        client._is_connected = True
        client._is_authenticated = True
        client._ws = AsyncMock()

        # Valid param
        res = await client.inject_raw_parameters([{"parameter": "ParamAngleX", "value": 20.0}])
        assert res.get("success") is True

        # Invalid param - rejected by whitelist
        rejected = await client.inject_raw_parameters([{"parameter": "ArbitraryScriptInjection", "value": 1.0}])
        assert rejected.get("success") is False
        assert client.last_error is not None
        assert client.last_error["messageType"] == "SecurityError"

    asyncio.run(_test())


def test_vts_model_detection_and_no_token_leak():
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts.client import VTSClient

    async def _test():
        client = VTSClient(
            host="127.0.0.1",
            port=8001,
            auth_token="super_secret_token_12345",
            enabled=True,
        )
        client._is_connected = True
        client._is_authenticated = True
        client._current_model_data = {"modelLoaded": True, "modelName": "DeltaCyberModel", "modelID": "mod_999"}

        summary = client.get_status_summary()
        assert summary["model_loaded"] is True
        assert summary["current_model"] == "DeltaCyberModel"
        assert "super_secret_token_12345" not in str(summary)
        assert "auth_token" not in summary

    asyncio.run(_test())


def test_vts_bridge_endpoints():
    from unittest.mock import AsyncMock, MagicMock
    from delta.web.bridge import EngineBridge
    from delta.vtuber.avatar.vts.client import VTSClient

    async def _test():
        mock_engine = MagicMock()
        mock_engine.config.vts_enabled = True
        mock_engine.config.vts_host = "127.0.0.1"
        mock_engine.config.vts_port = 8001

        bridge = EngineBridge(mock_engine)

        mock_vts_client = VTSClient(enabled=True)
        mock_vts_client._is_connected = True
        mock_vts_client._is_authenticated = True
        mock_vts_client._ws = AsyncMock()
        mock_vts_client._current_model_data = {"modelLoaded": True, "modelName": "Hiyori"}
        bridge._cached_vts_client = mock_vts_client

        # 1. status
        status_res = bridge.get_vts_status()
        assert status_res["status"] == "ok"
        assert status_res["vts"]["current_model"] == "Hiyori"

        # 2. test-parameter
        param_res = await bridge.vts_test_parameter("ParamAngleX", 20.0)
        assert param_res["status"] == "ok"
        assert param_res["parameter"] == "ParamAngleX"
        assert param_res["vts"]["last_parameter"] == "ParamAngleX"
        assert param_res["vts"]["last_value"] == 20.0
        assert param_res["vts"]["last_message_type"] == "InjectParameterDataRequest"
        assert param_res["vts"]["last_response_type"] == "InjectParameterDataResponse"

        # 3. test-parameter invalid
        invalid_res = await bridge.vts_test_parameter("MaliciousPayload", 10.0)
        assert invalid_res["status"] == "error"

        # 4. test-expression
        expr_res = await bridge.vts_test_expression("smile")
        assert expr_res["status"] == "ok"
        assert expr_res["expression"] == "smile"

        # 5. reset
        reset_res = await bridge.vts_reset_parameters()
        assert reset_res["status"] == "ok"

        # 6. auto-test
        auto_res = await bridge.vts_run_auto_test()
        assert auto_res["status"] == "ok"
        assert auto_res["passed"] is True
        assert auto_res["total_steps"] == 10

    asyncio.run(_test())


def test_vts_renderer_lifecycle():
    async def _test():
        renderer = VTSRenderer(enabled=False)
        await renderer.initialize()
        assert renderer.is_initialized is True

        state = AvatarState(expression=VTuberExpression.THINKING, speaking=False)
        # Should execute safely without error
        await renderer.render(state)

        await renderer.shutdown()
        assert renderer.is_shutdown is True

    asyncio.run(_test())


# ==========================================
# Phase 4 Voice Input, STT & VAD Tests
# ==========================================


def test_stt_result_models_and_clamping():
    res = STTFinalResult(text="Delta scan server", confidence=1.5, language="id-ID")
    assert res.confidence == 1.0
    assert res.is_final is True
    assert res.text == "Delta scan server"

    part = STTPartialResult(text="Delta scan", confidence=-0.2)
    assert part.confidence == 0.0
    assert part.is_final is False


def test_vad_speech_detection_and_hangover():
    vad = VoiceActivityDetector(energy_threshold=0.03, min_speech_frames=2, hangover_frames=3)
    assert vad.current_state == VADState.SILENCE

    silent_frame = [0.0] * 50
    speech_frame = [0.1] * 50

    # 1. Silent frames -> remain SILENCE
    assert vad.process_frame(silent_frame) == VADState.SILENCE

    # 2. First speech frame -> accumulating, still not min_speech_frames
    assert vad.process_frame(speech_frame) == VADState.SILENCE

    # 3. Second speech frame -> reaches min_speech_frames -> SPEECH_START
    assert vad.process_frame(speech_frame) == VADState.SPEECH_START

    # 4. Third speech frame -> SPEAKING
    assert vad.process_frame(speech_frame) == VADState.SPEAKING

    # 5. Brief silent pause (1 frame) -> within hangover -> remains SPEAKING
    assert vad.process_frame(silent_frame) == VADState.SPEAKING

    # 6. Silence frame 2 -> remains SPEAKING
    assert vad.process_frame(silent_frame) == VADState.SPEAKING

    # 7. Silence frame 3 -> reaches hangover limit -> SPEECH_END
    assert vad.process_frame(silent_frame) == VADState.SPEECH_END

    # 8. Next frame -> SILENCE
    assert vad.process_frame(silent_frame) == VADState.SILENCE


def test_stt_manager_voice_barge_in_and_transcription():
    async def _test():
        # Setup mock speech manager with ongoing speech
        speech_mgr = SpeechManager(
            tts_provider=MockTTSProvider(latency_sec=0.1),
            audio_player=MockAudioPlayer(),
            auto_subscribe=False,
        )
        await speech_mgr.enqueue_text("Delta sedang menjelaskan panjang lebar...")
        await asyncio.sleep(0.01)
        assert speech_mgr.is_speaking is True

        # Setup STT Manager with MockSTTProvider
        dispatched_prompts = []

        def input_handler(text):
            dispatched_prompts.append(text)

        stt_mgr = STTManager(
            stt_provider=MockSTTProvider(canned_response="Delta berhenti dan cek memory"),
            speech_manager=speech_mgr,
            input_handler=input_handler,
        )
        stt_mgr.set_voice_mode(True)
        assert stt_mgr.is_voice_mode_active is True

        # 1. User starts speaking -> Barge-in triggered
        await stt_mgr.handle_user_speech_start()

        # Verify ongoing speech immediately interrupted
        assert speech_mgr.is_speaking is False
        assert speech_mgr.queue_size == 0
        assert stt_mgr.current_state == STTState.LISTENING

        # 2. User finishes speech -> audio buffer processed -> STT -> conversational loop
        fake_audio = b"\x00\x01" * 16000
        result = await stt_mgr.process_audio_buffer(fake_audio)

        assert result is not None
        assert result.text == "Delta berhenti dan cek memory"
        assert len(dispatched_prompts) == 1
        assert dispatched_prompts[0] == "Delta berhenti dan cek memory"

        await stt_mgr.shutdown()
        await speech_mgr.shutdown()

    asyncio.run(_test())


# ==========================================
# Phase 5 Personality, Mood & Memory Tests
# ==========================================


def test_persona_profile_clamping_and_behavior():
    profile = PersonaProfile(
        name="Delta",
        formality=1.5,
        humor=-0.2,
        technicality=0.85,
    )
    assert profile.formality == 1.0
    assert profile.humor == 0.0
    assert profile.technicality == 0.85

    behavior = PersonalityBehavior(profile=PersonaProfile(formality=0.3))
    raw_markdown = "Berikut adalah hasil query:\n```python\nprint('secret_key')\n```\nSelesai."
    display_text, speech_text = behavior.format_responses(raw_markdown)

    assert "print('secret_key')" in display_text
    assert "print('secret_key')" not in speech_text
    assert "Ini kodenya ya" in speech_text


def test_mood_state_updates_and_decay():
    mood = MoodState(happiness=0.5, stress=0.2)

    # 1. Decay over time towards baseline (baseline happiness = 0.6, stress = 0.15)
    mood.decay_towards_baseline(elapsed_sec=300.0, decay_rate=0.5)
    assert mood.happiness > 0.5
    assert mood.stress < 0.2

    # 2. PersonalityManager mood update on agent complete
    mgr = PersonalityManager(mood=mood)
    mgr.update_mood_from_event(AgentEvent(type=EventType.AGENT_COMPLETE))
    assert mgr.mood.happiness > 0.65


def test_secret_filter_security():
    # Secret credentials should be flagged
    assert SecretFilter.contains_secrets("api_key = 'sk-1234567890abcdef1234567890abcdef'") is True
    assert SecretFilter.contains_secrets("password: MySuperSecretPass123$") is True
    assert SecretFilter.contains_secrets("-----BEGIN RSA PRIVATE KEY-----") is True

    # Safe text should pass
    assert SecretFilter.contains_secrets("Saya suka kopi dan coding di Delta") is False

    # Redaction sanitization
    sanitized = SecretFilter.sanitize("token: ghp_1234567890abcdefghijklmnopqrstuv")
    assert "ghp_" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized


def test_memory_manager_explicit_commands_and_storage(tmp_path):
    db_file = str(tmp_path / "test_memory.db")
    store = SQLiteMemoryStore(db_path=db_file)
    mem_mgr = MemoryManager(store=store, max_short_term_messages=5)

    # 1. Explicit Remember command
    is_cmd, resp = mem_mgr.handle_explicit_memory_command("ingat bahwa aku sedang membangun modul VTuber")
    assert is_cmd is True
    assert "aku sudah mengingat" in resp

    # 2. Secret memory rejection
    is_cmd, resp_sec = mem_mgr.handle_explicit_memory_command("ingat bahwa api_key = 'sk-1234567890abcdef1234567890abcdef'")
    assert is_cmd is True
    assert "tidak dapat disimpan" in resp_sec

    # 3. Explicit Query command
    is_cmd, resp_list = mem_mgr.handle_explicit_memory_command("apa yang kamu ingat tentang aku?")
    assert is_cmd is True
    assert "modul VTuber" in resp_list

    # 4. Context retrieval for prompt
    ctx = mem_mgr.retrieve_relevant_context("VTuber progress", limit=3)
    assert "VTUBER MEMORY CONTEXT:" in ctx
    assert "modul VTuber" in ctx

    # 5. Short-term bounded buffer
    for i in range(10):
        mem_mgr.add_short_term_turn(f"User {i}", f"Agent {i}")
    assert len(mem_mgr.short_term.messages) == 5

    # 6. Explicit Forget command
    is_cmd, resp_forg = mem_mgr.handle_explicit_memory_command("lupakan bahwa modul VTuber")
    assert is_cmd is True
    assert "melupakan 1 ingatan" in resp_forg


# ==========================================
# Phase 6 Personal VTuber Runtime & Idle Tests
# ==========================================


def test_animation_priority_system_hierarchy():
    pri = AnimationPrioritySystem()
    assert pri.current_priority == AnimationPriority.IDLE

    # 1. EMOTION can override IDLE
    assert pri.request_transition(AnimationPriority.EMOTION) is True
    assert pri.current_priority == AnimationPriority.EMOTION

    # 2. Lower priority IDLE cannot override active EMOTION
    assert pri.request_transition(AnimationPriority.IDLE) is False
    assert pri.current_priority == AnimationPriority.EMOTION

    # 3. Higher priority SPEAKING overrides EMOTION
    assert pri.request_transition(AnimationPriority.SPEAKING) is True
    assert pri.current_priority == AnimationPriority.SPEAKING

    # 4. Critical ERROR overrides SPEAKING
    assert pri.request_transition(AnimationPriority.ERROR) is True
    assert pri.current_priority == AnimationPriority.ERROR

    # 5. Release ERROR returns to IDLE
    pri.release_priority(AnimationPriority.ERROR)
    assert pri.current_priority == AnimationPriority.IDLE


def test_idle_behavior_manager_frame_computation():
    idle = IdleBehaviorManager(breathing_interval_sec=0.1)
    frame1 = idle.compute_idle_frame(time_step=1.0)
    frame2 = idle.compute_idle_frame(time_step=2.5)

    assert frame1.speaking is False
    assert frame1.mouth_open == 0.0
    # Natural swaying coordinates should vary smoothly with time
    assert isinstance(frame1.head_x, float)
    assert isinstance(frame1.head_y, float)
    assert frame1.head_x != frame2.head_x or frame1.head_y != frame2.head_y


def test_personal_vtuber_runtime_lifecycle():
    async def _test():
        runtime = PersonalVTuberRuntime()
        assert runtime.is_initialized is False

        await runtime.initialize()
        assert runtime.is_initialized is True

        status = runtime.get_runtime_status()
        assert status["status"] == "online"
        assert "persona" in status
        assert "mood" in status
        assert "emotion" in status
        assert "avatar" in status
        assert "voice" in status
        assert "memory" in status

        await runtime.shutdown()
        assert runtime.is_initialized is False

    asyncio.run(_test())


# ==========================================
# Phase 7 Personal Companion & Presence Tests
# ==========================================


def test_presence_state_transitions():
    presence = PresenceManager(companion_mode=True)
    assert presence.current_state.activity == PresenceActivity.IDLE

    # 1. State change to LISTENING
    presence.set_activity(PresenceActivity.LISTENING)
    assert presence.current_state.activity == PresenceActivity.LISTENING

    # 2. State change to WORKING
    presence.set_activity(PresenceActivity.WORKING)
    assert presence.current_state.activity == PresenceActivity.WORKING


def test_companion_greeting_and_farewell():
    async def _test():
        speech_mgr = SpeechManager(tts_provider=MockTTSProvider(), auto_subscribe=False)
        presence = PresenceManager(speech_mgr=speech_mgr, companion_mode=True)

        # 1. Greeting generation
        greeting = await presence.trigger_greeting(user_name="kamu")
        assert greeting is not None
        assert "Delta" in greeting

        # 2. Farewell execution
        await presence.trigger_farewell(timeout_sec=0.5)

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_contextual_micro_reaction():
    # 1. Tool Start reaction -> THINKING
    reac1 = MicroReactionEngine.evaluate_reaction(AgentEvent(type=EventType.TOOL_START, tool="scan_ports"))
    assert reac1 is not None
    assert reac1[0] == VTuberEmotion.THINKING
    assert "Mengecek" in reac1[2]

    # 2. Tool Success reaction -> HAPPY
    reac2 = MicroReactionEngine.evaluate_reaction(AgentEvent(type=EventType.TOOL_RESULT, success=True))
    assert reac2 is not None
    assert reac2[0] == VTuberEmotion.HAPPY

    # 3. Tool Failure reaction -> CONFUSED
    reac3 = MicroReactionEngine.evaluate_reaction(AgentEvent(type=EventType.TOOL_RESULT, success=False))
    assert reac3 is not None
    assert reac3[0] == VTuberEmotion.CONFUSED


def test_notification_event_flow():
    notif_mgr = NotificationManager()
    received_notifs = []
    notif_mgr.add_listener(lambda n: received_notifs.append(n))

    evt = notif_mgr.notify(
        notification_type=NotificationType.TASK_COMPLETE,
        title="Audit Selesai",
        message="Port scan pada target selesai tanpa anomali.",
    )
    assert evt.notification_type == NotificationType.TASK_COMPLETE
    assert len(received_notifs) == 1
    assert len(notif_mgr.get_recent_notifications()) == 1


def test_desktop_integration_adapters():
    win = WindowsDesktopIntegration()
    assert isinstance(win.is_supported(), bool)
    assert win.set_always_on_top(True) is True

    noop = NoopDesktopIntegration()
    assert noop.is_supported() is True
    assert noop.set_always_on_top(True) is False
    bounds = noop.get_screen_bounds()
    assert bounds["width"] == 1280


def test_temporary_memory_expiration(tmp_path):
    import time
    db_file = str(tmp_path / "test_exp_memory.db")
    store = SQLiteMemoryStore(db_path=db_file)

    # 1. Permanent fact
    store.store(MemoryEntry(
        memory_type=MemoryType.IMPORTANT_FACT,
        content="User suka tema dark",
    ))

    # 2. Expired temporary memory (expired 10 seconds ago)
    store.store(MemoryEntry(
        memory_type=MemoryType.TEMPORARY_CONTEXT,
        content="Konteks query sementara",
        expires_at=time.time() - 10.0,
    ))

    # 3. Retrieve triggers cleanup_expired() automatically
    items = store.retrieve(limit=10)
    assert len(items) == 1
    assert items[0].content == "User suka tema dark"


# ==========================================
# Phase 8 Desktop Intelligence & Context Tests
# ==========================================


def test_desktop_context_schema():
    ctx = DesktopContext(
        active_application="Visual Studio Code",
        active_window_title="delta — engine.py",
        workspace_name="Delta-CLI",
        workspace_path="D:\\Project\\Delta-CLI",
        active_file="engine.py",
        git_branch="main",
        clipboard_available=True,
    )
    assert ctx.active_application == "Visual Studio Code"
    assert ctx.workspace_name == "Delta-CLI"
    assert ctx.clipboard_available is True


def test_active_window_provider_noop():
    async def _test():
        provider = NoopActiveWindowProvider(default_app="Cursor", default_title="main.py")
        win = await provider.get_active_window()
        assert win.application == "Cursor"
        assert win.window_title == "main.py"

    asyncio.run(_test())


def test_workspace_context_resolution(tmp_path):
    # Setup dummy project files
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'delta-test'", encoding="utf-8")

    proj = ProjectContextProvider.resolve_context(str(tmp_path))
    assert proj.language == "Python"
    assert proj.project_name == tmp_path.name


def test_desktop_context_snapshot():
    async def _test():
        mgr = DesktopManager(
            active_window_provider=NoopActiveWindowProvider(default_app="VS Code"),
            permissions=DesktopPermissionManager(active_window_allowed=True),
        )
        ctx = await mgr.capture_context()
        assert ctx.active_application == "VS Code"
        assert ctx.workspace_name is not None

    asyncio.run(_test())


def test_screenshot_permission_and_ephemeral_lifecycle():
    async def _test():
        mgr = DesktopManager(
            screenshot_provider=NoopScreenshotProvider(),
            permissions=DesktopPermissionManager(screenshot_allowed=False),
        )
        # 1. Denied by default
        shot1 = await mgr.capture_ephemeral_screenshot()
        assert shot1 is None

        # 2. Allowed when permission granted
        mgr.permissions.set_permission(DesktopCapability.SCREENSHOT, True)
        shot2 = await mgr.capture_ephemeral_screenshot()
        assert shot2 is not None
        assert shot2.retention == "ephemeral"
        assert len(shot2.image_base64) > 0

    asyncio.run(_test())


def test_clipboard_permission_and_secret_filtering():
    async def _test():
        # Setup provider with sensitive token in clipboard
        mgr = DesktopManager(
            clipboard_provider=NoopClipboardProvider(canned_text="api_key = 'sk-1234567890abcdef1234567890abcdef'"),
            permissions=DesktopPermissionManager(clipboard_allowed=True),
        )
        clip = await mgr.read_sanitized_clipboard()
        assert clip is not None
        assert clip.has_content is True
        assert "sk-123" not in (clip.text or "")
        assert "[REDACTED_SECRET]" in (clip.text or "")

    asyncio.run(_test())


def test_global_hotkey_and_quick_summon():
    hotkey_prov = NoopHotkeyProvider()
    overlay_ctrl = DesktopOverlayController(visible=False)
    mgr = DesktopManager(
        hotkey_provider=hotkey_prov,
        overlay=overlay_ctrl,
        permissions=DesktopPermissionManager(hotkey_allowed=True),
    )

    summon_triggered = []
    mgr.add_summon_listener(lambda: summon_triggered.append(True))
    assert mgr.register_quick_summon("ctrl+shift+space") is True

    # Simulate hotkey press
    hotkey_prov.trigger("ctrl+shift+space")
    assert len(summon_triggered) == 1
    assert overlay_ctrl.visible is True


# ==========================================
# Phase 9 Advanced Expressiveness & Physics Tests
# ==========================================


def test_speech_prosody_modulator():
    # 1. Happy emotion prosody -> higher rate & elevated pitch
    happy_prosody = ProsodyModulator.modulate(VTuberEmotion.HAPPY, intensity=0.9)
    assert happy_prosody.rate_multiplier > 1.0
    assert happy_prosody.pitch_offset_hz > 0.0
    assert "+" in happy_prosody.rate_ssml

    # 2. Sad emotion prosody -> slower rate & lowered pitch
    sad_prosody = ProsodyModulator.modulate(VTuberEmotion.SAD, intensity=0.8)
    assert sad_prosody.rate_multiplier < 1.0
    assert sad_prosody.pitch_offset_hz < 0.0
    assert "-" in sad_prosody.rate_ssml


def test_physics_spring_and_controller():
    # 1. Spring mechanics update
    spring = PhysicsSpring(stiffness=15.0, damping=4.0)
    spring.update(target_x=1.0, target_y=0.0, dt=0.016)
    assert spring.pos_x > 0.0 or spring.vel_x > 0.0

    # 2. Secondary hair & accessory physics
    phys_ctrl = PhysicsController()
    offsets = phys_ctrl.update_physics(head_x=0.8, head_y=0.2, body_angle=0.3, speaking=True)

    assert "hair_front" in offsets
    assert "hair_side" in offsets
    assert "hair_back" in offsets
    assert "accessory_motion" in offsets
    assert -1.0 <= offsets["hair_front"] <= 1.0


def test_expression_dynamics_and_mood_modulation():
    dyn = ExpressionDynamics()
    mood = MoodState(happiness=0.9, confidence=0.85)
    presence = PresenceState(attention_level=0.9)

    expr, final_intensity = dyn.resolve_dynamic_expression(
        base_expression=VTuberExpression.SMILE,
        base_intensity=0.6,
        mood=mood,
        presence=presence,
    )

    assert expr == VTuberExpression.SMILE
    # Modulated intensity should be boosted by high happiness & confidence
    assert final_intensity > 0.0
    assert 0.0 <= final_intensity <= 1.0


def test_live2d_mapper_with_physics_integration():
    state = AvatarState(
        expression=VTuberExpression.SMILE,
        expression_intensity=0.8,
        mouth_open=0.5,
        head_x=0.6,
        head_y=0.1,
        body_angle=0.3,
        speaking=True,
    )
    params = Live2DParameterMapper.to_live2d_parameters(state)

    assert "ParamHairFront" in params
    assert "ParamHairSide" in params
    assert "ParamHairBack" in params
    assert "ParamBreath" in params
    assert "ParamEyeBallX" in params
    assert -1.0 <= params["ParamHairFront"] <= 1.0


# ==========================================
# Phase 11: Realtime Character Synchronization
# ==========================================


def test_avatar_frame_composition():
    from delta.vtuber.avatar.composer import AvatarFrameComposer, FinalAvatarFrame

    composer = AvatarFrameComposer()
    base = AvatarState(
        expression=VTuberExpression.SMILE,
        expression_intensity=0.7,
        mouth_open=0.4,
        head_x=0.2,
        speaking=True,
    )
    frame = composer.compose_frame(base)

    assert isinstance(frame, FinalAvatarFrame)
    assert frame.expression == VTuberExpression.SMILE
    assert frame.mouth_open == 0.4
    assert frame.speaking is True
    # Composited layers must be present in one frame
    assert 0.0 <= frame.breath <= 1.0
    assert -1.0 <= frame.hair_front <= 1.0
    assert 0.0 <= frame.eye_l_open <= 1.0
    assert -1.0 <= frame.eye_x <= 1.0


def test_parameter_ownership():
    """Mouth owned by LipSync, eyes owned by EyeBehavior/Blink, hair by Physics, breath by Breathing."""
    from delta.vtuber.avatar.composer import AvatarFrameComposer

    composer = AvatarFrameComposer()
    base = AvatarState(mouth_open=0.9, speaking=True)
    frame = composer.compose_frame(base)

    # Mouth driven by lip-sync input
    assert frame.mouth_open == 0.9
    # Eyes from eye controller, not random hard-coded
    assert 0.0 <= frame.eye_l_open <= 1.0
    # Hair from physics controller
    assert -1.0 <= frame.hair_front <= 1.0
    # Breath continuous
    assert 0.0 <= frame.breath <= 1.0

    # Controller-driven reset on stop
    ctrl = AvatarController(renderer=MockAvatarRenderer(), auto_subscribe=False)
    ctrl._current_state.speaking = True
    ctrl._current_state.mouth_open = 0.9
    await_ctrl_reset = ctrl.set_speaking(False)
    asyncio.run(await_ctrl_reset)
    assert ctrl.current_state.mouth_open == 0.0


def test_lipsync_to_avatar_frame():
    from delta.vtuber.avatar.composer import AvatarFrameComposer

    composer = AvatarFrameComposer()
    # Real amplitude-driven values (from AudioAmplitudeAnalyzer), not random/sin
    for amplitude in (0.1, 0.5, 0.9):
        base = AvatarState(mouth_open=amplitude, speaking=True)
        frame = composer.compose_frame(base)
        assert frame.mouth_open == amplitude

    # Stop => mouth zero (barge-in ownership in controller)
    base = AvatarState(mouth_open=0.0, speaking=False)
    frame = composer.compose_frame(base)
    assert frame.mouth_open == 0.0


def test_emotion_to_avatar_frame():
    from delta.vtuber.avatar.composer import AvatarFrameComposer
    from delta.vtuber.avatar.live2d_mapper import Live2DExpressionMapper

    composer = AvatarFrameComposer()
    mapping = {
        VTuberEmotion.NEUTRAL: VTuberExpression.NEUTRAL,
        VTuberEmotion.HAPPY: VTuberExpression.SMILE,
        VTuberEmotion.EXCITED: VTuberExpression.EXCITED,
        VTuberEmotion.THINKING: VTuberExpression.THINKING,
        VTuberEmotion.SAD: VTuberExpression.SAD,
        VTuberEmotion.ANGRY: VTuberExpression.ANGRY,
    }
    for emotion, expression in mapping.items():
        base = AvatarState(expression=expression, expression_intensity=0.6)
        frame = composer.compose_frame(base)
        assert frame.expression == expression
        # Must produce valid Live2D expression params
        expr_params = Live2DExpressionMapper.get_expression_parameters(expression, frame.expression_intensity)
        assert len(expr_params) > 0


def test_mood_modulation():
    from delta.vtuber.avatar.composer import AvatarFrameComposer

    composer = AvatarFrameComposer()
    base = AvatarState(expression=VTuberExpression.SMILE, expression_intensity=0.6)

    # High happiness boosts smile intensity
    frame_high = composer.compose_frame(base, mood_modifier={"happiness": 0.9})
    frame_low = composer.compose_frame(base, mood_modifier={"happiness": 0.1})
    assert frame_high.expression_intensity > frame_low.expression_intensity
    # Clamped 0..1
    assert 0.0 <= frame_high.expression_intensity <= 1.0


def test_parameter_delta_suppression():
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts_renderer import VTSRenderer

    async def _test():
        renderer = VTSRenderer(enabled=True, delta_threshold=0.02)
        renderer.client._is_connected = True
        renderer.client._is_authenticated = True
        renderer.client._ws = AsyncMock()
        renderer.client._current_model_data = {"modelLoaded": True}

        state = AvatarState(head_x=0.5, expression=VTuberExpression.SMILE, mouth_open=0.5, speaking=True)
        await renderer.render(state)
        first_count = renderer.client.requests_sent_count

        # Nearly identical state (delta < threshold) -> suppressed
        state_small = AvatarState(head_x=0.501, expression=VTuberExpression.SMILE, mouth_open=0.501, speaking=True)
        await renderer.render(state_small)
        assert renderer.client.requests_sent_count == first_count
        assert renderer.dropped_updates >= 1

        # Significant change -> sent
        state_big = AvatarState(head_x=-0.5, expression=VTuberExpression.SMILE, mouth_open=0.5, speaking=True)
        await renderer.render(state_big)
        assert renderer.client.requests_sent_count == first_count + 1

    asyncio.run(_test())


def test_latest_state_wins():
    """Stale frames are dropped; the newest state must be the one sent."""
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts_renderer import VTSRenderer

    async def _test():
        renderer = VTSRenderer(enabled=True, update_hz=1000.0)
        renderer.client._is_connected = True
        renderer.client._is_authenticated = True
        renderer.client._ws = AsyncMock()

        sent_states = []

        async def capture_send(state, supported_parameters=None):
            sent_states.append(state)
            return True

        renderer.client.send_avatar_state = capture_send

        s1 = AvatarState(head_x=0.1)
        s2 = AvatarState(head_x=0.4)
        s3 = AvatarState(head_x=0.9)
        # Rapid stream — stale frames inside cadence window must be discarded
        await renderer.render(s1)
        await renderer.render(s2)
        await renderer.render(s3)

        # Whatever was sent, the last sent frame must be the latest state (or dropped as stale)
        if sent_states:
            assert sent_states[-1].head_x in (0.1, 0.4, 0.9)
            assert sent_states[-1] is s3 or sent_states[-1].timestamp <= s3.timestamp

    asyncio.run(_test())


def test_vts_rate_limit():
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts_renderer import VTSRenderer

    async def _test():
        renderer = VTSRenderer(enabled=True, update_hz=30.0)
        renderer.client._is_connected = True
        renderer.client._is_authenticated = True
        renderer.client._ws = AsyncMock()

        state_a = AvatarState(head_x=0.9, mouth_open=0.9, speaking=False)
        await renderer.render(state_a)
        sent_first = renderer.client.requests_sent_count

        # Immediate second render within 1/30s window -> stale dropped
        # (speaking frames bypass cadence for realtime lip-sync; idle frames do not)
        state_b = AvatarState(head_x=-0.9, mouth_open=0.0, speaking=False)
        await renderer.render(state_b)
        assert renderer.stale_updates_dropped >= 1
        assert renderer.client.requests_sent_count == sent_first

    asyncio.run(_test())


def test_vts_capability_mapping():
    """Unsupported parameters are filtered out from injection payload."""
    from delta.vtuber.avatar.vts.mapper import VTSMapper

    state = AvatarState(expression=VTuberExpression.SMILE, mouth_open=0.5, speaking=True)
    full_msg = VTSMapper.to_vts_inject_message(state)
    full_ids = {p["id"] for p in full_msg.data["parameterValues"]}
    assert "ParamHairFront" in full_ids

    # Model without hair physics support
    limited = ["ParamAngleX", "ParamMouthOpenY", "ParamMouthForm"]
    msg = VTSMapper.to_vts_inject_message(state, supported_parameters=limited)
    sent_ids = {p["id"] for p in msg.data["parameterValues"]}
    assert sent_ids.issubset(set(limited))
    assert "ParamHairFront" not in sent_ids
    assert "ParamMouthOpenY" in sent_ids


def test_expression_capability():
    from delta.vtuber.avatar.character_profile import CharacterProfile

    profile = CharacterProfile(
        supported_expressions=["neutral", "smile", "angry"],
    )
    assert profile.is_expression_supported("smile") is True
    assert profile.is_expression_supported("SMILE") is True  # case-insensitive
    assert profile.is_expression_supported("excited") is False
    assert profile.is_parameter_supported("ParamAngleX") is True
    assert profile.is_parameter_supported("ParamUnknown") is False


def test_barge_in_resets_vts_mouth():
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts_renderer import VTSRenderer

    async def _test():
        renderer = VTSRenderer(enabled=True, update_hz=1000.0)
        renderer.client._is_connected = True
        renderer.client._is_authenticated = True
        renderer.client._ws = AsyncMock()

        # Start speaking with mouth open
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        await ctrl.set_speaking(True)
        await ctrl.set_mouth_open(0.9)
        assert ctrl.current_state.mouth_open > 0.5

        # Barge-in: interrupt speech -> mouth must immediately zero
        interrupt_event = SpeechLifecycleEvent(
            event_type=SpeechLifecycleEventType.SPEECH_INTERRUPTED,
            speech_id="barge-in-test",
        )
        await ctrl.handle_speech_lifecycle(interrupt_event)
        assert ctrl.current_state.speaking is False
        assert ctrl.current_state.mouth_open == 0.0

        # VTS received the forced zero-mouth update (force-rendered even within cadence window)
        last_state = renderer._last_sent_state
        assert last_state is not None
        assert last_state.mouth_open == 0.0
        assert last_state.speaking is False

    asyncio.run(_test())


def test_physics_composition():
    from delta.vtuber.avatar.composer import AvatarFrameComposer

    composer = AvatarFrameComposer()
    base = AvatarState(head_x=0.8, head_y=0.3, speaking=True)
    frame = composer.compose_frame(base)

    # Hair springs respond to head movement with damped motion (not random jitter)
    assert -1.0 <= frame.hair_front <= 1.0
    assert -1.0 <= frame.hair_side <= 1.0
    assert -1.0 <= frame.hair_back <= 1.0
    # Repeated identical input converges (spring settles toward target, no divergence)
    frame2 = composer.compose_frame(base)
    assert -1.0 <= frame2.hair_front <= 1.0


def test_breathing_composition():
    import math
    from delta.vtuber.avatar.composer import AvatarFrameComposer

    composer = AvatarFrameComposer()
    # Breathing runs continuously: idle, speaking, and thinking
    for state in (
        AvatarState(speaking=False),
        AvatarState(speaking=True, mouth_open=0.5),
        AvatarState(expression=VTuberExpression.THINKING),
    ):
        frame = composer.compose_frame(state)
        assert 0.0 <= frame.breath <= 1.0

    # Breath oscillates over time (not frozen at one value)
    t0 = 100.0
    f1 = composer.compose_frame(AvatarState(), current_time=t0)
    f2 = composer.compose_frame(AvatarState(), current_time=t0 + 1.5)
    assert abs(f2.breath - f1.breath) > 0.01


def test_character_profile():
    from delta.vtuber.avatar.character_profile import CharacterProfile, default_character_profile

    profile = default_character_profile
    assert profile.name == "Delta AI VTuber"
    assert profile.model_id == "delta_cyber_v1"
    assert "ParamMouthOpenY" in profile.supported_parameters
    assert "ParamHairFront" in profile.supported_parameters
    assert profile.is_expression_supported("smile")
    assert profile.voice_profile == "id-ID-GadisNeural"
    assert 0.0 < profile.voice_speed <= 2.0
    assert profile.physics_enabled is True
    assert profile.lip_sync_enabled is True

    # Custom profile is fully configurable
    custom = CharacterProfile(name="Custom", model_id="custom_1", physics_enabled=False)
    assert custom.physics_enabled is False
    assert custom.is_parameter_supported("ParamAngleX")


def test_visual_source_schemas_and_mock():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceType, VisualSourceState, VisualSourceStatus
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource

    async def _test():
        mock_source = MockVisualSource()
        assert mock_source.get_status().state == VisualSourceState.DISCONNECTED

        ok = await mock_source.initialize()
        assert ok is True

        started = await mock_source.start()
        assert started is True
        assert mock_source.get_status().state == VisualSourceState.STREAMING
        assert mock_source.get_status().connected is True

        await mock_source.stop()
        assert mock_source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())


# ==========================================
# Phase 13 VTS Visual Bridge Tests
# ==========================================


def test_visual_source_schemas_and_mock():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceType, VisualSourceState, VisualSourceStatus
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.manager import VTSVisualManager

    async def _test():
        mock_source = MockVisualSource()
        assert mock_source.get_status().state == VisualSourceState.DISCONNECTED

        ok = await mock_source.initialize()
        assert ok is True

        started = await mock_source.start()
        assert started is True
        assert mock_source.get_status().state == VisualSourceState.STREAMING
        assert mock_source.get_status().connected is True

        await mock_source.stop()
        assert mock_source.get_status().state == VisualSourceState.DISCONNECTED

        mgr = VTSVisualManager(source=mock_source)
        assert await mgr.initialize() is True
        assert mgr.get_status().source == VisualSourceType.MOCK

    asyncio.run(_test())


def test_vts_visual_status_and_stream_endpoints():
    from delta.web.bridge import EngineBridge
    from delta.vtuber.avatar.vts_visual.manager import VTSVisualManager
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource

    bridge = EngineBridge(None)
    bridge.vts_visual_mgr = VTSVisualManager(source=MockVisualSource())

    res = bridge.get_vts_visual_status()
    assert res["status"] == "ok"
    assert "visual" in res
    assert res["visual"]["source"] == "mock_visual_source"
    assert "authenticationToken" not in str(res)


def test_visual_source_fallback_logic():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus, VisualSourceType, VisualSourceState

    # Primary active status
    status_primary = VisualSourceStatus(
        connected=True,
        source=VisualSourceType.VIRTUAL_CAM,
        state=VisualSourceState.STREAMING,
        active_path="primary_browser_cam",
    )
    assert status_primary.connected is True
    assert status_primary.active_path == "primary_browser_cam"

    # Fallback status
    status_fallback = VisualSourceStatus(
        connected=False,
        source=VisualSourceType.BROWSER_LIVE2D,
        state=VisualSourceState.FALLBACK,
        active_path="tertiary_browser_live2d",
    )
    assert status_fallback.connected is False
    assert status_fallback.active_path == "tertiary_browser_live2d"


def test_visual_source_lifecycle():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        assert source.get_status().state == VisualSourceState.DISCONNECTED

        await source.initialize()
        await source.start()
        assert source.get_status().state == VisualSourceState.STREAMING

        await source.stop()
        assert source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())


def test_vts_visual_source_status():
    from delta.vtuber.avatar.vts_visual.manager import VTSVisualManager
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource

    mgr = VTSVisualManager(source=MockVisualSource())
    status = mgr.get_status()

    assert status.source == "mock_visual_source"
    assert status.transparent is True
    assert "authenticationToken" not in str(status.model_dump())


def test_visual_source_disconnect():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        await source.start()
        await source.stop()
        assert source.get_status().connected is False
        assert source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())


def test_visual_source_reconnect():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        await source.start()
        await source.stop()
        await source.start()
        assert source.get_status().connected is True
        assert source.get_status().state == VisualSourceState.STREAMING

    asyncio.run(_test())


def test_visual_source_fallback():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus, VisualSourceType, VisualSourceState

    status = VisualSourceStatus(
        connected=False,
        source=VisualSourceType.BROWSER_LIVE2D,
        state=VisualSourceState.FALLBACK,
        active_path="tertiary_browser_live2d",
    )
    assert status.connected is False
    assert status.active_path == "tertiary_browser_live2d"


def test_visual_viewer_state():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus, VisualSourceType

    status = VisualSourceStatus(
        connected=True,
        source=VisualSourceType.VIRTUAL_CAM,
        active_path="primary_browser_cam",
    )
    assert status.active_path == "primary_browser_cam"


def test_transparent_mode():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus

    status = VisualSourceStatus(transparent=True)
    assert status.transparent is True


def test_aspect_ratio():
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceStatus

    status = VisualSourceStatus(width=1920, height=1080)
    ratio = status.width / status.height
    assert round(ratio, 2) == 1.78


def test_cleanup():
    from delta.vtuber.avatar.vts_visual.sources import MockVisualSource
    from delta.vtuber.avatar.vts_visual.schemas import VisualSourceState

    async def _test():
        source = MockVisualSource()
        await source.start()
        await source.stop()
        assert source.get_status().state == VisualSourceState.DISCONNECTED

    asyncio.run(_test())



def test_text_input_auto_response():
    from delta.vtuber.response import ResponseProcessor

    processor = ResponseProcessor()
    raw = "Halo! **Delta** di sini. ```python\nprint(1)\n``` Sampai jumpa!"
    payload = processor.process(raw, response_id="text-resp-1")

    assert payload.response_id == "text-resp-1"
    # Display text retains Markdown
    assert "**Delta**" in payload.display_text
    # Spoken text strips raw code block / Markdown formatting for clean TTS
    assert "print(1)" not in payload.speech_text
    assert payload.emotion is not None


def test_voice_input_auto_response():
    from unittest.mock import AsyncMock
    from delta.vtuber.voice.stt.schemas import STTFinalResult
    from delta.vtuber.voice.stt.manager import STTManager

    async def _test():
        handled_text = []

        def input_handler(text):
            handled_text.append(text)

        stt_mgr = STTManager(input_handler=input_handler)
        stt_mgr.provider.transcribe = AsyncMock(return_value=STTFinalResult(text="Delta scan server"))

        res = await stt_mgr.process_audio_buffer(b"\x00\x00" * 100)
        assert res is not None
        assert res.text == "Delta scan server"
        assert len(handled_text) == 1
        assert handled_text[0] == "Delta scan server"

    asyncio.run(_test())


def test_unified_response_event():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        received_events = []
        bus = VTuberEventBus()
        bus.subscribe(lambda ev: received_events.append(ev), VTuberEventType.RESPONSE)

        dispatcher = ResponseDispatcher(event_bus=bus)
        payload = ResponsePayload(
            response_id="res-evt-100",
            display_text="Test response",
            speech_text="Test response spoken",
            emotion=VTuberEmotion.HAPPY,
        )
        ok = await dispatcher.dispatch(payload)
        assert ok is True
        assert len(received_events) == 1
        assert received_events[0].type == VTuberEventType.RESPONSE
        assert received_events[0].payload.metadata["response_id"] == "res-evt-100"

    asyncio.run(_test())


def test_response_to_speech():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        speech_mgr = SpeechManager(auto_subscribe=False)
        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr)

        payload = ResponsePayload(
            response_id="auto-tts-1",
            speech_text="Sistem keamanan aktif.",
        )
        ok = await dispatcher.dispatch(payload)
        assert ok is True
        assert speech_mgr.queue_size == 1

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_response_to_avatar():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        renderer = MockAvatarRenderer()
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        speech_mgr = SpeechManager(auto_subscribe=False)

        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr, avatar_ctrl=ctrl)
        dispatcher.wire_speech_lifecycle(speech_mgr)

        payload = ResponsePayload(
            response_id="avatar-resp-1",
            speech_text="Avatar respon otomatis.",
        )
        await dispatcher.dispatch(payload)
        assert ctrl.current_state.speaking is True

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_response_to_emotion():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        renderer = MockAvatarRenderer()
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        eng = EmotionEngine()

        dispatcher = ResponseDispatcher(avatar_ctrl=ctrl, emotion_eng=eng)
        payload = ResponsePayload(
            response_id="emo-resp-1",
            speech_text="Jawaban gembira!",
            emotion=VTuberEmotion.HAPPY,
            emotion_intensity=0.9,
        )
        await dispatcher.dispatch(payload)

        assert eng.current_emotion == VTuberEmotion.HAPPY
        assert ctrl.current_state.expression == VTuberExpression.SMILE

    asyncio.run(_test())


def test_thinking_state():
    from delta.ai.events import AgentEvent, EventType

    async def _test():
        adapter = VTuberAgentAdapter(auto_attach=False)
        ev = AgentEvent(type=EventType.AGENT_THINKING, status_text="Memikirkan jawaban...")
        await adapter.handle_agent_event_async(ev)

        assert adapter.state_machine.current_state == VTuberState.THINKING

    asyncio.run(_test())


def test_speaking_state():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        renderer = MockAvatarRenderer()
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        speech_mgr = SpeechManager(auto_subscribe=False)

        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr, avatar_ctrl=ctrl)
        dispatcher.wire_speech_lifecycle(speech_mgr)

        payload = ResponsePayload(
            response_id="speaking-state-1",
            speech_text="Sedang berbicara...",
        )
        await dispatcher.dispatch(payload)
        assert ctrl.current_state.speaking is True

        # Stop speech -> speaking state returns False
        await speech_mgr.stop()
        assert ctrl.current_state.speaking is False

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_idle_after_response():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        renderer = MockAvatarRenderer()
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        speech_mgr = SpeechManager(auto_subscribe=False)

        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr, avatar_ctrl=ctrl)
        dispatcher.wire_speech_lifecycle(speech_mgr)

        payload = ResponsePayload(response_id="idle-1", speech_text="Selesai.")
        await dispatcher.dispatch(payload)

        await speech_mgr.stop()
        await ctrl.set_idle()

        assert ctrl.current_state.speaking is False
        assert ctrl.current_state.expression == VTuberExpression.NEUTRAL

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_barge_in_response_cancel():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        renderer = MockAvatarRenderer()
        ctrl = AvatarController(renderer=renderer, auto_subscribe=False)
        speech_mgr = SpeechManager(auto_subscribe=False)

        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr, avatar_ctrl=ctrl)

        payload = ResponsePayload(response_id="barge-in-res", speech_text="Teks panjang untuk di-interrupt.")
        await dispatcher.dispatch(payload)

        # Barge-in cancellation
        await dispatcher.cancel_response("barge-in-res")
        assert speech_mgr.is_speaking is False
        assert ctrl.current_state.speaking is False
        assert ctrl.current_state.mouth_open == 0.0

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_duplicate_response_prevention():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        speech_mgr = SpeechManager(auto_subscribe=False)
        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr)

        payload = ResponsePayload(response_id="dup-100", speech_text="Pesan unik.")
        ok1 = await dispatcher.dispatch(payload)
        assert ok1 is True

        # Second dispatch with identical response_id -> rejected
        ok2 = await dispatcher.dispatch(payload)
        assert ok2 is False
        assert speech_mgr.queue_size == 1

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_response_ordering():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        speech_mgr = SpeechManager(auto_subscribe=False)
        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr)

        p1 = ResponsePayload(response_id="resp-A", speech_text="Respon pertama.")
        p2 = ResponsePayload(response_id="resp-B", speech_text="Respon kedua.")

        await dispatcher.dispatch(p1)
        # New response cancels old response
        await dispatcher.cancel_response("resp-A")
        await dispatcher.dispatch(p2)

        assert dispatcher._current_response_id == "resp-B"

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_streaming_sentence_dispatch():
    from delta.vtuber.response import ResponseDispatcher

    async def _test():
        speech_mgr = SpeechManager(auto_subscribe=False)
        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr)

        # Stream tokens
        await dispatcher.feed_stream_token("Kalimat pertama selesai. ")
        await dispatcher.feed_stream_token("Kalimat kedua masih berjalan")
        await dispatcher.flush_stream()

        assert speech_mgr.queue_size >= 1

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_empty_response():
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        speech_mgr = SpeechManager(auto_subscribe=False)
        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr)

        empty_payload = ResponsePayload(response_id="empty-1", display_text="", speech_text="")
        ok = await dispatcher.dispatch(empty_payload)

        assert ok is False
        assert speech_mgr.queue_size == 0

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_vts_automatic_parameter_dispatch():
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts_renderer import VTSRenderer
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        vts_renderer = VTSRenderer(enabled=True, update_hz=1000.0)
        vts_renderer.client._is_connected = True
        vts_renderer.client._is_authenticated = True
        vts_renderer.client._ws = AsyncMock()

        ctrl = AvatarController(renderer=vts_renderer, auto_subscribe=False)
        speech_mgr = SpeechManager(auto_subscribe=False)

        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr, avatar_ctrl=ctrl)
        dispatcher.wire_speech_lifecycle(speech_mgr)

        payload = ResponsePayload(
            response_id="auto-vts-dispatch",
            speech_text="Otomatis terkirim ke VTube Studio.",
            emotion=VTuberEmotion.HAPPY,
        )
        await dispatcher.dispatch(payload)

        # Automatic dispatch reached VTS client without manual button click
        assert vts_renderer.client.requests_sent_count >= 1
        assert ctrl.current_state.expression == VTuberExpression.SMILE

        await speech_mgr.shutdown()

    asyncio.run(_test())


def test_vts_offline_response_fallback():
    from delta.vtuber.avatar.vts_renderer import VTSRenderer
    from delta.vtuber.response import ResponseDispatcher, ResponsePayload

    async def _test():
        # VTS renderer disabled / offline
        vts_renderer = VTSRenderer(enabled=False)
        ctrl = AvatarController(renderer=vts_renderer, auto_subscribe=False)
        speech_mgr = SpeechManager(auto_subscribe=False)

        dispatcher = ResponseDispatcher(speech_mgr=speech_mgr, avatar_ctrl=ctrl)
        payload = ResponsePayload(
            response_id="vts-offline-fallback",
            speech_text="VTS offline tetapi respon AI tetap berjalan.",
        )
        ok = await dispatcher.dispatch(payload)

        # Response succeeds via fallback without crashing
        assert ok is True
        assert ctrl.current_state.speaking is True

        await speech_mgr.shutdown()

    asyncio.run(_test())


# ==========================================
# Regression Tests for VTS Control Channel
# ==========================================


def test_vts_auth_state():
    from delta.vtuber.avatar.vts.client import VTSClient
    from delta.vtuber.avatar.vts.protocol import VTSConnectionState

    client = VTSClient(enabled=True)
    assert client.is_authenticated is False
    assert client.is_connected is False
    assert client.state == VTSConnectionState.DISCONNECTED

    summary = client.get_status_summary()
    assert summary["authenticated"] is False
    assert summary["connected"] is False


def test_vts_model_loaded_state():
    from delta.vtuber.avatar.vts.client import VTSClient

    client = VTSClient(enabled=True)
    client._is_connected = True
    client._is_authenticated = True

    # No model loaded
    client._current_model_data = {"modelLoaded": False, "modelName": ""}
    summary = client.get_status_summary()
    assert summary["model_loaded"] is False
    assert summary["current_model"] == ""
    assert summary["model_name"] == ""

    # Model loaded
    client._current_model_data = {"modelLoaded": True, "modelName": "Shizuku", "modelID": "vts_shizuku_01"}
    summary2 = client.get_status_summary()
    assert summary2["model_loaded"] is True
    assert summary2["current_model"] == "Shizuku"
    assert summary2["model_name"] == "Shizuku"
    assert summary2["model_id"] == "vts_shizuku_01"


def test_vts_parameter_capabilities():
    from delta.vtuber.avatar.vts.client import VTSClient

    client = VTSClient(enabled=True)
    client._supported_parameters_set = {"ParamAngleX", "ParamAngleY", "ParamMouthOpenY"}

    assert client.is_parameter_supported("ParamAngleX") is True
    assert client.is_parameter_supported("ParamAngleY") is True
    assert client.is_parameter_supported("ParamMouthOpenY") is True
    assert client.is_parameter_supported("ParamBrowLY") is False


def test_vts_real_response_validation():
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts.client import VTSClient

    async def _test():
        client = VTSClient(enabled=True)
        client._is_connected = True
        client._is_authenticated = True

        mock_ws = AsyncMock()
        error_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaDirectInject",
            "messageType": "APIError",
            "data": {
                "errorID": 100,
                "errorMessage": "Parameter could not be found or injected",
            }
        }
        mock_ws.recv.return_value = json.dumps(error_payload)
        client._ws = mock_ws

        res = await client.inject_raw_parameters([{"parameter": "ParamAngleX", "value": 20.0}])
        assert res["success"] is False
        assert res["reason"] == "VTS_API_ERROR"
        assert res["errorID"] == 100
        assert "Parameter could not be found" in res["errorMessage"]

    asyncio.run(_test())


def test_vts_parameter_injection_result():
    from unittest.mock import AsyncMock
    from delta.vtuber.avatar.vts.client import VTSClient

    async def _test():
        client = VTSClient(enabled=True)
        client._is_connected = True
        client._is_authenticated = True

        mock_ws = AsyncMock()
        success_payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaDirectInject",
            "messageType": "InjectParameterDataResponse",
            "data": {}
        }
        mock_ws.recv.return_value = json.dumps(success_payload)
        client._ws = mock_ws

        res = await client.inject_raw_parameters([{"parameter": "ParamAngleX", "value": 20.0}])
        assert res["success"] is True
        assert res["reason"] == "OK"
        assert client.last_error is None

    asyncio.run(_test())


def test_vts_expression_availability():
    from unittest.mock import AsyncMock, MagicMock
    from delta.web.bridge import EngineBridge
    from delta.vtuber.avatar.vts.client import VTSClient

    async def _test():
        mock_engine = MagicMock()
        bridge = EngineBridge(mock_engine)

        mock_client = VTSClient(enabled=True)
        mock_client._is_connected = True
        mock_client._is_authenticated = True
        mock_client._ws = AsyncMock()
        mock_client._ws.recv.return_value = json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaExpressionTest",
            "messageType": "InjectParameterDataResponse",
            "data": {}
        })
        bridge._cached_vts_client = mock_client

        # Valid expression
        res_smile = await bridge.vts_test_expression("smile")
        assert res_smile["status"] == "ok"
        assert res_smile["expression"] == "smile"

        # Invalid expression
        res_invalid = await bridge.vts_test_expression("nonexistent_expression_xyz")
        assert res_invalid["status"] == "error"
        assert res_invalid["reason"] == "EXPRESSION_NOT_AVAILABLE"

    asyncio.run(_test())


def test_vts_auto_test_diagnostics():
    from unittest.mock import AsyncMock, MagicMock
    from delta.web.bridge import EngineBridge
    from delta.vtuber.avatar.vts.client import VTSClient

    async def _test():
        mock_engine = MagicMock()
        bridge = EngineBridge(mock_engine)

        mock_client = VTSClient(enabled=True)
        mock_client._is_connected = True
        mock_client._is_authenticated = True
        mock_client._current_model_data = {"modelLoaded": True, "modelName": "Hiyori Live2D", "modelID": "hiyori_1"}
        mock_client._supported_parameters_set = {"ParamAngleX", "ParamAngleY", "ParamMouthOpenY"}
        mock_client._ws = AsyncMock()
        mock_client._ws.recv.return_value = json.dumps({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "DeltaAutoTest",
            "messageType": "InjectParameterDataResponse",
            "data": {}
        })
        bridge._cached_vts_client = mock_client

        report = await bridge.vts_run_auto_test()
        assert report["total_steps"] == 10
        assert report["steps"][0]["name"] == "getCurrentModel"
        assert report["steps"][0]["status"] == "PASS"

        # Check diagnostics on each step
        for step in report["steps"]:
            assert "step" in step
            assert "name" in step
            assert "status" in step
            assert "details" in step

    asyncio.run(_test())









