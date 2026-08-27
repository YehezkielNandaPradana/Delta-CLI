# Refactor: tools registry
# delta/ai/tools.py

"""

Tool and Function Calling Engine for Delta AI Coding Agent.

Provides JSON Schema tool definitions, a unified ToolRegistry, and dual parsers

(native API tool_calls + XML fallback parser) for models without native tool calling capabilities.

"""

import json

import os

import re

from dataclasses import dataclass, field

from typing import Any, Callable, Dict, List, Optional, Tuple

@dataclass

class ToolParameter:

    """Parameter definition for a Tool."""

    name: str

    type: str  # "string", "integer", "number", "boolean", "array", "object"

    description: str

    required: bool = True

    enum: Optional[List[str]] = None

    items: Optional[Dict[str, Any]] = None

@dataclass

class Tool:

    """Tool definition for LLM function calling."""

    name: str

    description: str

    func: Callable[..., Any]

    parameters: List[ToolParameter] = field(default_factory=list)

    category: str = "general"

    def to_json_schema(self) -> Dict[str, Any]:

        """Export tool definition to OpenAI/Anthropic compatible JSON Schema."""

        properties = {}

        required_params = []

        for p in self.parameters:

            param_schema: Dict[str, Any] = {

                "type": p.type,

                "description": p.description,

            }

            if p.enum:

                param_schema["enum"] = p.enum

            if p.items:

                param_schema["items"] = p.items

            properties[p.name] = param_schema

            if p.required:

                required_params.append(p.name)

        return {

            "type": "function",

            "function": {

                "name": self.name,

                "description": self.description,

                "parameters": {

                    "type": "object",

                    "properties": properties,

                    "required": required_params,

                },

            },

        }

    def execute(self, **kwargs) -> Dict[str, Any]:

        """Execute the tool function safely."""
        from delta.ai.events import event_bus, generate_real_diff

        path = kwargs.get("path") or kwargs.get("file_path")
        old_content = None
        if self.name in ("edit_file", "smart_edit", "write_file", "write") and path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    old_content = f.read()
            except Exception:
                old_content = ""
        elif self.name in ("write_file", "write") and path and not os.path.isfile(path):
            old_content = ""

        try:
            result = self.func(**kwargs)

            # Emit file_update diff if file was modified
            if path and old_content is not None and os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        new_content = f.read()
                    diff_event = generate_real_diff(path, old_content, new_content)
                    if diff_event:
                        event_bus.emit(diff_event)
                except Exception:
                    pass

            if isinstance(result, dict) and "success" in result:
                return result
            return {"success": True, "output": str(result), "error": None}

        except Exception as e:
            return {"success": False, "output": None, "error": str(e)}

class ToolRegistry:

    """Central registry holding tools available to Delta AI Agent."""

    def __init__(self) -> None:

        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:

        """Register a new tool."""

        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:

        """Get a tool by name."""

        return self._tools.get(name)

    def list_all(self) -> List[Tool]:

        """List all registered tools."""

        return list(self._tools.values())

    def list_tools(self) -> List[Tool]:

        """Alias for list_all."""

        return self.list_all()

    def to_json_schemas(self) -> List[Dict[str, Any]]:

        """Export all tools as JSON schema list for LLM providers."""

        return [tool.to_json_schema() for tool in self._tools.values()]

    def generate_xml_prompt_instructions(self) -> str:

        """Generate prompt instructions for models relying on XML tool calling."""

        if not self._tools:

            return ""

        lines = [

            "### AVAILABLE TOOLS",

            "You can invoke tools to inspect files, search code, execute commands, or edit files.",

            "To use a tool, format your call using the XML tag `<tool_call>`:",

            "",

            "```xml",

            "<tool_call>",

            "  <name>tool_name</name>",

            "  <args>",

            '    {"param_name": "value"}',

            "  </args>",

            "</tool_call>",

            "```",

            "",

            "Available Tool Specs:",

        ]

        for tool in self._tools.values():

            params_str = ", ".join([f"{p.name} ({p.type}{' optional' if not p.required else ''}): {p.description}" for p in tool.parameters])

            lines.append(f"- **{tool.name}**: {tool.description}")

            lines.append(f"  Parameters: {params_str or 'None'}")

        return "\n".join(lines)

    def execute_call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:

        """Execute a tool call by name with keyword arguments."""

        tool = self.get(name)

        if not tool:

            return {"success": False, "output": None, "error": f"Tool '{name}' is not registered."}

        return tool.execute(**args)

# --- Tool Call Parsers ---

XML_TOOL_CALL_PATTERN = re.compile(

    r"<tool_call>\s*<name>(.*?)</name>\s*<args>(.*?)</args>\s*</tool_call>",

    re.DOTALL | re.IGNORECASE,

)

def parse_xml_tool_calls(text: str) -> List[Tuple[str, Dict[str, Any]]]:

    """Parse XML-formatted tool calls from LLM text output."""

    calls: List[Tuple[str, Dict[str, Any]]] = []

    if not text:

        return calls

    matches = XML_TOOL_CALL_PATTERN.findall(text)

    for name, raw_args in matches:

        name = name.strip()

        raw_args = raw_args.strip()

        try:

            args = json.loads(raw_args) if raw_args else {}

        except json.JSONDecodeError:

            # Fallback to key-value regex extraction if JSON parsing fails

            args = {}

            kv_pairs = re.findall(r'"(\w+)":\s*"([^"]+)"', raw_args)

            for k, v in kv_pairs:

                args[k] = v

        calls.append((name, args))

    return calls

def parse_json_tool_calls(tool_calls_payload: List[Dict[str, Any]]) -> List[Tuple[str, Dict[str, Any], str]]:

    """Parse OpenAI/Anthropic style tool_calls payload list.

    Returns list of (tool_name, arguments_dict, tool_call_id).

    """

    results: List[Tuple[str, Dict[str, Any], str]] = []

    for call in tool_calls_payload:

        tool_id = call.get("id", f"call_{len(results)}")

        function_data = call.get("function", {})

        name = function_data.get("name", "")

        raw_args = function_data.get("arguments", {})

        if isinstance(raw_args, str):

            try:

                args = json.loads(raw_args) if raw_args else {}

            except json.JSONDecodeError:

                args = {}

        else:

            args = raw_args or {}

        results.append((name, args, tool_id))

    return results

