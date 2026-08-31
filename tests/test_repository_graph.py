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
