import time
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from tqdm import tqdm
from sqlalchemy.orm import Session
from packages.ai.embeddings.factory import get_embedder
from packages.ai.retriever.factory import get_vectorstore
from packages.models import engine
from packages.models.sitemap import Sitemap
from packages.models.githubissue import Issue
from packages.models.gitcommit import GitCommit
from ollama import generate
import networkx as nx
import json

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
    
    def get_connected_nodes(self, node_id: str, max_depth: int = 2) -> List[GraphNode]:
        """Get all nodes connected to a given node within max_depth"""
        if node_id not in self.graph:
            return []
        
        connected_ids = set()
        current_level = {node_id}
        
        for depth in range(max_depth):
            next_level = set()
            for current_id in current_level:
                neighbors = set(self.graph.neighbors(current_id)) | set(self.graph.predecessors(current_id))
                next_level.update(neighbors - connected_ids)
                connected_ids.update(neighbors)
            current_level = next_level
            
        return [self.nodes[nid] for nid in connected_ids if nid in self.nodes]
    
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
                doc_id = f"doc_{doc.id}"
                content = doc.markdown or ""
                
                if not content.strip():
                    continue
                
                embedding = self.safe_embed(content)
                
                node = GraphNode(
                    id=doc_id,
                    type="doc",
                    content=content,
                    embedding=embedding,
                    metadata={
                        "url": doc.url,
                        "site": doc.site,
                        "title": getattr(doc, 'title', ''),
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
                print(f"❌ Error processing doc {doc.id}: {str(e)}")
        
        # Process issues and PRs
        print("🐛 Processing issues and PRs...")
        issues = session.query(Issue).all()
        for issue in tqdm(issues, desc="Processing issues"):
            try:
                issue_id = f"issue_{issue.id}"
                content = f"Issue: {issue.title}\n\n{issue.body or ''}"
                
                embedding = self.safe_embed(content)
                
                issue_node = GraphNode(
                    id=issue_id,
                    type="issue",
                    content=content,
                    embedding=embedding,
                    metadata={
                        "url": issue.url,
                        "title": issue.title,
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
                if issue.pull_request:
                    pr_id = f"pr_{issue.pull_request.id}"
                    pr_content = f"Pull Request: {issue.pull_request.title}\n\n{issue.pull_request.body or ''}"
                    
                    pr_embedding = self.safe_embed(pr_content)
                    
                    pr_node = GraphNode(
                        id=pr_id,
                        type="pr",
                        content=pr_content,
                        embedding=pr_embedding,
                        metadata={
                            "url": issue.pull_request.url,
                            "title": issue.pull_request.title,
                            "state": getattr(issue.pull_request, 'state', 'unknown'),
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
                print(f"❌ Error processing issue {issue.id}: {str(e)}")
        
        # Process commits
        print("🔨 Processing commits...")
        commits = session.query(GitCommit).all()
        for commit in tqdm(commits, desc="Processing commits"):
            try:
                commit_id = f"commit_{commit.id}"
                content = f"""Commit: {commit.message}
Author: {commit.author}
Date: {commit.date}
Files: {', '.join(commit.files)}
Diff:
{commit.diff}"""
                
                embedding = self.safe_embed(content)
                
                commit_node = GraphNode(
                    id=commit_id,
                    type="commit",
                    content=content,
                    embedding=embedding,
                    metadata={
                        "repo": commit.repo_name,
                        "hash": commit.commit_hash,
                        "author": commit.author,
                        "date": str(commit.date),
                        "files": commit.files,
                        "references": self.extract_references(content)
                    }
                )
                
                self.knowledge_graph.add_node(commit_node)
                
                # Add to vectorstore
                if embedding:
                    sanitized_metadata = self.sanitize_metadata(commit_node.metadata)
                    self.vectorstore.add_document(
                        doc_id=commit_id,
                        embedding=embedding,
                        document=content,
                        metadata=sanitized_metadata
                    )
                    
            except Exception as e:
                print(f"❌ Error processing commit {commit.id}: {str(e)}")
        
        # Build relationships between nodes
        print("🔗 Building relationships...")
        self.build_relationships()
        
        session.close()
        print(f"✅ Knowledge graph built with {len(self.knowledge_graph.nodes)} nodes and {len(self.knowledge_graph.edges)} edges")
    
    def build_relationships(self):
        """Build relationships between nodes based on content and references"""
        nodes = list(self.knowledge_graph.nodes.values())
        
        for i, node1 in enumerate(tqdm(nodes, desc="Building relationships")):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                relationships = self.find_relationships(node1, node2)
                
                for rel_type, weight in relationships:
                    edge = GraphEdge(
                        source=node1.id,
                        target=node2.id,
                        relationship_type=rel_type,
                        weight=weight
                    )
                    self.knowledge_graph.add_edge(edge)
    
    def find_relationships(self, node1: GraphNode, node2: GraphNode) -> List[Tuple[str, float]]:
        """Find relationships between two nodes"""
        relationships = []
        
        # Reference-based relationships
        refs1 = node1.metadata.get('references', {})
        refs2 = node2.metadata.get('references', {})
        
        # Check for direct references
        if node1.type == 'commit' and node2.type == 'issue':
            # Check if commit message references issue
            issue_num = node2.id.split('_')[1]
            if issue_num in refs1.get('issues', []):
                relationships.append(('fixes', 0.9))
        
        # File-based relationships
        files1 = set(refs1.get('files', []))
        files2 = set(refs2.get('files', []))
        if files1 and files2:
            file_overlap = len(files1.intersection(files2)) / len(files1.union(files2))
            if file_overlap > 0.3:
                relationships.append(('affects_same_files', file_overlap))
        
        # Content similarity
        similarity = self.find_content_similarity(node1.content, node2.content)
        if similarity > 0.2:
            relationships.append(('similar_content', similarity))
        
        # Author-based relationships (for commits)
        if (node1.type == 'commit' and node2.type == 'commit' and 
            node1.metadata.get('author') == node2.metadata.get('author')):
            relationships.append(('same_author', 0.5))
        
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
                # Get connected nodes
                connected_nodes = self.knowledge_graph.get_connected_nodes(doc_id, max_depth=1)
                
                # Add context from connected nodes
                for connected_node in connected_nodes[:2]:  # Limit to avoid too much context
                    if connected_node.content not in enhanced_context:
                        enhanced_context.append(f"[Connected {connected_node.type}]: {connected_node.content[:500]}...")
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
            response = generate(model="deepseek-r1:1.5b", prompt=prompt)
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
    vectorstore = get_vectorstore("chroma", collection_name="docs")
    graph_rag = GraphBasedRAG(embedder, vectorstore)
    graph_rag.build_knowledge_graph()
    return graph_rag.query_with_graph_context(question)

def run_graph_embedder():
    """Run the graph-enhanced embedder"""
    embedder = get_embedder("ollama")
    vectorstore = get_vectorstore("chroma", collection_name="docs")
    graph_rag = GraphBasedRAG(embedder, vectorstore)
    graph_rag.build_knowledge_graph()

# Legacy functions for backward compatibility
def run_generator(question):
    return run_graph_generator(question)

def run_embedder():
    return run_graph_embedder()

def create_chatbot(embedder, vectorstore):
    return create_graph_chatbot(embedder, vectorstore)