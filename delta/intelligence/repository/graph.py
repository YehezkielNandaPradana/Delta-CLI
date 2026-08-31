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
