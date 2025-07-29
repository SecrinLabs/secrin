"""
Graph builder for creating knowledge graphs from database content.
"""
import time
import os
from typing import Dict, List, Set, Tuple
from tqdm import tqdm
from sqlalchemy.orm import Session

from .knowledge_graph import KnowledgeGraph
from .models import GraphNode, GraphEdge
from .utils import extract_references, find_content_similarity, sanitize_metadata, extract_keywords
from service.src.models import engine
from service.src.models.Sitemap import Sitemap
from service.src.models.Issue import Issue


class GraphBuilder:
    """Builds knowledge graphs from database content"""
    
    def __init__(self, embedder, vectorstore, graph_cache_path):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.graph_cache_path = graph_cache_path
        self.knowledge_graph = KnowledgeGraph()
    
    def safe_embed(self, text: str) -> List[float]:
        """Safely embed text with error handling"""
        try:
            embedding = self.embedder.embed(text)
            if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], (list, tuple)):
                return embedding[0]
            return embedding
        except Exception as e:
            print(f"❌ Embedding error: {str(e)}")
            return None
    
    def build_knowledge_graph(self, force_rebuild=False):
        """Build the knowledge graph from database"""
        # If not forcing rebuild, try to load from cache first
        if not force_rebuild:
            if self.knowledge_graph.load_from_disk(self.graph_cache_path):
                if not self.should_rebuild_graph():
                    print("✅ Using cached knowledge graph")
                    return
                else:
                    print("🔄 Rebuilding knowledge graph due to data changes...")
        
        session = Session(engine)
        
        print("🔗 Building knowledge graph...")
        
        # Clear existing graph
        self.knowledge_graph = KnowledgeGraph()
        
        # Process documentation
        self._process_documentation(session)
        
        # Process issues and PRs
        self._process_issues(session)
        
        # Build relationships between nodes
        print("🔗 Building relationships...")
        self._build_relationships()
        
        session.close()
        print(f"✅ Knowledge graph built with {len(self.knowledge_graph.nodes)} nodes and {len(self.knowledge_graph.edges)} edges")
        
        # Save to cache
        os.makedirs(os.path.dirname(self.graph_cache_path), exist_ok=True)
        self.knowledge_graph.save_to_disk(self.graph_cache_path)
    
    def _process_documentation(self, session):
        """Process documentation from database"""
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
                        "references": extract_references(content)
                    }
                )
                
                self.knowledge_graph.add_node(node)
                
                # Add to vectorstore
                if embedding:
                    sanitized_metadata = sanitize_metadata(node.metadata)
                    self.vectorstore.add_document(
                        doc_id=doc_id,
                        embedding=embedding,
                        document=content,
                        metadata=sanitized_metadata
                    )
                    
            except Exception as e:
                print(f"❌ Error processing doc {doc.Id}: {str(e)}")
    
    def _process_issues(self, session):
        """Process issues and PRs from database"""
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
                        "references": extract_references(content)
                    }
                )
                
                self.knowledge_graph.add_node(issue_node)
                
                # Add to vectorstore
                if embedding:
                    sanitized_metadata = sanitize_metadata(issue_node.metadata)
                    self.vectorstore.add_document(
                        doc_id=issue_id,
                        embedding=embedding,
                        document=content,
                        metadata=sanitized_metadata
                    )
                
                # Process related PR if exists
                if issue.PR:
                    self._process_pr(issue)
                    
            except Exception as e:
                print(f"❌ Error processing issue {issue.Id}: {str(e)}")
    
    def _process_pr(self, issue):
        """Process a single PR related to an issue"""
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
                "references": extract_references(pr_content)
            }
        )
        
        self.knowledge_graph.add_node(pr_node)
        
        # Add to vectorstore
        if pr_embedding:
            sanitized_pr_metadata = sanitize_metadata(pr_node.metadata)
            self.vectorstore.add_document(
                doc_id=pr_id,
                embedding=pr_embedding,
                document=pr_content,
                metadata=sanitized_pr_metadata
            )
        
        # Create edge between issue and PR
        edge = GraphEdge(
            source=f"issue_{issue.Id}",
            target=pr_id,
            relationship_type="related_to",
            weight=1.0,
            metadata={"type": "issue_pr_relation"}
        )
        self.knowledge_graph.add_edge(edge)
    
    def should_rebuild_graph(self) -> bool:
        """Check if knowledge graph should be rebuilt based on data freshness"""
        try:
            if not os.path.exists(self.graph_cache_path):
                return True  # No cache exists, need to build
                
            # Check cache age (rebuild if older than 24 hours)
            cache_age = time.time() - os.path.getmtime(self.graph_cache_path)
            if cache_age > 24 * 3600:  # 24 hours
                print("🕐 Cache is older than 24 hours, rebuilding...")
                return True
                
            # Check if database has new content
            session = Session(engine)
            try:
                # Quick count of documents and issues
                doc_count = session.query(Sitemap).count()
                issue_count = session.query(Issue).count()
                
                # Count PRs (they are linked to issues, so approximately equal to issues)
                # Estimate total expected nodes: docs + issues + PRs (roughly same as issues)
                expected_nodes = doc_count + (issue_count * 2)  # issues + approx same number of PRs
                
                # Check if counts have changed significantly
                current_nodes = len(self.knowledge_graph.nodes)
                
                # Allow 20% variance for PR variations
                threshold = max(20, int(expected_nodes * 0.2))
                
                if abs(current_nodes - expected_nodes) > threshold:
                    print(f"📊 Data size changed significantly ({current_nodes} vs ~{expected_nodes} expected, threshold: {threshold}), rebuilding...")
                    return True
                    
            finally:
                session.close()
                
            return False
        except Exception as e:
            print(f"⚠️ Error checking rebuild status: {str(e)}")
            return True  # Err on the side of rebuilding
    
    def _build_relationships(self):
        """Optimized relationship building using reference indexing"""
        print("🔗 Building reference index...")
        reference_index = self._build_reference_index()
        
        print("🔍 Finding relationship candidates...")
        candidates = self._get_relationship_candidates(reference_index)
        
        print(f"📊 Found {len(candidates)} potential relationships")
        
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
            if not self._should_create_relationship(node1.type, node2.type):
                continue
            
            # Skip if content is too small
            if len(node1.content) < 50 or len(node2.content) < 50:
                continue
            
            # Check if edge already exists
            if self.knowledge_graph.graph.has_edge(node1_id, node2_id):
                continue
            
            relationships = self._find_relationships(node1, node2)
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
    
    def _build_reference_index(self) -> Dict[str, Dict[str, Set[str]]]:
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
            keywords = extract_keywords(node.content)
            for keyword in keywords:
                if keyword not in reference_index['keywords']:
                    reference_index['keywords'][keyword] = set()
                reference_index['keywords'][keyword].add(node.id)
        
        return reference_index
    
    def _get_relationship_candidates(self, reference_index: Dict[str, Dict[str, Set[str]]]) -> Set[Tuple[str, str]]:
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
    
    def _should_create_relationship(self, node1_type: str, node2_type: str) -> bool:
        """Determine if relationship should be created between node types"""
        # Define allowed relationship patterns
        allowed_patterns = {
            ('issue', 'pr'),
            ('doc', 'issue'),
            ('doc', 'pr'),
            ('issue', 'issue'),    # Related issues
        }
        
        pattern = tuple(sorted([node1_type, node2_type]))
        return pattern in allowed_patterns
    
    def _find_relationships(self, node1: GraphNode, node2: GraphNode) -> List[Tuple[str, float]]:
        """Optimized relationship finding between two nodes"""
        relationships = []
        
        # Get references for both nodes
        refs1 = node1.metadata.get('references', {})
        refs2 = node2.metadata.get('references', {})
        
        # 1. Direct reference relationships (highest weight)
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
        
        # 3. Commit hash relationships (high weight)
        commits1 = set(refs1.get('commits', []))
        commits2 = set(refs2.get('commits', []))
        if commits1 and commits2:
            commit_overlap = len(commits1.intersection(commits2))
            if commit_overlap > 0:
                relationships.append(('references_same_commits', 0.8))
        
        # 4. Content similarity (lower weight, only if no other relationships found)
        if not relationships:
            similarity = find_content_similarity(node1.content, node2.content)
            if similarity > 0.4:  # Higher threshold for content similarity
                relationships.append(('similar_content', min(similarity, 0.6)))
        
        return relationships
