# delta/modules/codebase.py

"""

Codebase Intelligence Module for Delta AI Coding Agent.

Provides workspace tree building, glob file searching, and AST symbol extraction

(classes, functions, methods, imports) for code analysis.

"""

import ast

import os

import re

from typing import Any, Dict, List, Optional

class CodebaseModule:

    """Codebase understanding and search module."""

    def __init__(self, root_dir: Optional[str] = None) -> None:

        self.root_dir = os.path.abspath(root_dir or os.getcwd())

        self.ignore_dirs = {

            ".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".venv",

            "venv", "node_modules", "dist", "build", ".claude", ".idea", ".vscode"

        }

    def build_tree(self, max_depth: int = 3, max_files: int = 200) -> str:

        """Generate a clean ASCII file tree of the workspace."""

        lines: List[str] = []

        total_files = 0

        def _traverse(current_dir: str, depth: int, prefix: str) -> None:

            nonlocal total_files

            if depth > max_depth or total_files >= max_files:

                return

            try:

                entries = sorted(os.listdir(current_dir))

            except PermissionError:

                return

            dirs = [e for e in entries if os.path.isdir(os.path.join(current_dir, e)) and e not in self.ignore_dirs]

            files = [e for e in entries if os.path.isfile(os.path.join(current_dir, e))]

            all_entries = dirs + files

            for i, entry in enumerate(all_entries):

                if total_files >= max_files:

                    lines.append(f"{prefix}... [truncated]")

                    break

                is_last = (i == len(all_entries) - 1)

                connector = "└── " if is_last else "├── "

                rel_path = os.path.join(current_dir, entry)

                lines.append(f"{prefix}{connector}{entry}")

                if os.path.isdir(rel_path) and entry not in self.ignore_dirs:

                    extension = "    " if is_last else "│   "

                    _traverse(rel_path, depth + 1, prefix + extension)

                else:

                    total_files += 1

        lines.append(f"📁 {os.path.basename(self.root_dir) or self.root_dir}")

        _traverse(self.root_dir, 1, "")

        return "\n".join(lines)

    def find_files(self, pattern: str, max_results: int = 50) -> List[str]:

        """Find files in workspace matching a glob or substring pattern."""

        results: List[str] = []

        pattern_lower = pattern.lower()

        for root, dirs, files in os.walk(self.root_dir):

            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            for f in files:

                rel_path = os.path.relpath(os.path.join(root, f), self.root_dir)

                if pattern_lower in f.lower() or pattern_lower in rel_path.lower():

                    results.append(rel_path)

                    if len(results) >= max_results:

                        return results

        return results

    def extract_symbols(self, file_path: str) -> Dict[str, Any]:

        """Extract class, function, and method symbols from Python file via AST."""

        full_path = os.path.join(self.root_dir, file_path) if not os.path.isabs(file_path) else file_path

        if not os.path.exists(full_path):

            return {"success": False, "error": f"File '{file_path}' does not exist."}

        if not full_path.endswith(".py"):

            # Fallback regex symbol extractor for non-python files

            return self._regex_extract_symbols(full_path)

        try:

            with open(full_path, "r", encoding="utf-8", errors="replace") as f:

                content = f.read()

            tree = ast.parse(content, filename=full_path)

            classes: List[Dict[str, Any]] = []

            functions: List[Dict[str, Any]] = []

            imports: List[str] = []

            for node in ast.walk(tree):

                if isinstance(node, ast.ClassDef):

                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]

                    classes.append({"name": node.name, "line": node.lineno, "methods": methods})

                elif isinstance(node, ast.FunctionDef) and not isinstance(getattr(node, 'parent', None), ast.ClassDef):

                    functions.append({"name": node.name, "line": node.lineno, "args": [a.arg for a in node.args.args]})

                elif isinstance(node, ast.Import):

                    for alias in node.names:

                        imports.append(alias.name)

                elif isinstance(node, ast.ImportFrom):

                    mod = node.module or ""

                    for alias in node.names:

                        imports.append(f"{mod}.{alias.name}")

            return {

                "success": True,

                "file": file_path,

                "classes": classes,

                "functions": functions,

                "imports": imports,

            }

        except Exception as e:

            return {"success": False, "error": f"Failed to parse AST: {str(e)}"}

    def _regex_extract_symbols(self, full_path: str) -> Dict[str, Any]:

        """Regex symbol extraction fallback for JS/TS/Go/etc."""

        try:

            with open(full_path, "r", encoding="utf-8", errors="replace") as f:

                lines = f.readlines()

            functions = []

            classes = []

            for idx, line in enumerate(lines, 1):

                fn_match = re.search(r'(?:function|def|const|let|var)\s+([a-zA-Z0-9_]+)\s*=?\s*\(', line)

                if fn_match:

                    functions.append({"name": fn_match.group(1), "line": idx})

                cls_match = re.search(r'(?:class|interface|type)\s+([a-zA-Z0-9_]+)', line)

                if cls_match:

                    classes.append({"name": cls_match.group(1), "line": idx})

            return {

                "success": True,

                "file": os.path.basename(full_path),

                "classes": classes,

                "functions": functions,

                "imports": [],

            }

        except Exception as e:

            return {"success": False, "error": str(e)}

