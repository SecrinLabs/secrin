# How DevSecrin Works

## Overview

DevSecrin operates as an intelligent layer between your development tools and AI, creating a unified knowledge graph that makes scattered information easily accessible through natural language queries.

## Core Pipeline

### 1. Data Collection (Collectors)

DevSecrin uses specialized collectors to gather information from various sources:

#### Git Repository Collector
```python
# Extracts from Git repositories
- Commit messages and metadata
- Code changes and diffs  
- Branch information
- Author and timestamp data
- File relationships and dependencies
```

**Data Collected**:
- Commit history with full context
- Code evolution patterns
- Author contribution patterns
- File modification frequency
- Branching and merging patterns

#### Issue Tracker Collector (Jira, GitHub Issues)
```python
# Gathers issue and project data
- Issue descriptions and comments
- Status changes and assignments
- Priority and label information
- Linked pull requests
- Resolution details
```

**Data Collected**:
- Issue lifecycle and resolution patterns
- Feature request to implementation mapping
- Bug report and fix correlations
- Team workload and assignment patterns
- Project milestone progress

#### Documentation Collector (Confluence, Notion, Web)
```python
# Scrapes documentation sources
- Wiki pages and articles
- API documentation
- Architecture diagrams
- Meeting notes and decisions
- Process documentation
```

**Data Collected**:
- Architectural decisions and rationale
- Process and workflow documentation
- API specifications and examples
- Team knowledge and best practices
- Historical decision records

#### Local Repository Analyzer
```python
# Analyzes local codebases
- Code structure and patterns
- Function and class relationships
- Import dependencies
- Configuration files
- Test coverage mapping
```

**Data Collected**:
- Code organization patterns
- Dependency relationships
- Configuration management
- Testing strategies
- Code quality metrics

### 2. Data Processing Pipeline

#### Content Parsing and Normalization
```python
class ContentProcessor:
    def parse_commit(self, commit):
        return {
            'id': commit.sha,
            'message': commit.message,
            'author': commit.author.name,
            'timestamp': commit.committed_date,
            'files_changed': [f.name for f in commit.files],
            'diff': commit.diff,
            'semantic_type': self.classify_commit(commit.message)
        }
    
    def parse_issue(self, issue):
        return {
            'id': issue.number,
            'title': issue.title,
            'description': issue.body,
            'labels': [l.name for l in issue.labels],
            'status': issue.state,
            'linked_commits': self.find_linked_commits(issue)
        }
```

#### Knowledge Graph Construction

DevSecrin builds a rich knowledge graph connecting various entities:

```python
class KnowledgeGraph:
    def build_relationships(self):
        # Code-to-Issue relationships
        self.link_commits_to_issues()
        
        # Code-to-Documentation relationships  
        self.link_code_to_docs()
        
        # Author-to-Component relationships
        self.build_expertise_graph()
        
        # Temporal relationships
        self.build_timeline_connections()
```

**Graph Entities**:
- **Code Entities**: Files, functions, classes, modules
- **Issue Entities**: Bugs, features, tasks, epics
- **People Entities**: Authors, reviewers, assignees
- **Documentation Entities**: Pages, sections, diagrams
- **Time Entities**: Releases, milestones, sprints

**Relationship Types**:
- `FIXES`: Issue → Commit
- `IMPLEMENTS`: Feature → Code
- `DOCUMENTS`: Documentation → Code
- `AUTHORED_BY`: Code → Person
- `DEPENDS_ON`: Code → Code
- `PART_OF`: Code → Module

#### Vector Embedding Generation

All textual content is converted to high-dimensional vectors for semantic search:

```python
class EmbeddingGenerator:
    def __init__(self, model="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model)
    
    def generate_embeddings(self, texts):
        # Generate semantic embeddings
        embeddings = self.model.encode(texts)
        
        # Store in ChromaDB
        self.vector_store.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=self.extract_metadata(texts)
        )
```

**Embedding Sources**:
- Commit messages and code comments
- Issue descriptions and comments
- Documentation content
- Code function/class descriptions
- API documentation

### 3. Storage Schema

DevSecrin uses a multi-modal storage approach:

#### PostgreSQL (Structured Data)
```sql
-- Core entities and relationships
CREATE TABLE commits (
    id VARCHAR PRIMARY KEY,
    message TEXT,
    author VARCHAR,
    timestamp TIMESTAMP,
    repository VARCHAR
);

CREATE TABLE issues (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    status VARCHAR,
    labels JSONB
);

CREATE TABLE relationships (
    source_type VARCHAR,
    source_id VARCHAR,
    target_type VARCHAR,
    target_id VARCHAR,
    relationship_type VARCHAR,
    confidence FLOAT
);
```

#### ChromaDB (Vector Storage)
```python
# Vector storage for semantic search
collection_schema = {
    'name': 'devsecrin_knowledge',
    'metadata': {
        'source_type': str,  # 'commit', 'issue', 'doc'
        'source_id': str,
        'timestamp': str,
        'author': str,
        'tags': list
    }
}
```

#### NetworkX Graph (Relationship Storage)
```python
# In-memory graph for fast traversal
knowledge_graph = nx.MultiDiGraph()

# Add nodes with rich attributes
knowledge_graph.add_node(
    'commit_abc123',
    type='commit',
    message='Fix authentication bug',
    author='john_doe',
    timestamp='2024-01-15'
)

# Add relationships
knowledge_graph.add_edge(
    'issue_456',
    'commit_abc123',
    relationship='fixes',
    confidence=0.95
)
```

### 4. AI Pipeline

#### Query Processing
```python
class QueryProcessor:
    def process_query(self, query):
        # 1. Intent classification
        intent = self.classify_intent(query)
        
        # 2. Entity extraction
        entities = self.extract_entities(query)
        
        # 3. Generate search strategy
        strategy = self.generate_strategy(intent, entities)
        
        return strategy
```

#### Context Retrieval (Hybrid RAG)

DevSecrin uses a sophisticated hybrid retrieval approach:

```python
class HybridRetriever:
    def retrieve_context(self, query, strategy):
        # Vector-based semantic search
        semantic_results = self.vector_search(query)
        
        # Graph-based relationship traversal
        graph_results = self.graph_traverse(strategy.entities)
        
        # Structured database queries
        structured_results = self.db_query(strategy.filters)
        
        # Combine and rank results
        context = self.merge_and_rank([
            semantic_results,
            graph_results, 
            structured_results
        ])
        
        return context
```

**Retrieval Strategies**:

1. **Semantic Search**: Find content similar to the query
2. **Graph Traversal**: Follow relationships to find connected information
3. **Temporal Search**: Find information from specific time periods
4. **Author Search**: Find content by specific contributors
5. **Component Search**: Find information about specific code components

#### Context Assembly
```python
class ContextAssembler:
    def assemble_context(self, retrieved_items, query):
        context = {
            'primary_sources': [],
            'related_code': [],
            'historical_context': [],
            'author_insights': [],
            'documentation': []
        }
        
        for item in retrieved_items:
            category = self.categorize_item(item)
            context[category].append(item)
        
        # Format for LLM consumption
        return self.format_for_llm(context, query)
```

#### LLM Generation

The assembled context is fed to the local Ollama model:

```python
class LLMGenerator:
    def generate_response(self, query, context):
        prompt = self.build_prompt(query, context)
        
        response = self.ollama_client.generate(
            model="deepseek-r1:1.5b",
            prompt=prompt,
            options={
                'temperature': 0.7,
                'max_tokens': 2048,
                'top_p': 0.9
            }
        )
        
        return self.post_process(response)
```

**Prompt Structure**:
```
System: You are DevSecrin, an AI assistant with deep knowledge of this codebase.

Context: 
{assembled_context}

Query: {user_query}

Instructions:
- Provide specific, actionable answers
- Reference source materials
- Include relevant code examples
- Explain the reasoning behind decisions
```

### 5. Real-time Updates

DevSecrin maintains freshness through incremental updates:

#### Change Detection
```python
class ChangeDetector:
    def detect_changes(self):
        # Git repository changes
        new_commits = self.git_collector.get_new_commits()
        
        # Issue tracker updates  
        updated_issues = self.issue_collector.get_updates()
        
        # Documentation changes
        doc_changes = self.doc_collector.get_changes()
        
        return self.prioritize_updates([
            new_commits, updated_issues, doc_changes
        ])
```

#### Incremental Processing
```python
class IncrementalProcessor:
    def process_updates(self, changes):
        for change in changes:
            # Update embeddings
            if change.affects_content:
                self.update_embeddings(change)
            
            # Update graph relationships  
            if change.affects_relationships:
                self.update_graph(change)
            
            # Update structured data
            self.update_database(change)
            
            # Notify connected clients
            self.notify_subscribers(change)
```

### 6. API Interface

DevSecrin exposes its functionality through multiple interfaces:

#### REST API
```python
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Process query through full pipeline
    response = await pipeline.process_query(
        query=request.message,
        context_limit=request.context_limit,
        sources=request.source_filters
    )
    
    return ChatResponse(
        message=response.text,
        sources=response.sources,
        confidence=response.confidence
    )
```

#### WebSocket API
```python
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    async for data in websocket.iter_text():
        query = json.loads(data)
        
        # Stream response in real-time
        async for chunk in pipeline.stream_response(query):
            await websocket.send_text(json.dumps(chunk))
```

#### Python SDK
```python
from devsecrin import DevSecrinClient

client = DevSecrinClient(api_url="http://localhost:8000")

# Simple query
response = client.ask("Why did we switch to React?")

# Advanced query with filters
response = client.ask(
    query="Show me recent authentication changes",
    sources=["git", "issues"],
    time_range="last_month",
    authors=["john_doe"]
)
```

## Performance Optimizations

### Caching Strategy
- **Query Result Caching**: Cache frequent queries
- **Embedding Caching**: Reuse embeddings for duplicate content
- **Graph Path Caching**: Cache common relationship paths
- **LLM Response Caching**: Cache responses for identical contexts

### Batch Processing
- **Embedding Generation**: Process multiple texts simultaneously
- **Database Operations**: Batch inserts and updates
- **Graph Updates**: Bulk relationship modifications
- **Index Maintenance**: Periodic optimization

### Memory Management
- **Lazy Loading**: Load data on demand
- **Connection Pooling**: Reuse database connections
- **Graph Pruning**: Remove stale relationships
- **Garbage Collection**: Clean up unused embeddings

## Monitoring and Observability

### Metrics Collection
```python
class MetricsCollector:
    def track_query(self, query, response_time, sources_used):
        self.metrics.increment('queries_total')
        self.metrics.histogram('query_duration', response_time)
        self.metrics.counter('sources_accessed', sources_used)
    
    def track_ingestion(self, source_type, items_processed):
        self.metrics.gauge(f'{source_type}_items_processed', items_processed)
        self.metrics.timestamp(f'{source_type}_last_update')
```

### Health Monitoring
- **Database Connectivity**: Monitor database health
- **Vector Store Status**: Check ChromaDB availability
- **LLM Responsiveness**: Monitor Ollama response times
- **Memory Usage**: Track system resource consumption
- **Data Freshness**: Monitor last update times per source