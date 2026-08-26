# Refactor: react loop
# delta/ai/react_loop.py
"""
ReAct Agentic Loop Engine for Delta AI Coding Agent.
Orchestrates User Request -> Analyze -> Plan -> Select Tool -> Execute Tool -> Observe -> Update Task -> Verify -> Complete.
Emits real-time AgentEvents to EventBus for CLI & Web UI.
"""

import time
import json
from typing import Any, Optional
from delta.ai.events import AgentEvent, EventType, EventBus, event_bus
from delta.ai.task_manager import AgentTaskManager
from delta.ai.tools import ToolRegistry, parse_xml_tool_calls, parse_json_tool_calls

class ReActAgentEngine:
    """ReAct Execution Loop for Delta AI Coding Agent."""

    def __init__(self, llm_engine: Any, tool_registry: ToolRegistry, bus: Optional[EventBus] = None):
        self.llm = llm_engine
        self.tools = tool_registry
        self.bus = bus or event_bus
        self.task_manager = AgentTaskManager(self.bus)
        self.max_steps = 15

    def run(self, user_request: str) -> str:
        self.bus.emit(AgentEvent(type=EventType.AGENT_START, status_text="Analyzing user request..."))

        # Step 1: Initial planning phase
        self.bus.emit(AgentEvent(type=EventType.AGENT_STATUS, status_text="Formulating execution plan..."))

        # Initial prompt to set system context for ReAct tool calling
        xml_tools = self.tools.generate_xml_prompt_instructions()
        react_instructions = f"""You are operating in ReAct (Reason-Act-Observe) agentic mode.
Solve the task step-by-step using available tools.

{xml_tools}

Always analyze first, create/update tasks if complex, pick a tool, observe its result, and verify before declaring completion.
"""
        self.llm.set_system_context(react_instructions)

        step = 0
        final_answer = ""

        while step < self.max_steps:
            step += 1
            self.bus.emit(AgentEvent(
                type=EventType.AGENT_THINKING,
                status_text=f"ReAct Step {step}/{self.max_steps}: Reasoning...",
                elapsed_time=time.time() - self.task_manager.bus._subscribers[0].__dict__.get("start_time", time.time()) if self.task_manager.bus._subscribers else 0
            ))

            # Query LLM with native tool schemas
            tool_schemas = self.tools.to_json_schemas()
            llm_output = self.llm.chat(user_request if step == 1 else "Continue step-by-step.", tools=tool_schemas)

            # Check if JSON structure returned (for tool calls)
            tool_calls = []
            assistant_text = llm_output

            try:
                parsed_json = json.loads(llm_output)
                if isinstance(parsed_json, dict) and "tool_calls" in parsed_json:
                    assistant_text = parsed_json.get("content", "")
                    tool_calls = parse_json_tool_calls(parsed_json["tool_calls"])
            except Exception:
                pass

            # Fallback to XML tool calls parsing if native tool calls absent
            if not tool_calls:
                xml_calls = parse_xml_tool_calls(llm_output)
                for name, args in xml_calls:
                    tool_calls.append((name, args, f"xml_{step}"))

            if assistant_text:
                self.bus.emit(AgentEvent(type=EventType.MESSAGE_DELTA, content=assistant_text))

            # If no tool calls requested, we have reached final response
            if not tool_calls:
                final_answer = assistant_text
                break

            # Execute tool calls sequentially
            for tool_name, tool_args, tool_id in tool_calls:
                res = self.tools.execute_call(tool_name, tool_args)
                output_str = str(res.get("output") or res.get("error") or "")
                # Append tool observation back to LLM context
                self.llm.append_tool_result(tool_id, output_str)

        self.bus.emit(AgentEvent(type=EventType.AGENT_COMPLETE, status_text="Execution completed."))
        return final_answer or "Agent execution finished."
