# Configuration Guide

## Quick Setup

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit required settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=your_password
NEO4J_DB=neo4j

# 3. Choose your embedding provider
EMBEDDING_PROVIDER=ollama  # or openai or sentence_transformer

# 4. Validate
python -m packages.config.cli validate
```

## Essential Settings

### Database (Required)
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=your_password
NEO4J_DB=neo4j
```

### Embedding Provider

**Option 1: Ollama (Local, Free)**
```bash
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIMENSION=1024
```

**Option 2: OpenAI (Cloud, API Key Required)**
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

**Option 3: Local Model (Free, CPU/GPU)**
```bash
EMBEDDING_PROVIDER=sentence_transformer
SENTENCE_TRANSFORMER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

## Environment

```bash
ENVIRONMENT=development  # development, staging, or production
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

## CLI Commands

```bash
# Check if config is valid
python -m packages.config.cli validate

# View current settings
python -m packages.config.cli summary

# Test database connection
python -m packages.config.cli test-connection

# See all feature flags
python -m packages.config.cli flags
```

## Using in Code

```python
from packages.config import Settings, is_feature_enabled, FeatureFlag

# Get settings
settings = Settings()
print(settings.NEO4J_URI)
print(settings.EMBEDDING_PROVIDER)

# Check environment
if settings.is_production():
    # production logic
    pass

# Use feature flags
if is_feature_enabled(FeatureFlag.ENABLE_VECTOR_SEARCH):
    results = search(query)
```

## Feature Flags

Control features without code changes. View all flags:
```bash
python -m packages.config.cli flags
```

Enable/disable in code:
```python
from packages.config import get_feature_flag_manager, FeatureFlag

manager = get_feature_flag_manager()
manager.enable(FeatureFlag.ENABLE_QUERY_CACHE)
manager.disable(FeatureFlag.ENABLE_TRACING)
```

## Common Issues

**"Configuration is invalid"**
- Check all required settings are in `.env`
- Run: `python -m packages.config.cli validate`

**"Cannot connect to Neo4j"**
- Verify Neo4j is running
- Run: `python -m packages.config.cli test-connection`

**"Feature not working"**
- Check feature flag status
- Run: `python -m packages.config.cli flags`

## Production Deployment

**Docker:**
```dockerfile
ENV ENVIRONMENT=production
ENV NEO4J_URI=bolt://neo4j:7687
ENV EMBEDDING_PROVIDER=openai
ENV OPENAI_API_KEY=${OPENAI_KEY}
```

**Kubernetes:**
Use ConfigMap for settings and Secret for passwords/keys.

---

That's it! For advanced options, see `packages/config/settings.py`.
