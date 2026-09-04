import os
import hashlib
from pathlib import Path
from typing import Optional
from delta.intelligence.repository.graph import RepositoryGraph, FileMetadata
from delta.intelligence.symbols.ast_parser import ASTSymbolParser

class IncrementalIndexer:
    IGNORED_DIRS = {".git", ".delta", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".idea", ".vscode"}
    ALLOWED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".go", ".rs"}

    def __init__(self, root_path: str = ".", workspace_root: Optional[str] = None):
        target = workspace_root if workspace_root is not None else root_path
        self.root = Path(target).resolve()
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
