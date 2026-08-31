# Delta Autonomous Engineering Agent (Phase 2: Repository Intelligence & RepositoryGraph) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Repository Intelligence Subsystem for Delta: Language/Framework/Test Runner Detectors, AST Multi-language Symbol Parsers, structured `RepositoryGraph` representation (Files, Modules, Symbols, Imports, Calls, Routes, Tests), and Incremental Indexing cache.

**Architecture:** Implement `delta/intelligence/repository/` and `delta/intelligence/symbols/` as pure, fast, deterministic analyzers. The graph model tracks nodes and directional edges, handles incremental updates via SHA-256 file hashing, and exports to `.delta/graph.json`.

**Tech Stack:** Python 3.10+, stdlib (`ast`, `hashlib`, `pathlib`, `json`, `re`, `dataclasses`, `enum`), pytest.

## Global Constraints

- Must never scan or parse whole repositories blindly on each query; incremental cache with file SHA-256 invalidation is mandatory.
- Multi-language AST support: Python (`ast`), JavaScript/TypeScript (regex & AST tokens), PHP (token structure), Go, Rust.
- Detect frameworks and test commands accurately (pytest, jest, vitest, phpunit, cargo test, go test, dotnet test).
- Zero regression on all 364 existing tests.

---

### Task 1: Environment & Project Detector (Language, Framework, Build & Test Runners)

**Files:**
- Create: `delta/intelligence/repository/detector.py`
- Create: `delta/intelligence/repository/__init__.py`
- Create: `delta/intelligence/__init__.py`
- Test: `tests/test_repo_detector.py`

**Interfaces:**
- Produces: `ProjectInfo`, `DetectorResult`, `RepositoryDetector.detect(root_path) -> DetectorResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_repo_detector.py
import tempfile
import os
from delta.intelligence.repository.detector import RepositoryDetector

def test_detect_python_pytest_project():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "pyproject.toml"), "w") as f:
            f.write("[tool.pytest.ini_options]\n")
        with open(os.path.join(tmp, "main.py"), "w") as f:
            f.write("print('hello')\n")
            
        detector = RepositoryDetector(tmp)
        info = detector.detect()
        assert "python" in info.languages
        assert info.primary_language == "python"
        assert info.test_runner == "pytest"
        assert info.test_command == "pytest"

def test_detect_node_project():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "package.json"), "w") as f:
            f.write('{"scripts": {"test": "jest"}, "dependencies": {"react": "^18.0.0"}}')
            
        detector = RepositoryDetector(tmp)
        info = detector.detect()
        assert "javascript" in info.languages or "typescript" in info.languages
        assert "react" in info.frameworks
        assert info.test_runner == "jest"
        assert info.test_command == "npm test"

def test_detect_laravel_project():
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "composer.json"), "w") as f:
            f.write('{"require": {"laravel/framework": "^10.0"}}')
        with open(os.path.join(tmp, "artisan"), "w") as f:
            f.write("<?php")
            
        detector = RepositoryDetector(tmp)
        info = detector.detect()
        assert "php" in info.languages
        assert "laravel" in info.frameworks
        assert info.test_command == "php artisan test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_repo_detector.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.intelligence'`

- [ ] **Step 3: Write minimal implementation**

```python
# delta/intelligence/repository/detector.py
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

@dataclass
class DetectorResult:
    primary_language: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)
    build_systems: List[str] = field(default_factory=list)
    test_runner: Optional[str] = None
    test_command: Optional[str] = None
    entrypoints: List[str] = field(default_factory=list)
    has_git: bool = False

class RepositoryDetector:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()

    def detect(self) -> DetectorResult:
        languages: Set[str] = set()
        frameworks: Set[str] = set()
        package_managers: Set[str] = set()
        build_systems: Set[str] = set()
        test_runner = None
        test_command = None
        entrypoints: List[str] = []

        has_git = (self.root / ".git").exists()

        # Check Python
        if (self.root / "pyproject.toml").exists() or (self.root / "setup.py").exists() or (self.root / "requirements.txt").exists() or any(self.root.glob("*.py")):
            languages.add("python")
            package_managers.add("pip")
            test_runner = "pytest"
            test_command = "pytest"
            if (self.root / "manage.py").exists():
                frameworks.add("django")
            if (self.root / "app.py").exists():
                entrypoints.append("app.py")
            if (self.root / "main.py").exists():
                entrypoints.append("main.py")

        # Check Node / JS / TS
        pkg_json = self.root / "package.json"
        if pkg_json.exists():
            languages.add("javascript")
            package_managers.add("npm")
            if (self.root / "tsconfig.json").exists() or any(self.root.glob("**/*.ts")):
                languages.add("typescript")
            try:
                with open(pkg_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    if "react" in deps:
                        frameworks.add("react")
                    if "vue" in deps:
                        frameworks.add("vue")
                    if "express" in deps:
                        frameworks.add("express")
                    if "next" in deps:
                        frameworks.add("next.js")
                    if "jest" in deps:
                        test_runner = "jest"
                        test_command = "npm test"
                    elif "vitest" in deps:
                        test_runner = "vitest"
                        test_command = "npx vitest run"
                    else:
                        test_runner = "npm test"
                        test_command = "npm test"
            except Exception:
                pass

        # Check PHP / Laravel
        composer_json = self.root / "composer.json"
        if composer_json.exists():
            languages.add("php")
            package_managers.add("composer")
            if (self.root / "artisan").exists():
                frameworks.add("laravel")
                test_runner = "artisan test"
                test_command = "php artisan test"
            elif (self.root / "phpunit.xml").exists() or (self.root / "phpunit.xml.dist").exists():
                test_runner = "phpunit"
                test_command = "./vendor/bin/phpunit"

        # Check Go
        if (self.root / "go.mod").exists():
            languages.add("go")
            test_runner = "go test"
            test_command = "go test ./..."

        # Check Rust
        if (self.root / "Cargo.toml").exists():
            languages.add("rust")
            test_runner = "cargo test"
            test_command = "cargo test"

        # Primary language heuristic
        primary = "unknown"
        if "python" in languages:
            primary = "python"
        elif "typescript" in languages:
            primary = "typescript"
        elif "javascript" in languages:
            primary = "javascript"
        elif "php" in languages:
            primary = "php"
        elif "go" in languages:
            primary = "go"
        elif "rust" in languages:
            primary = "rust"
        elif languages:
            primary = list(languages)[0]

        return DetectorResult(
            primary_language=primary,
            languages=sorted(list(languages)),
            frameworks=sorted(list(frameworks)),
            package_managers=sorted(list(package_managers)),
            build_systems=sorted(list(build_systems)),
            test_runner=test_runner,
            test_command=test_command,
            entrypoints=entrypoints,
            has_git=has_git
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_repo_detector.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/intelligence/repository/detector.py delta/intelligence/repository/__init__.py delta/intelligence/__init__.py tests/test_repo_detector.py
git commit -m "feat(intelligence): implement RepositoryDetector for environment and framework discovery"
```

---

### Task 2: Multi-Language AST Symbol & Reference Extractor

**Files:**
- Create: `delta/intelligence/symbols/ast_parser.py`
- Create: `delta/intelligence/symbols/__init__.py`
- Test: `tests/test_ast_symbol_parser.py`

**Interfaces:**
- Produces: `SymbolInfo` (name, kind: function|class|method|interface, qname, start_line, end_line, signature, docstring), `ASTSymbolParser.parse_file(file_path, content) -> List[SymbolInfo]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ast_symbol_parser.py
from delta.intelligence.symbols.ast_parser import ASTSymbolParser

def test_parse_python_symbols():
    py_code = '''
class AuthService:
    """Handles authentication."""
    def validate_token(self, token: str) -> bool:
        return len(token) > 10

def generate_key(user_id: int):
    return f"key_{user_id}"
'''
    parser = ASTSymbolParser()
    symbols = parser.parse_content("auth/service.py", py_code, language="python")
    names = [s.name for s in symbols]
    assert "AuthService" in names
    assert "validate_token" in names
    assert "generate_key" in names

    auth_cls = next(s for s in symbols if s.name == "AuthService")
    assert auth_cls.kind == "class"
    assert "Handles authentication" in auth_cls.docstring

    val_tok = next(s for s in symbols if s.name == "validate_token")
    assert val_tok.kind == "method"
    assert val_tok.parent_name == "AuthService"

def test_parse_js_ts_symbols():
    js_code = '''
export class TokenValidator {
    verify(token) {
        return true;
    }
}

export function parseHeader(header) {
    return header.split(" ");
}
'''
    parser = ASTSymbolParser()
    symbols = parser.parse_content("src/auth.ts", js_code, language="typescript")
    names = [s.name for s in symbols]
    assert "TokenValidator" in names
    assert "verify" in names
    assert "parseHeader" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ast_symbol_parser.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.intelligence.symbols'`

- [ ] **Step 3: Write minimal implementation**

```python
# delta/intelligence/symbols/ast_parser.py
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
                # Check if top-level function (not method)
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
        
        # Regex heuristics for JS/TS classes, methods, functions
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ast_symbol_parser.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/intelligence/symbols/ast_parser.py delta/intelligence/symbols/__init__.py tests/test_ast_symbol_parser.py
git commit -m "feat(intelligence): implement ASTSymbolParser for Python, JS/TS, and PHP"
```

---

### Task 3: RepositoryGraph and Incremental Indexer

**Files:**
- Create: `delta/intelligence/repository/graph.py`
- Create: `delta/intelligence/repository/indexer.py`
- Test: `tests/test_repository_graph.py`

**Interfaces:**
- Produces: `RepositoryGraph`, `GraphNode`, `GraphEdge`, `IncrementalIndexer(root_path).index_repository() -> RepositoryGraph`, `graph.find_symbol(name)`, `graph.find_callers(qname)`, `graph.save(path)`, `graph.load(path)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_repository_graph.py
import tempfile
import os
from delta.intelligence.repository.indexer import IncrementalIndexer
from delta.intelligence.repository.graph import RepositoryGraph

def test_incremental_indexing_and_symbol_query():
    with tempfile.TemporaryDirectory() as tmp:
        src_dir = os.path.join(tmp, "src")
        os.makedirs(src_dir, exist_ok=True)
        
        file1 = os.path.join(src_dir, "calc.py")
        with open(file1, "w") as f:
            f.write("def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n")

        indexer = IncrementalIndexer(tmp)
        graph = indexer.index()
        
        assert len(graph.files) == 1
        syms = graph.find_symbols("add")
        assert len(syms) == 1
        assert syms[0].name == "add"

        # Check persistence
        graph_file = os.path.join(tmp, ".delta", "graph.json")
        assert os.path.exists(graph_file)

        # Reload graph
        loaded = RepositoryGraph.load(graph_file)
        assert len(loaded.find_symbols("multiply")) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_repository_graph.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'delta.intelligence.repository.graph'`

- [ ] **Step 3: Write minimal implementation**

```python
# delta/intelligence/repository/graph.py
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path
from delta.intelligence.symbols.ast_parser import SymbolInfo

@dataclass
class FileMetadata:
    path: str
    sha256: str
    language: str
    size: int
    symbol_count: int

@dataclass
class RepositoryGraph:
    root_path: str
    files: Dict[str, FileMetadata] = field(default_factory=dict)
    symbols: List[SymbolInfo] = field(default_factory=list)
    imports: Dict[str, List[str]] = field(default_factory=dict)
    routes: List[Dict[str, Any]] = field(default_factory=list)

    def find_symbols(self, name: str) -> List[SymbolInfo]:
        return [s for s in self.symbols if s.name.lower() == name.lower()]

    def find_symbols_in_file(self, file_path: str) -> List[SymbolInfo]:
        return [s for s in self.symbols if s.file_path == file_path]

    def save(self, path: str):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "root_path": self.root_path,
            "files": {k: asdict(v) for k, v in self.files.items()},
            "symbols": [asdict(s) for s in self.symbols],
            "imports": self.imports,
            "routes": self.routes
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "RepositoryGraph":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        graph = cls(root_path=data["root_path"])
        graph.files = {k: FileMetadata(**v) for k, v in data.get("files", {}).items()}
        graph.symbols = [SymbolInfo(**s) for s in data.get("symbols", [])]
        graph.imports = data.get("imports", {})
        graph.routes = data.get("routes", [])
        return graph
```

```python
# delta/intelligence/repository/indexer.py
import os
import hashlib
from pathlib import Path
from typing import Optional
from delta.intelligence.repository.graph import RepositoryGraph, FileMetadata
from delta.intelligence.symbols.ast_parser import ASTSymbolParser

class IncrementalIndexer:
    IGNORED_DIRS = {".git", ".delta", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".idea", ".vscode"}
    ALLOWED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".go", ".rs"}

    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()
        self.delta_dir = self.root / ".delta"
        self.graph_file = self.delta_dir / "graph.json"
        self.parser = ASTSymbolParser()

    def _file_hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()

    def index(self) -> RepositoryGraph:
        graph = RepositoryGraph(root_path=str(self.root))
        if self.graph_file.exists():
            try:
                graph = RepositoryGraph.load(str(self.graph_file))
            except Exception:
                graph = RepositoryGraph(root_path=str(self.root))

        current_files = set()

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in self.IGNORED_DIRS]
            for fn in filenames:
                ext = os.path.splitext(fn)[1]
                if ext in self.ALLOWED_EXTENSIONS:
                    full_p = Path(dirpath) / fn
                    rel_p = str(full_p.relative_to(self.root)).replace("\\", "/")
                    current_files.add(rel_p)

                    fhash = self._file_hash(full_p)
                    # Check if file changed
                    if rel_p not in graph.files or graph.files[rel_p].sha256 != fhash:
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        lang = "python" if ext == ".py" else ("typescript" if ext in [".ts", ".tsx"] else ("javascript" if ext in [".js", ".jsx"] else "php"))
                        syms = self.parser.parse_content(rel_p, content, language=lang)

                        # Remove old symbols for this file
                        graph.symbols = [s for s in graph.symbols if s.file_path != rel_p]
                        graph.symbols.extend(syms)

                        graph.files[rel_p] = FileMetadata(
                            path=rel_p,
                            sha256=fhash,
                            language=lang,
                            size=len(content),
                            symbol_count=len(syms)
                        )

        # Remove deleted files
        deleted = set(graph.files.keys()) - current_files
        for d in deleted:
            del graph.files[d]
            graph.symbols = [s for s in graph.symbols if s.file_path != d]

        graph.save(str(self.graph_file))
        return graph
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_repository_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delta/intelligence/repository/graph.py delta/intelligence/repository/indexer.py tests/test_repository_graph.py
git commit -m "feat(intelligence): implement RepositoryGraph and IncrementalIndexer"
```
