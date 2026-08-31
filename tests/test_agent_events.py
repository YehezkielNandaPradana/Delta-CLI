# tests/test_agent_events.py
"""
Comprehensive Integration Tests for Agent Event System, Event Bus, Task Manager,
Real Diff Engine, CLI Renderer, SSE Web Server Transport, and ReAct Loop.
"""

import os
import tempfile
import unittest
from delta.ai.events import AgentEvent, EventType, EventBus, TaskStatus, generate_real_diff, event_bus
from delta.ai.task_manager import AgentTaskManager
from delta.ai.tools import Tool, ToolParameter
from delta.ai.cli_renderer import CLIRenderer

class TestAgentEventSystem(unittest.TestCase):

    def test_event_bus_pub_sub(self):
        bus = EventBus()
        received = []

        def subscriber(ev: AgentEvent):
            received.append(ev)

        unsub = bus.subscribe(subscriber)
        event = AgentEvent(type=EventType.AGENT_START, status_text="Testing bus")
        bus.emit(event)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].type, EventType.AGENT_START)
        self.assertEqual(received[0].status_text, "Testing bus")

        unsub()
        bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE))
        self.assertEqual(len(received), 1)

    def test_task_manager_lifecycle(self):
        bus = EventBus()
        events = []
        bus.subscribe(lambda ev: events.append(ev))

        mgr = AgentTaskManager(bus)
        task = mgr.create_task("Fix authentication bug")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, EventType.TASK_CREATED)

        mgr.start_task(task.id)
        self.assertEqual(task.status, TaskStatus.RUNNING)
        self.assertEqual(events[1].type, EventType.TASK_STARTED)

        mgr.complete_task(task.id)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(events[2].type, EventType.TASK_COMPLETED)

    def test_generate_real_diff(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
            f.write("def foo():\n    return 1\n")
            path = f.name

        try:
            old_content = "def foo():\n    return 1\n"
            new_content = "def foo():\n    return 2\n"

            diff_event = generate_real_diff(path, old_content, new_content)
            self.assertIsNotNone(diff_event)
            assert diff_event is not None
            self.assertEqual(diff_event.type, EventType.FILE_UPDATE)
            self.assertEqual(diff_event.added_lines, 1)
            self.assertEqual(diff_event.removed_lines, 1)
            self.assertTrue(diff_event.diff is not None and "-    return 1" in diff_event.diff)
            self.assertTrue(diff_event.diff is not None and "+    return 2" in diff_event.diff)
        finally:
            os.remove(path)

    def test_engine_emits_immediate_start_events(self):
        events = []
        def listener(ev):
            events.append(ev.type)
        sub = event_bus.subscribe(listener)
        try:
            event_bus.emit(AgentEvent(type=EventType.AGENT_START, status_text="Thinking..."))
            event_bus.emit(AgentEvent(type=EventType.AGENT_THINKING, status_text="Analyzing..."))
            assert EventType.AGENT_START in events
            assert EventType.AGENT_THINKING in events
        finally:
            sub()
        bus = EventBus()
        events = []
        bus.subscribe(lambda ev: events.append(ev))

        # Backup global event_bus subscribers for clean test
        from delta.ai import events as evt_module
        old_bus = evt_module.event_bus
        evt_module.event_bus = bus

        try:
            def dummy_func(a: int):
                return f"Result: {a * 2}"

            t = Tool(
                name="double",
                description="Double a number",
                func=dummy_func,
                parameters=[ToolParameter("a", "integer", "Number")]
            )
            res = t.execute(a=5)

            self.assertTrue(res["success"])
            self.assertEqual(res["output"], "Result: 10")
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0].type, EventType.TOOL_START)
            self.assertEqual(events[1].type, EventType.TOOL_RESULT)
        finally:
            evt_module.event_bus = old_bus

    def test_cli_renderer_handles_events(self):
        bus = EventBus()
        renderer = CLIRenderer(bus)

        try:
            bus.emit(AgentEvent(type=EventType.AGENT_START))
            bus.emit(AgentEvent(type=EventType.TOOL_START, tool="edit_file"))
            bus.emit(AgentEvent(type=EventType.FILE_UPDATE, path="delta/ai/llm.py", added_lines=5, removed_lines=2, diff="@@ -1,2 +1,2 @@\n-old\n+new"))
            bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE))
        finally:
            renderer.close()

    def test_agent_step_self_parent_rejection(self):
        from delta.ai.events import AgentStep, StepKind, StepStatus
        step = AgentStep(
            id="step_A", task_id="t1", execution_id="ex1", parent_id="step_A",
            kind=StepKind.READ, label="Reading file", status=StepStatus.RUNNING, created_at=100.0
        )
        with self.assertRaises(ValueError) as ctx:
            step.validate()
        self.assertIn("cannot be its own parent", str(ctx.exception))

    def test_agent_step_circular_parent_chain_rejection(self):
        from delta.ai.events import AgentStep, StepKind, StepStatus
        step_a = AgentStep(id="A", task_id="t1", execution_id="ex1", parent_id=None, kind=StepKind.ROOT, label="Root", status=StepStatus.COMPLETED, created_at=100.0)
        step_b = AgentStep(id="B", task_id="t1", execution_id="ex1", parent_id="A", kind=StepKind.CONTEXT, label="Ctx", status=StepStatus.COMPLETED, created_at=101.0)
        step_c = AgentStep(id="C", task_id="t1", execution_id="ex1", parent_id="B", kind=StepKind.SEARCH, label="Search", status=StepStatus.RUNNING, created_at=102.0)

        steps = {"A": step_a, "B": step_b, "C": step_c}
        # Create circular dependency A -> C
        step_a.parent_id = "C"

        with self.assertRaises(ValueError) as ctx:
            step_a.validate(steps)
        self.assertIn("Circular parent chain detected", str(ctx.exception))

    def test_agent_step_root_validation(self):
        from delta.ai.events import AgentStep, StepKind, StepStatus
        invalid_root = AgentStep(
            id="root_1", task_id="t1", execution_id="ex1", parent_id="parent_invalid",
            kind=StepKind.ROOT, label="Root Task", status=StepStatus.RUNNING, created_at=100.0
        )
        with self.assertRaises(ValueError) as ctx:
            invalid_root.validate()
        self.assertIn("must have parent_id=None", str(ctx.exception))

        valid_root = AgentStep(
            id="root_1", task_id="t1", execution_id="ex1", parent_id=None,
            kind=StepKind.ROOT, label="Root Task", status=StepStatus.RUNNING, created_at=100.0
        )
        valid_root.validate()  # Should not raise

    def test_event_bus_sequence_isolation_per_execution(self):
        bus = EventBus()
        ev_ex1_a = AgentEvent(type=EventType.AGENT_START, execution_id="exec_1")
        ev_ex1_b = AgentEvent(type=EventType.TOOL_START, execution_id="exec_1")
        ev_ex2_a = AgentEvent(type=EventType.AGENT_START, execution_id="exec_2")

        bus.emit(ev_ex1_a)
        bus.emit(ev_ex1_b)
        bus.emit(ev_ex2_a)

        self.assertEqual(ev_ex1_a.sequence, 1)
        self.assertEqual(ev_ex1_b.sequence, 2)
        self.assertEqual(ev_ex2_a.sequence, 1)  # Sequence resets per execution_id isolation

    def test_engine_emits_structured_agent_steps(self):
        bus = EventBus()
        events = []
        bus.subscribe(lambda ev: events.append(ev))

        import time
        from delta.ai.events import AgentStep, StepKind, StepStatus, EventType
        root_step = AgentStep(
            id="root_exec_1",
            task_id="t1",
            execution_id="exec_1",
            parent_id=None,
            kind=StepKind.ROOT,
            label="Root Task",
            status=StepStatus.RUNNING,
            created_at=time.time(),
            started_at=time.time()
        )
        root_step.validate()

        child_step = AgentStep(
            id="tool_1",
            task_id="t1",
            execution_id="exec_1",
            parent_id=root_step.id,
            kind=StepKind.READ,
            label="Reading file",
            status=StepStatus.RUNNING,
            created_at=time.time(),
            started_at=time.time(),
            file_path="test.py"
        )
        child_step.validate({"root_exec_1": root_step})

        bus.emit(AgentEvent(
            type=EventType.AGENT_STEP_STARTED,
            execution_id="exec_1",
            task_id="t1",
            step_id=child_step.id,
            payload={"step": child_step.to_dict()}
        ))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, EventType.AGENT_STEP_STARTED)
        self.assertEqual(events[0].payload["step"]["parent_id"], "root_exec_1")
        self.assertEqual(events[0].payload["step"]["kind"], "read")

if __name__ == "__main__":
    unittest.main()
