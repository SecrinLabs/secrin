import time
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from tqdm import tqdm
from sqlalchemy.orm import Session
from ollama import generate
import networkx as nx
import json

from embeddings.factory import get_embedder
from retriever.factory import get_vectorstore
from service.src.models import engine
from service.src.models.Sitemap import Sitemap
from service.src.models.Issue import Issue
from config import settings

config = settings

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

class GraphBasedRAG:
    """Enhanced RAG system with graph-based context retrieval"""
    
    def __init__(self, embedder, vectorstore):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.knowledge_graph = KnowledgeGraph()
        
    def safe_embed(self, text: str) -> Optional[List[float]]:
        """Safely embed text with error handling"""
        try:
            embedding = self.embedder.embed(text)
            if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], (list, tuple)):
                return embedding[0]
            return embedding
        except Exception as e:
            print(f"❌ Embedding error: {str(e)}")
            return None
    
    def sanitize_metadata(self, metadata: Dict) -> Dict:
        """Sanitize metadata to ensure vectorstore compatibility"""
        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, (list, tuple)):
                # Convert arrays to comma-separated strings
                sanitized[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                sanitized[key] = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)) or value is None:
                # Keep scalar values as is
                sanitized[key] = value
            else:
                # Convert other types to strings
                sanitized[key] = str(value)
        return sanitized
    
    def extract_references(self, text: str) -> Dict[str, List[str]]:
        """Extract references to issues, PRs, commits from text"""
        references = {
            'issues': [],
            'prs': [],
            'commits': [],
            'files': []
        }
        
        # GitHub issue references (#123, issue #123)
        issue_pattern = r'#(\d+)|issue\s+#(\d+)'
        issues = re.findall(issue_pattern, text.lower())
        references['issues'] = [i[0] or i[1] for i in issues if i[0] or i[1]]
        
        # PR references (PR #123, pull request #123)
        pr_pattern = r'pr\s+#(\d+)|pull\s+request\s+#(\d+)'
        prs = re.findall(pr_pattern, text.lower())
        references['prs'] = [p[0] or p[1] for p in prs if p[0] or p[1]]
        
        # Commit hashes (40 or 7+ character hex)
        commit_pattern = r'\b([a-f0-9]{7,40})\b'
        commits = re.findall(commit_pattern, text.lower())
        references['commits'] = commits
        
        # File references
        file_pattern = r'([a-zA-Z0-9_\-./]+\.(py|js|html|css|json|yml|yaml|md|txt))'
        files = re.findall(file_pattern, text)
        references['files'] = [f[0] for f in files]
        
        return references
    
    def find_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate content similarity between two texts"""
        # Simple keyword-based similarity (can be enhanced with embeddings)
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def build_knowledge_graph(self):
        """Build the knowledge graph from database"""
        session = Session(engine)
        
        print("🔗 Building knowledge graph...")
        
        # Process documentation
        print("📄 Processing documentation...")
        sitemap_docs = session.query(Sitemap).all()
        for doc in tqdm(sitemap_docs, desc="Processing docs"):
            try:
                doc_id = f"doc_{doc.Id}"
                content = doc.Markdown or ""
                
                if not content.strip():
                    continue
                
                embedding = self.safe_embed(content)
                
                node = GraphNode(
                    id=doc_id,
                    type="doc",
                    content=content,
                    embedding=embedding,
                    metadata={
                        "url": doc.URL,
                        "site": doc.Site,
                        "title": getattr(doc, 'Title', ''),
                        "references": self.extract_references(content)
                    }
                )
                
                self.knowledge_graph.add_node(node)
                
                # Add to vectorstore
                if embedding:
                    sanitized_metadata = self.sanitize_metadata(node.metadata)
                    self.vectorstore.add_document(
                        doc_id=doc_id,
                        embedding=embedding,
                        document=content,
                        metadata=sanitized_metadata
                    )
                    
            except Exception as e:
                print(f"❌ Error processing doc {doc.Id}: {str(e)}")
        
        # Process issues and PRs
        print("🐛 Processing issues and PRs...")
        issues = session.query(Issue).all()
        for issue in tqdm(issues, desc="Processing issues"):
            try:
                issue_id = f"issue_{issue.Id}"
                content = f"Issue: {issue.Title}\n\n{issue.Body or ''}"
                
                embedding = self.safe_embed(content)
                
                issue_node = GraphNode(
                    id=issue_id,
                    type="issue",
                    content=content,
                    embedding=embedding,
                    metadata={
                        "url": issue.Url,
                        "title": issue.Title,
                        "state": getattr(issue, 'state', 'unknown'),
                        "references": self.extract_references(content)
                    }
                )
                
                self.knowledge_graph.add_node(issue_node)
                
                # Add to vectorstore
                if embedding:
                    sanitized_metadata = self.sanitize_metadata(issue_node.metadata)
                    self.vectorstore.add_document(
                        doc_id=issue_id,
                        embedding=embedding,
                        document=content,
                        metadata=sanitized_metadata
                    )
                
                # Process related PR if exists
                if issue.PR:
                    pr_id = f"pr_{issue.PR.Id}"
                    pr_content = f"Pull Request: {issue.PR.Title}\n\n{issue.PR.Body or ''}"
                    
                    pr_embedding = self.safe_embed(pr_content)
                    
                    pr_node = GraphNode(
                        id=pr_id,
                        type="pr",
                        content=pr_content,
                        embedding=pr_embedding,
                        metadata={
                            "url": issue.PR.Url,
                            "title": issue.PR.Title,
                            "state": getattr(issue.PR, 'state', 'unknown'),
                            "references": self.extract_references(pr_content)
                        }
                    )
                    
                    self.knowledge_graph.add_node(pr_node)
                    
                    # Add to vectorstore
                    if pr_embedding:
                        sanitized_pr_metadata = self.sanitize_metadata(pr_node.metadata)
                        self.vectorstore.add_document(
                            doc_id=pr_id,
                            embedding=pr_embedding,
                            document=pr_content,
                            metadata=sanitized_pr_metadata
                        )
                    
                    # Create edge between issue and PR
                    edge = GraphEdge(
                        source=issue_id,
                        target=pr_id,
                        relationship_type="related_to",
                        weight=1.0,
                        metadata={"type": "issue_pr_relation"}
                    )
                    self.knowledge_graph.add_edge(edge)
                    
            except Exception as e:
                print(f"❌ Error processing issue {issue.Id}: {str(e)}")
        
        # Process commits
#         print("🔨 Processing commits...")
#         commits = session.query(GitCommit).all()
#         for commit in tqdm(commits, desc="Processing commits"):
#             try:
#                 commit_id = f"commit_{commit.id}"
#                 content = f"""Commit: {commit.message}
# Author: {commit.author}
# Date: {commit.date}
# Files: {', '.join(commit.files)}
# Diff:
# {commit.diff}"""
                
#                 embedding = self.safe_embed(content)
                
#                 commit_node = GraphNode(
#                     id=commit_id,
#                     type="commit",
#                     content=content,
#                     embedding=embedding,
#                     metadata={
#                         "repo": commit.repo_name,
#                         "hash": commit.commit_hash,
#                         "author": commit.author,
#                         "date": str(commit.date),
#                         "files": commit.files,
#                         "references": self.extract_references(content)
#                     }
#                 )
                
#                 self.knowledge_graph.add_node(commit_node)
                
#                 # Add to vectorstore
#                 if embedding:
#                     sanitized_metadata = self.sanitize_metadata(commit_node.metadata)
#                     self.vectorstore.add_document(
#                         doc_id=commit_id,
#                         embedding=embedding,
#                         document=content,
#                         metadata=sanitized_metadata
#                     )
                    
#             except Exception as e:
#                 print(f"❌ Error processing commit {commit.id}: {str(e)}")
        
        # Build relationships between nodes
        print("🔗 Building relationships...")
        self.build_relationships()
        
        session.close()
        print(f"✅ Knowledge graph built with {len(self.knowledge_graph.nodes)} nodes and {len(self.knowledge_graph.edges)} edges")
    
    def build_reference_index(self) -> Dict[str, Set[str]]:
        """Build reference index for efficient relationship discovery"""
        reference_index = {
            'issues': {},
            'prs': {},
            'commits': {},
            'files': {},
            'authors': {},
            'keywords': {}
        }
        
        for node in self.knowledge_graph.nodes.values():
            refs = node.metadata.get('references', {})
            
            # Index by issue references
            for issue_id in refs.get('issues', []):
                if issue_id not in reference_index['issues']:
                    reference_index['issues'][issue_id] = set()
                reference_index['issues'][issue_id].add(node.id)
            
            # Index by PR references
            for pr_id in refs.get('prs', []):
                if pr_id not in reference_index['prs']:
                    reference_index['prs'][pr_id] = set()
                reference_index['prs'][pr_id].add(node.id)
            
            # Index by commit references
            for commit_hash in refs.get('commits', []):
                if commit_hash not in reference_index['commits']:
                    reference_index['commits'][commit_hash] = set()
                reference_index['commits'][commit_hash].add(node.id)
            
            # Index by file references
            for file_path in refs.get('files', []):
                if file_path not in reference_index['files']:
                    reference_index['files'][file_path] = set()
                reference_index['files'][file_path].add(node.id)
            
            # Index by author
            author = node.metadata.get('author')
            if author:
                if author not in reference_index['authors']:
                    reference_index['authors'][author] = set()
                reference_index['authors'][author].add(node.id)
            
            # Index by keywords (extract from content)
            keywords = self.extract_keywords(node.content)
            for keyword in keywords:
                if keyword not in reference_index['keywords']:
                    reference_index['keywords'][keyword] = set()
                reference_index['keywords'][keyword].add(node.id)
        
        return reference_index
    
    def extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        import re
        
        # Remove common words and extract meaningful terms
        common_words = {'the', 'is', 'at', 'which', 'on', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'from', 'up', 'into', 'over', 'after'}
        
        # Extract words, function names, class names, etc.
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text.lower())
        
        # Filter out common words and short words
        keywords = {word for word in words if word not in common_words and len(word) > 2}
        
        # Limit to top keywords to avoid noise
        return set(list(keywords)[:50])  # Top 50 keywords per document
    
    def get_relationship_candidates(self, reference_index: Dict[str, Dict[str, Set[str]]]) -> Set[Tuple[str, str]]:
        """Get candidate node pairs that likely have relationships"""
        candidates = set()
        
        # Find nodes sharing references
        for ref_type, ref_dict in reference_index.items():
            for ref_value, node_ids in ref_dict.items():
                if len(node_ids) > 1:  # Only if multiple nodes reference the same thing
                    node_list = list(node_ids)
                    for i in range(len(node_list)):
                        for j in range(i + 1, len(node_list)):
                            # Create ordered pair to avoid duplicates
                            pair = tuple(sorted([node_list[i], node_list[j]]))
                            candidates.add(pair)
        
        return candidates
    
    def should_create_relationship(self, node1_type: str, node2_type: str) -> bool:
        """Determine if relationship should be created between node types"""
        # Define allowed relationship patterns
        allowed_patterns = {
            #('commit', 'issue'),
            #('commit', 'pr'),
            ('issue', 'pr'),
            ('doc', 'issue'),
            ('doc', 'pr'),
            #('doc', 'commit'),
            #('commit', 'commit'),  # Same author relationships
            ('issue', 'issue'),    # Related issues
        }
        
        pattern = tuple(sorted([node1_type, node2_type]))
        return pattern in allowed_patterns
    
    def build_relationships(self):
        """Optimized relationship building using reference indexing"""
        print("🔗 Building reference index...")
        reference_index = self.build_reference_index()
        
        print("🔍 Finding relationship candidates...")
        candidates = self.get_relationship_candidates(reference_index)
        
        print(f"📊 Found {len(candidates)} potential relationships (reduced from {len(self.knowledge_graph.nodes)**2//2})")
        
        relationship_cache = {}
        
        for node1_id, node2_id in tqdm(candidates, desc="Building relationships"):
            # Check if we've already processed this pair
            cache_key = tuple(sorted([node1_id, node2_id]))
            if cache_key in relationship_cache:
                continue
            
            node1 = self.knowledge_graph.nodes.get(node1_id)
            node2 = self.knowledge_graph.nodes.get(node2_id)
            
            if not node1 or not node2:
                continue
            
            # Skip if relationship type not allowed
            if not self.should_create_relationship(node1.type, node2.type):
                continue
            
            # Skip if content is too small
            if len(node1.content) < 50 or len(node2.content) < 50:
                continue
            
            # Check if edge already exists
            if self.knowledge_graph.graph.has_edge(node1_id, node2_id):
                continue
            
            relationships = self.find_relationships(node1, node2)
            relationship_cache[cache_key] = relationships
            
            for rel_type, weight in relationships:
                # Only create edge if weight is significant
                if weight > 0.1:  # Threshold to avoid weak relationships
                    edge = GraphEdge(
                        source=node1_id,
                        target=node2_id,
                        relationship_type=rel_type,
                        weight=weight
                    )
                    self.knowledge_graph.add_edge(edge)
    
    def find_relationships(self, node1: GraphNode, node2: GraphNode) -> List[Tuple[str, float]]:
        """Optimized relationship finding between two nodes"""
        relationships = []
        
        # Get references for both nodes
        refs1 = node1.metadata.get('references', {})
        refs2 = node2.metadata.get('references', {})
        
        # 1. Direct reference relationships (highest weight)
        if node1.type == 'commit' and node2.type == 'issue':
            issue_num = node2.id.split('_')[1]
            if issue_num in refs1.get('issues', []):
                relationships.append(('fixes', 0.95))
                return relationships  # Strong relationship found, no need to check others
        
        if node1.type == 'commit' and node2.type == 'pr':
            pr_num = node2.id.split('_')[1]
            if pr_num in refs1.get('prs', []):
                relationships.append(('implements', 0.95))
                return relationships
        
        if node1.type == 'issue' and node2.type == 'pr':
            # Check if they reference each other
            issue_num = node1.id.split('_')[1]
            pr_num = node2.id.split('_')[1]
            if issue_num in refs2.get('issues', []) or pr_num in refs1.get('prs', []):
                relationships.append(('addresses', 0.9))
                return relationships
        
        # 2. File-based relationships (medium-high weight)
        files1 = set(refs1.get('files', []))
        files2 = set(refs2.get('files', []))
        if files1 and files2:
            file_overlap = len(files1.intersection(files2))
            total_files = len(files1.union(files2))
            if file_overlap > 0:
                overlap_ratio = file_overlap / total_files
                if overlap_ratio > 0.3:  # Significant overlap
                    relationships.append(('affects_same_files', min(overlap_ratio, 0.8)))
        
        # 3. Author-based relationships (medium weight)
        if (node1.type == 'commit' and node2.type == 'commit' and 
            node1.metadata.get('author') == node2.metadata.get('author')):
            relationships.append(('same_author', 0.5))
        
        # 4. Commit hash relationships (high weight)
        commits1 = set(refs1.get('commits', []))
        commits2 = set(refs2.get('commits', []))
        if commits1 and commits2:
            commit_overlap = len(commits1.intersection(commits2))
            if commit_overlap > 0:
                relationships.append(('references_same_commits', 0.8))
        
        # 5. Content similarity (lower weight, only if no other relationships found)
        if not relationships:
            similarity = self.find_content_similarity(node1.content, node2.content)
            if similarity > 0.4:  # Higher threshold for content similarity
                relationships.append(('similar_content', min(similarity, 0.6)))
        
        return relationships
    
    def query_with_graph_context(self, question: str, n_results: int = 3) -> str:
        """Enhanced query with graph-based context"""
        # Get initial results from vectorstore
        query_embedding = self.safe_embed(question)
        if query_embedding is None:
            return "❌ Could not generate embedding for your question."
        
        # Get similar documents
        try:
            results = self.vectorstore.query(query_embedding, n_results=n_results)
            if isinstance(results, dict) and 'documents' in results:
                documents = results['documents']
                doc_ids = results.get('ids', [])
            elif isinstance(results, list):
                documents = results
                doc_ids = []
            else:
                documents = []
                doc_ids = []
        except Exception as e:
            print(f"❌ Vectorstore query error: {str(e)}")
            return "❌ Error querying the knowledge base."
        
        if not documents:
            return "The available sources do not contain the answer."
        
        # Enhance with graph context
        enhanced_context = []
        graph_metadata = []
        
        for i, doc in enumerate(documents):
            enhanced_context.append(doc)
            
            # Get doc_id if available
            doc_id = doc_ids[i] if i < len(doc_ids) else None
            
            if doc_id and doc_id in self.knowledge_graph.nodes:
                # Get connected nodes with limits
                connected_nodes = self.knowledge_graph.get_connected_nodes(doc_id, max_depth=1, max_nodes=5)
                
                # Add context from connected nodes, prioritizing by relationship strength
                for connected_node in connected_nodes:
                    if connected_node.content not in enhanced_context:
                        # Truncate content to prevent context explosion
                        truncated_content = connected_node.content[:300] + "..." if len(connected_node.content) > 300 else connected_node.content
                        enhanced_context.append(f"[Connected {connected_node.type}]: {truncated_content}")
                        graph_metadata.append({
                            'type': connected_node.type,
                            'relationship': 'connected',
                            'metadata': connected_node.metadata
                        })
        
        context = "\n\n---\n\n".join(enhanced_context)
        
        # Enhanced prompt with graph context
        prompt = f"""## 🧠 Graph-Enhanced Developer Context Engine v2.0

> You are a **Graph-Enhanced Developer Context Engine AI**, leveraging a knowledge graph to provide comprehensive context from interconnected sources.
> Your role is to extract and synthesize information from documents, issues, PRs, and commits that are contextually related.

---

### 🔒 Constraints

* Use **only** the content in the `Context` section below.
* **Do not** make assumptions or use external knowledge.
* **Do not** hallucinate information.
* Prioritize information from directly connected sources.

---

### 🔗 Graph Context Available

The following context includes both directly relevant documents and related items from the knowledge graph:
- 📄 **Documentation** — feature design, usage, limitations
- 🐛 **Issues & PRs** — problem discussions, decisions, solutions
- 🔨 **Commits** — implementation details, changes, fixes
- 🔗 **Connected Items** — related content from the knowledge graph

---

### 🗃️ Enhanced Context (Documents + Connected Graph Nodes):

```
{context}
```

---

### ❓ Question:

```
{question}
```

---

### 📊 Graph Metadata:
{json.dumps(graph_metadata, indent=2) if graph_metadata else "No additional graph connections found."}

---

### ✅ Answer:
"""
        
        try:
            response = generate(model=config.OLLAMA_MODEL, prompt=prompt)
            return response["response"]
        except Exception as e:
            print(f"❌ Error generating response: {str(e)}")
            return "❌ Error generating response from the AI model."

def create_graph_chatbot(embedder, vectorstore):
    """Create enhanced chatbot with graph-based RAG"""
    graph_rag = GraphBasedRAG(embedder, vectorstore)
    
    # Build knowledge graph
    graph_rag.build_knowledge_graph()
    
    print("\n🤖 Welcome to the Graph-Enhanced Documentation Assistant!")
    print("Ask any question about the documentation (type 'exit' to quit)")
    print("Now with enhanced context from connected issues, PRs, and commits!\n")
    
    while True:
        try:
            print("👤 You:", end=" ")
            question = input().strip()
            if question.lower() in ['exit', 'quit', 'bye']:
                print("\n🤖 Goodbye! Have a great day!")
                break
            if not question:
                print("Please ask a question!")
                continue

            print("🤖 Thinking", end="")
            for _ in range(3):
                time.sleep(0.3)
                print(".", end="", flush=True)
            print("\n")

            answer = graph_rag.query_with_graph_context(question)
            print(f"\n🤖 Assistant: {answer}")
            print("\n" + "-"*50)

        except KeyboardInterrupt:
            print("\n\n🤖 Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

def run_graph_generator(question):
    """Run the graph-enhanced generator"""
    embedder = get_embedder("ollama")
    vectorstore = get_vectorstore("chroma", collection_name=config.CHROMA_COLLECTION_NAME)
    graph_rag = GraphBasedRAG(embedder, vectorstore)
    graph_rag.build_knowledge_graph()
    return graph_rag.query_with_graph_context(question)

def run_graph_embedder():
    """Run the graph-enhanced embedder"""
    embedder = get_embedder("ollama")
    vectorstore = get_vectorstore("chroma", collection_name=config.CHROMA_COLLECTION_NAME)
    graph_rag = GraphBasedRAG(embedder, vectorstore)
    graph_rag.build_knowledge_graph()

# Legacy functions for backward compatibility
def run_generator(question):
    return run_graph_generator(question)

def run_embedder():
    return run_graph_embedder()

def create_chatbot(embedder, vectorstore):
    return create_graph_chatbot(embedder, vectorstore)

run_embedder()