from pydantic import BaseModel, Field
from typing import Union
from .nodes import (
    RepoNode,
    FileNode,
    CommitNode,
    ModuleNode,
    ClassNode,
    FunctionNode,
    VariableNode,
    TestNode,
    DocNode,
    IssueNode,
    PackageNode,
)
from .relationships import Relationship

NodeUnion = Union[
    RepoNode,
    FileNode,
    CommitNode,
    ModuleNode,
    ClassNode,
    FunctionNode,
    VariableNode,
    TestNode,
    DocNode,
    IssueNode,
    PackageNode,
]


class GraphData(BaseModel):
    """Container for parsed graph data"""
    nodes: list[NodeUnion] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    
    def add_node(self, node: NodeUnion):
        self.nodes.append(node)
    
    def add_relationship(self, rel: Relationship):
        # Avoid duplicates
        if rel not in self.relationships:
            self.relationships.append(rel)
    
    def get_nodes_by_type(self, node_type: type):
        return [n for n in self.nodes if isinstance(n, node_type)]
