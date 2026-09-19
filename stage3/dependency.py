from typing import Dict, List, Set

class DependencyGraph:
    def __init__(self):
        # forward: what depends on this node?
        self.forward: Dict[str, Set[str]] = {}
        # reverse: what does this node depend on?
        self.reverse: Dict[str, Set[str]] = {}
        # validity state
        self.validity: Dict[str, bool] = {}

    def add_node(self, node_id: str):
        if node_id not in self.forward:
            self.forward[node_id] = set()
        if node_id not in self.reverse:
            self.reverse[node_id] = set()
        if node_id not in self.validity:
            self.validity[node_id] = True

    def add_edge(self, from_node: str, to_node: str):
        self.add_node(from_node)
        self.add_node(to_node)
        self.forward[from_node].add(to_node)
        self.reverse[to_node].add(from_node)
        if not self.validity.get(from_node, True):
            self.invalidate(to_node)

    def invalidate(self, node_id: str):
        if node_id not in self.validity or not self.validity[node_id]:
            return # Already invalid or doesn't exist
            
        self.validity[node_id] = False
        
        # Recursively invalidate downstream
        for dependent in self.forward.get(node_id, []):
            self.invalidate(dependent)

    def is_valid(self, node_id: str) -> bool:
        return self.validity.get(node_id, False)

    def mark_valid(self, node_id: str):
        if node_id in self.validity:
            self.validity[node_id] = True
