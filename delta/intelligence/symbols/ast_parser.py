import ast
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SymbolInfo:
    name: str
    kind: str  # "class", "function", "method", "interface"
    file_path: str
    start_line: int
    end_line: int
    signature: str
    docstring: str = ""
    parent_name: Optional[str] = None
    qname: str = ""

class ASTSymbolParser:
    def parse_content(self, file_path: str, content: str, language: str = "python") -> List[SymbolInfo]:
        if language == "python" or file_path.endswith(".py"):
            return self._parse_python(file_path, content)
        elif language in ["javascript", "typescript"] or file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
            return self._parse_js_ts(file_path, content)
        elif language == "php" or file_path.endswith(".php"):
            return self._parse_php(file_path, content)
        return []

    def _parse_python(self, file_path: str, content: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        try:
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                symbols.append(SymbolInfo(
                    name=node.name,
                    kind="class",
                    file_path=file_path,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    signature=f"class {node.name}",
                    docstring=doc,
                    qname=f"{file_path}:{node.name}"
                ))
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_doc = ast.get_docstring(item) or ""
                        symbols.append(SymbolInfo(
                            name=item.name,
                            kind="method",
                            file_path=file_path,
                            start_line=item.lineno,
                            end_line=getattr(item, "end_lineno", item.lineno),
                            signature=f"def {item.name}(...)",
                            docstring=method_doc,
                            parent_name=node.name,
                            qname=f"{file_path}:{node.name}.{item.name}"
                        ))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Top-level functions only
                if not any(isinstance(parent, ast.ClassDef) and node in parent.body for parent in ast.walk(tree)):
                    fn_doc = ast.get_docstring(node) or ""
                    symbols.append(SymbolInfo(
                        name=node.name,
                        kind="function",
                        file_path=file_path,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        signature=f"def {node.name}(...)",
                        docstring=fn_doc,
                        qname=f"{file_path}:{node.name}"
                    ))
        return symbols

    def _parse_js_ts(self, file_path: str, content: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()

        class_pat = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)")
        fn_pat = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(")
        method_pat = re.compile(r"^\s*(?:async\s+)?([A-Za-z0-9_$]+)\s*\([^)]*\)\s*\{")

        current_class = None
        for idx, line in enumerate(lines, 1):
            c_match = class_pat.search(line)
            if c_match:
                name = c_match.group(1)
                current_class = name
                symbols.append(SymbolInfo(
                    name=name,
                    kind="class",
                    file_path=file_path,
                    start_line=idx,
                    end_line=idx,
                    signature=line.strip(),
                    qname=f"{file_path}:{name}"
                ))
                continue

            f_match = fn_pat.search(line)
            if f_match:
                name = f_match.group(1)
                symbols.append(SymbolInfo(
                    name=name,
                    kind="function",
                    file_path=file_path,
                    start_line=idx,
                    end_line=idx,
                    signature=line.strip(),
                    qname=f"{file_path}:{name}"
                ))
                continue

            if current_class:
                m_match = method_pat.search(line)
                if m_match and not line.strip().startswith("if") and not line.strip().startswith("for"):
                    name = m_match.group(1)
                    symbols.append(SymbolInfo(
                        name=name,
                        kind="method",
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        signature=line.strip(),
                        parent_name=current_class,
                        qname=f"{file_path}:{current_class}.{name}"
                    ))
        return symbols

    def _parse_php(self, file_path: str, content: str) -> List[SymbolInfo]:
        symbols: List[SymbolInfo] = []
        lines = content.splitlines()
        class_pat = re.compile(r"^\s*(?:abstract\s+|final\s+)?class\s+([A-Za-z0-9_]+)")
        fn_pat = re.compile(r"^\s*(?:public\s+|protected\s+|private\s+|static\s+)*function\s+([A-Za-z0-9_]+)\s*\(")

        current_class = None
        for idx, line in enumerate(lines, 1):
            c_match = class_pat.search(line)
            if c_match:
                current_class = c_match.group(1)
                symbols.append(SymbolInfo(
                    name=current_class,
                    kind="class",
                    file_path=file_path,
                    start_line=idx,
                    end_line=idx,
                    signature=line.strip(),
                    qname=f"{file_path}:{current_class}"
                ))
                continue
            f_match = fn_pat.search(line)
            if f_match:
                name = f_match.group(1)
                symbols.append(SymbolInfo(
                    name=name,
                    kind="method" if current_class else "function",
                    file_path=file_path,
                    start_line=idx,
                    end_line=idx,
                    signature=line.strip(),
                    parent_name=current_class,
                    qname=f"{file_path}:{current_class}.{name}" if current_class else f"{file_path}:{name}"
                ))
        return symbols
