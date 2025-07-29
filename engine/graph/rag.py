"""
RAG system with graph-based context retrieval.
"""
import time
import json
from typing import List, Optional
from ollama import generate

from .builder import GraphBuilder
from .utils import sanitize_metadata
from config import settings

config = settings


class GraphBasedRAG:
    """Enhanced RAG system with graph-based context retrieval"""
    
    def __init__(self, embedder, vectorstore, graph_cache_path=f"./{config.CHROMA_PERSIST_DIRECTORY}/knowledge_graph.pkl"):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.graph_builder = GraphBuilder(embedder, vectorstore, graph_cache_path)
        self.knowledge_graph = self.graph_builder.knowledge_graph
    
    def safe_embed(self, text: str) -> Optional[List[float]]:
        """Safely embed text with error handling"""
        return self.graph_builder.safe_embed(text)
    
    def build_knowledge_graph(self, force_rebuild=False):
        """Build the knowledge graph from database"""
        self.graph_builder.build_knowledge_graph(force_rebuild)
        self.knowledge_graph = self.graph_builder.knowledge_graph
    
    def query_with_graph_context(self, question: str, n_results: int = 3) -> str:
        """Enhanced query with graph-based context"""
        start_time = time.time()
        
        # Get initial results from vectorstore
        start_embed = time.time()
        query_embedding = self.safe_embed(question)
        if query_embedding is None:
            return "❌ Could not generate embedding for your question."
        print(f"Embedding took {time.time() - start_embed:.2f} seconds")
        
        # Get similar documents
        start_doc_search = time.time()
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
        print(f"Doc Search took {time.time() - start_doc_search:.2f} seconds")
        
        if not documents:
            return "The available sources do not contain the answer."
        
        # Enhance with graph context
        enhanced_context = []
        graph_metadata = []
        get_nodes = time.time()
        
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
        
        print(f"nodes took {time.time() - get_nodes:.2f} seconds")
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
            chat_res = time.time()
            response = generate(model=config.OLLAMA_MODEL, prompt=prompt, think=False)
            print(f"chat took {time.time() - chat_res:.2f} seconds")
            return response["response"]
        except Exception as e:
            print(f"❌ Error generating response: {str(e)}")
            return "❌ Error generating response from the AI model."
