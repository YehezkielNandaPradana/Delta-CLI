#!/usr/bin/env python3
"""Scan delta/ imports and enforce dependency direction rules."""
import ast
import sys
from pathlib import Path

RULES = {
    "delta": ["delta.ai", "delta.core", "delta.ml", "delta.modules", "delta.plugins", "delta.utils", "delta.web"],  # entry points compose everything
    "delta.core": ["delta.ai", "delta.ml", "delta.modules", "delta.utils"],  # core engine orchestrates downstream layers
    "delta.ai": ["delta.core"],  # ai can import core only
    "delta.modules": ["delta.utils", "delta.core", "delta.ai"],  # modules can import utils/core/ai
    "delta.web": ["delta.modules", "delta.utils", "delta.core", "delta.ai"],  # web can import modules/utils/ai
    "delta.ml": ["delta.ai", "delta.core", "delta.utils"],  # ml can import ai/core/utils
    "delta.utils": [],  # utils stdlib only
    "delta.skills": [],  # skills stdlib only
    "delta.plugins": [],  # plugins stdlib only
}

VIOLATIONS = []

for pyfile in Path("delta").rglob("*.py"):
    if pyfile.name == "__init__.py" and pyfile.parent == Path("delta"):
        continue
    tree = ast.parse(pyfile.read_text(encoding="utf-8"))
    source_ns = ".".join(pyfile.parts[:2]) if len(pyfile.parts) > 2 else "delta"
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("delta."):
            target_ns = ".".join(node.module.split(".")[:2])
            allowed = RULES.get(source_ns, [])
            if target_ns not in allowed and target_ns != source_ns:
                VIOLATIONS.append(
                    f"VIOLATION: {pyfile} imports {node.module} "
                    f"(allowed: {allowed or 'stdlib only'})"
                )

if VIOLATIONS:
    print("\n".join(VIOLATIONS))
    sys.exit(1)
else:
    print("OK: all imports follow dependency rules")
    sys.exit(0)