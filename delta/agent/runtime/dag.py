# delta/agent/runtime/dag.py
from typing import List, Dict, Set, Optional

class TaskDAG:
    def __init__(self):
        self.nodes: Set[str] = set()
        self.deps: Dict[str, Set[str]] = {}
        self.completed: Set[str] = set()
        self.running: Set[str] = set()
        self.failed: Set[str] = set()

    def add_node(self, node_id: str, deps: Optional[List[str]] = None):
        self.nodes.add(node_id)
        self.deps[node_id] = set(deps or [])

    def get_executable_nodes(self) -> List[str]:
        executable = []
        for node in self.nodes:
            if node in self.completed or node in self.running or node in self.failed:
                continue
            node_deps = self.deps.get(node, set())
            if node_deps.issubset(self.completed):
                executable.append(node)
        return sorted(executable)

    def mark_running(self, node_id: str):
        self.running.add(node_id)

    def mark_completed(self, node_id: str):
        if node_id in self.running:
            self.running.remove(node_id)
        self.completed.add(node_id)

    def mark_failed(self, node_id: str):
        if node_id in self.running:
            self.running.remove(node_id)
        self.failed.add(node_id)

    def is_finished(self) -> bool:
        return (len(self.completed) + len(self.failed)) == len(self.nodes)
