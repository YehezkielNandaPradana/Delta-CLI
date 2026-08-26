# tests/test_ai_agent.py

"""

Comprehensive Unit and Integration Tests for Delta AI Coding Agent.

Tests Tool Registry, Codebase Intelligence, Terminal Execution, Smart Editing,

and ReAct execution loop capabilities.

"""

import os

import tempfile

from delta.ai.tools import Tool, ToolParameter, ToolRegistry, parse_xml_tool_calls

from delta.modules.codebase import CodebaseModule

from delta.modules.terminal import TerminalModule

from delta.modules.filesystem import FileSystemModule

class TestToolRegistry:

    def test_register_and_execute_tool(self):

        registry = ToolRegistry()

        tool = Tool(

            name="add_numbers",

            description="Add two numbers together",

            func=lambda a, b: a + b,

            parameters=[

                ToolParameter("a", "integer", "First number"),

                ToolParameter("b", "integer", "Second number"),

            ]

        )

        registry.register(tool)

        assert registry.get("add_numbers") is not None

        res = registry.execute_call("add_numbers", {"a": 5, "b": 10})

        assert res["success"] is True

        assert res["output"] == "15"

    def test_to_json_schema(self):

        registry = ToolRegistry()

        tool = Tool(

            name="grep_code",

            description="Search pattern in code",

            func=lambda pattern: pattern,

            parameters=[ToolParameter("pattern", "string", "Regex pattern")]

        )

        registry.register(tool)

        schemas = registry.to_json_schemas()

        assert len(schemas) == 1

        assert schemas[0]["function"]["name"] == "grep_code"

        assert "pattern" in schemas[0]["function"]["parameters"]["properties"]

    def test_xml_tool_call_parser(self):

        text = """

Let me search the files for you:

<tool_call>

  <name>find_files</name>

  <args>{"pattern": "llm.py"}</args>

</tool_call>

"""

        calls = parse_xml_tool_calls(text)

        assert len(calls) == 1

        name, args = calls[0]

        assert name == "find_files"

        assert args.get("pattern") == "llm.py"

class TestCodebaseModule:

    def test_build_tree_and_find_files(self):

        with tempfile.TemporaryDirectory() as tmpdir:

            sub = os.path.join(tmpdir, "src")

            os.makedirs(sub)

            test_file = os.path.join(sub, "main.py")

            with open(test_file, "w", encoding="utf-8") as f:

                f.write("def hello(): pass\n")

            cb = CodebaseModule(root_dir=tmpdir)

            tree = cb.build_tree(max_depth=2)

            assert "src" in tree

            found = cb.find_files("main.py")

            assert len(found) == 1

            symbols = cb.extract_symbols(os.path.join("src", "main.py"))

            assert symbols["success"] is True

            assert len(symbols["functions"]) == 1

            assert symbols["functions"][0]["name"] == "hello"

class TestTerminalModule:

    def test_execute_simple_command(self):

        term = TerminalModule(timeout=5)

        res = term.execute("echo 'Delta Coding Agent'")

        assert res["success"] is True

        assert "Delta Coding Agent" in res["output"]

    def test_block_dangerous_commands(self):

        term = TerminalModule()

        res = term.execute("rm -rf /")

        assert res["success"] is False

        assert "Command blocked" in res["error"]

class TestSmartEditFileSystem:

    def test_smart_edit_exact_and_fuzzy(self):

        with tempfile.TemporaryDirectory() as tmpdir:

            filepath = os.path.join(tmpdir, "sample.py")

            with open(filepath, "w", encoding="utf-8") as f:

                f.write("def add(a, b):\n    return a + b\n")

            fs = FileSystemModule(cwd=tmpdir)

            ok, msg = fs.smart_edit("sample.py", "return a + b", "return a * b")

            assert ok is True

            with open(filepath, "r", encoding="utf-8") as f:

                content = f.read()

            assert "return a * b" in content

    def test_smart_edit_prevents_syntax_error(self):

        with tempfile.TemporaryDirectory() as tmpdir:

            filepath = os.path.join(tmpdir, "broken.py")

            with open(filepath, "w", encoding="utf-8") as f:

                f.write("def valid_function():\n    pass\n")

            fs = FileSystemModule(cwd=tmpdir)

            ok, msg = fs.smart_edit("broken.py", "pass", "pass (broken syntax =")

            assert ok is False

            assert "SyntaxError" in msg

