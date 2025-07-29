"""
Core knowledge graph implementation.
"""
import os
import pickle
import networkx as nx
from typing import Dict, List

from .models import GraphNode, GraphEdge


class KnowledgeGraph:
    """Graph-based knowledge system for RAG"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        
    def add_node(self, node: GraphNode):
        """Add a node to the graph"""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, 
                          type=node.type, 
                          content=node.content,
                          metadata=node.metadata)
    
    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph"""
        self.edges.append(edge)
        self.graph.add_edge(edge.source, edge.target,
                          relationship=edge.relationship_type,
                          weight=edge.weight,
                          metadata=edge.metadata)
        
        # Update node connections
        if edge.source in self.nodes:
            self.nodes[edge.source].connections.add(edge.target)
        if edge.target in self.nodes:
            self.nodes[edge.target].connections.add(edge.source)
    
    def get_connected_nodes(self, node_id: str, max_depth: int = 2, max_nodes: int = 10) -> List[GraphNode]:
        """Get connected nodes with limits to prevent context explosion"""
        if node_id not in self.graph:
            return []
        
        connected_ids = set()
        current_level = {node_id}
        
        for depth in range(max_depth):
            next_level = set()
            for current_id in current_level:
                neighbors = set(self.graph.neighbors(current_id)) | set(self.graph.predecessors(current_id))
                # Sort neighbors by edge weight (if available) to prioritize stronger connections
                neighbor_weights = []
                for neighbor in neighbors:
                    if neighbor not in connected_ids:
                        weight = self.graph.get_edge_data(current_id, neighbor, {}).get('weight', 0.5)
                        neighbor_weights.append((neighbor, weight))
                
                # Sort by weight descending and take top connections
                neighbor_weights.sort(key=lambda x: x[1], reverse=True)
                top_neighbors = [n[0] for n in neighbor_weights[:max_nodes//max_depth]]
                
                next_level.update(top_neighbors)
                connected_ids.update(top_neighbors)
                
                # Stop if we have enough nodes
                if len(connected_ids) >= max_nodes:
                    break
            
            current_level = next_level
            if len(connected_ids) >= max_nodes:
                break
        
        # Return top nodes sorted by relationship strength
        result_nodes = []
        for node_id in list(connected_ids)[:max_nodes]:
            if node_id in self.nodes:
                result_nodes.append(self.nodes[node_id])
        
        return result_nodes
    
    def get_path_context(self, node_id: str, target_id: str) -> List[GraphNode]:
        """Get context by finding paths between nodes"""
        try:
            path = nx.shortest_path(self.graph, node_id, target_id)
            return [self.nodes[nid] for nid in path if nid in self.nodes]
        except nx.NetworkXNoPath:
            return []
    
    def save_to_disk(self, filepath: str):
        """Save knowledge graph to disk"""
        try:
            graph_data = {
                'nodes': self.nodes,
                'edges': self.edges,
                'graph': self.graph
            }
            with open(filepath, 'wb') as f:
                pickle.dump(graph_data, f)
            print(f"✅ Knowledge graph saved to {filepath}")
        except Exception as e:
            print(f"❌ Error saving knowledge graph: {str(e)}")
    
    def load_from_disk(self, filepath: str) -> bool:
        """Load knowledge graph from disk"""
        try:
            if not os.path.exists(filepath):
                return False
                
            with open(filepath, 'rb') as f:
                graph_data = pickle.load(f)
            
            self.nodes = graph_data['nodes']
            self.edges = graph_data['edges'] 
            self.graph = graph_data['graph']
            
            print(f"✅ Knowledge graph loaded from {filepath}")
            print(f"📊 Loaded {len(self.nodes)} nodes and {len(self.edges)} edges")
            return True
        except Exception as e:
            print(f"❌ Error loading knowledge graph: {str(e)}")
            return False
