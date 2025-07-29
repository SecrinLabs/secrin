"""
Data models for the knowledge graph system.
"""
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    id: str
    type: str  # 'doc', 'issue', 'pr', 'commit'
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None
    connections: Set[str] = None
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = set()


@dataclass
class GraphEdge:
    """Represents an edge/relationship between nodes"""
    source: str
    target: str
    relationship_type: str
    weight: float = 1.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
