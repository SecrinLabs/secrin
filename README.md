![Secrin Banner](/public/brand_banner.png)

<p align="center">
<strong>Don't waste time on Q&A. Search less. Build more.</strong><br>
Your engineering knowledge deserves better than scattered repos, Slack threads, and tribal memory.
</p>

<p align="center">
  <a href="https://secrinlabs.com"><strong>Website</strong></a> ·
  <a href="https://github.com/secrinlabs/secrin">GitHub</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AI%20Native-Knowledge%20Graph-blue" />
  <img src="https://img.shields.io/github/stars/secrinlabs/secrin" />
  <img src="https://img.shields.io/github/license/secrinlabs/secrin" />
  <img src="https://img.shields.io/github/commit-activity/m/secrinlabs/secrin" />
</p>

---

## What is Secrin?

Secrin indexes any codebase into a **Neo4j knowledge graph**, generates plain-English summaries for every function, class, and file via your LLM of choice, and produces a searchable Markdown wiki — fully automated, living alongside your code.

```
secrin init                          # interactive setup → .secrin.yml
secrin graph build --repo .          # parse repo → Neo4j graph
secrin analyze                       # LLM summaries + vector embeddings
secrin domains                       # extract business domain concepts
secrin generate                      # write docs/wiki/
secrin chat "how does auth work?"    # Q&A from the graph
```

> Teams don't slow down because they forget how to code.
> They slow down because they forget *why* the code exists.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Commands](#commands)
- [Architecture](#architecture)
- [Git Hook](#git-hook)
- [Team Workflow](#team-workflow)
- [Contributing](#contributing)

---

## Features

| Feature | Description |
|---|---|
| **Code knowledge graph** | Neo4j graph of Files, Modules, Functions, Classes with CALLS, IMPORTS, and INHERITS edges |
| **LLM summaries** | Plain-English description of every node via Ollama, OpenAI, or Anthropic |
| **Vector search** | Semantic KNN search over embeddings stored directly in Neo4j vector indexes |
| **Hybrid search** | Combines vector KNN with 1-hop Cypher graph traversal for better recall |
| **Domain extraction** | Identifies business concepts (auth, payments, …) and links them to code nodes |
| **Wiki generation** | Markdown wiki with per-module pages, domain pages, and Mermaid architecture diagrams |
| **Chat Q&A** | Ask architecture questions; answers grounded in graph context, not hallucinated |
| **Git hook** | Post-commit hook auto-updates graph and wiki after every commit |
| **Multi-LLM** | Ollama (local) · OpenAI · Anthropic — switchable per repo via `.secrin.yml` |
| **Dashboard** | `secrin status` shows graph stats, coverage %, last analysis, wiki state |

---

## Installation

**Requirements:** Python ≥ 3.11, [Poetry](https://python-poetry.org/), Neo4j 5+

```bash
git clone https://github.com/secrinlabs/secrin
cd secrin
poetry install

# Start Neo4j (Docker — included in docker-compose.yml)
docker compose up neo4j -d

# Verify infrastructure
poetry run python scripts/verify.py
```

### Local LLM (Ollama)

```bash
# Install Ollama → https://ollama.com
ollama pull llama3               # completion model
ollama pull nomic-embed-text     # embedding model (768d)
```

### Cloud LLM

Set keys in `.env` before running `secrin init`:

```bash
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Quick Start

### 1 — Initialize

```bash
cd your-project
secrin init
```

The interactive wizard asks for your LLM provider, Neo4j connection, and wiki output directory,
then writes `.secrin.yml`. Commit this file so teammates share the same defaults.

```
? LLM provider (ollama / openai / anthropic): ollama
? Ollama host [http://localhost:11434]:
? Ollama model [llama3]:
? Embed model [nomic-embed-text]:
? Neo4j URI [bolt://localhost:7687]:
? Neo4j username [neo4j]:
? Neo4j password:
? Neo4j database [neo4j]:
? Wiki output directory [docs/wiki]:

✓ Created .secrin.yml
✓ Updated .env  (NEO4J_PASS)
✓ Connected to Neo4j  (0 nodes found)
✓ Connected to Ollama  (llama3 available)

Run `secrin graph build --repo <url-or-path>` to index your repo.
```

### 2 — Build the graph

```bash
# Current directory
secrin graph build --repo .

# GitHub URL (cloned automatically)
secrin graph build --repo https://github.com/your-org/your-repo
```

### 3 — Generate summaries and embeddings

```bash
secrin analyze
```

Runs in two phases:

```
⠋ [Phase 1] Summarizing  ollama / llama3  Function 48  Class 12  File 21
⠋ [Phase 2] Embedding    nomic-embed-text  Function 48  Class 12  File 21

╭─ Analysis Results ────────────────────────╮
│ Label      Summarized   Embedded           │
│ Function   612          612                │
│ Class      111          111                │
│ File       124          124                │
╰────────────────────────────────────────────╯

✓ Total nodes with summary: 847
```

### 4 — Generate the wiki

```bash
# Optional: identify business domain concepts
secrin domains

# Generate Markdown wiki
secrin generate
```

Output at `docs/wiki/`:

```
docs/wiki/
├── README.md              ← auto-linked index
├── architecture.md        ← system overview + Mermaid import graph
├── modules/
│   ├── packages-cli.md
│   └── packages-config.md
└── domains/
    ├── authentication.md
    └── payment-processing.md
```

### 5 — Search and chat

```bash
# Semantic search
secrin search "rate limiting"
secrin search "JWT token validation" --verbose

# Architecture Q&A — grounded in the graph, not hallucinated
secrin chat "how does authentication work?"
secrin chat "where is the payment webhook handler?"
secrin chat "what calls the user repository?"
```

### 6 — Check status

```bash
secrin status
```

```
Secrin  v2  your-project
──────────────────────────────────────────────────────────────
Graph          847 nodes · 2,341 edges
               Files 124  ·  Functions 612  ·  Classes 111  ·  Modules 4
Domains        8 domain entities identified
Coverage       98% summarized  ·  96% embedded
Last analyzed  2 hours ago  (main @ a3f9c12)
Neo4j          ● connected  bolt://localhost:7687
Wiki           docs/wiki/  ·  47 pages
.secrin.yml    ✓  ollama / llama3
──────────────────────────────────────────────────────────────
```

---

## Configuration

### `.secrin.yml` — team config (commit this)

```yaml
llm:
  provider: ollama          # ollama | openai | anthropic
  model: llama3
  embed_model: nomic-embed-text
  base_url: http://localhost:11434   # Ollama only; omitted for cloud providers

neo4j:
  uri: bolt://localhost:7687        # or AuraDB URI for a shared team graph
  username: neo4j
  database: neo4j

wiki:
  output_dir: docs/wiki
  languages:
    - python
```

### `.env` — secrets (never commit)

```bash
NEO4J_PASS=your_password

# Cloud LLM providers (set whichever you use)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional overrides (if you don't use .secrin.yml)
LLM_PROVIDER=ollama
LLM_MODEL_OLLAMA=qwen2.5-coder:0.5b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
```

### Provider comparison

| Provider | Completions | Embeddings | Best for |
|---|---|---|---|
| **Ollama** | local model | local model | Offline / no API cost |
| **OpenAI** | GPT-4o-mini | text-embedding-3-small | Best quality + speed |
| **Anthropic** | Claude Haiku | Ollama fallback* | Best reasoning quality |

\* Anthropic has no embeddings API. When `provider: anthropic`, embed calls route to Ollama automatically.

---

## Commands

### Setup & monitoring

| Command | Description |
|---|---|
| `secrin init` | Interactive wizard — creates `.secrin.yml` |
| `secrin init --force` | Reconfigure existing setup |
| `secrin status` | Dashboard: node counts, coverage, wiki state |

### Graph pipeline

| Command | Description |
|---|---|
| `secrin graph build --repo <url\|path>` | Parse repo and build Neo4j graph |
| `secrin graph visualize` | Open Neo4j Browser (or AuraDB console) |
| `secrin analyze` | LLM summaries + vector embeddings |
| `secrin analyze --skip-embed` | Summaries only (no embeddings) |
| `secrin analyze --batch-size 25` | Smaller batches for slow machines |
| `secrin domains` | Extract business domain entities |
| `secrin domains --sample 500` | Sample more nodes for better coverage |

### Wiki

| Command | Description |
|---|---|
| `secrin generate` | Write `docs/wiki/` from Neo4j |
| `secrin generate --skip-llm` | Fast mode — no narrative summaries |
| `secrin generate --output path/to/dir` | Custom output directory |
| `secrin diff` | Dry run: show what would change |

### Search & chat

| Command | Description |
|---|---|
| `secrin search "<query>"` | Hybrid vector + graph search |
| `secrin search "<query>" --verbose` | Full summaries in results |
| `secrin search "<query>" --top 10` | Return top 10 results |
| `secrin chat "<question>"` | Architecture Q&A from the graph |
| `secrin chat "<question>" --top 12` | More context nodes |

### Automation

| Command | Description |
|---|---|
| `secrin install-hooks` | Install git post-commit hook |
| `secrin post-commit` | Incremental graph + wiki update (called by hook) |
| `secrin post-commit --skip-wiki` | Update graph only |

---

## Architecture

```
secrin/
├── packages/
│   ├── cli/                         # Main CLI package
│   │   ├── agents/
│   │   │   ├── llm_client.py        # Unified Ollama / OpenAI / Anthropic client
│   │   │   ├── summarizer.py        # Node summarization agent
│   │   │   ├── embedder.py          # Vector embedding agent
│   │   │   ├── domain_extractor.py  # Business domain extraction
│   │   │   └── wiki_writer.py       # Markdown wiki generator
│   │   ├── commands/
│   │   │   ├── init.py              # Interactive setup wizard
│   │   │   ├── status.py            # Live dashboard
│   │   │   ├── chat.py              # Architecture Q&A
│   │   │   ├── diff.py              # Wiki dry-run diff
│   │   │   ├── graph.py             # graph build + visualize
│   │   │   ├── analyze.py           # summarize + embed (Rich progress)
│   │   │   ├── search.py            # hybrid search
│   │   │   ├── domains.py           # domain extraction
│   │   │   ├── generate.py          # wiki generation
│   │   │   └── hooks.py             # post-commit + install-hooks
│   │   ├── core/
│   │   │   ├── secrin_yml.py        # .secrin.yml loader/writer
│   │   │   ├── parser.py            # Tree-sitter AST parser (py/ts/js/tsx/jsx)
│   │   │   ├── cloner.py            # Git repo cloner
│   │   │   └── config.py            # Legacy .secrin/config.yaml
│   │   ├── graph/
│   │   │   ├── neo4j_client.py      # Neo4j driver wrapper
│   │   │   ├── builder.py           # Batch graph construction (UNWIND MERGE)
│   │   │   ├── schema.py            # Constraints + vector indexes
│   │   │   └── diff.py              # Incremental update engine (git-diff aware)
│   │   └── search/
│   │       ├── vector_search.py     # Neo4j KNN vector search
│   │       ├── graph_search.py      # 1-hop Cypher traversal
│   │       └── hybrid.py            # Vector + graph merge + re-rank
│   └── config/
│       └── settings.py              # Pydantic settings (env / .env)
└── docker-compose.yml               # Neo4j + Qdrant + Redis
```

### Neo4j schema

**Node labels:** `Module` · `File` · `Class` · `Function` · `DomainEntity`

**Relationships:**

| Relationship | From → To | Meaning |
|---|---|---|
| `CONTAINS` | Module → File | File belongs to module |
| `DEFINES` | File → Class / Function | File declares the node |
| `CONTAINS` | Class → Function | Method belongs to class |
| `CALLS` | Function → Function | Direct call edge |
| `IMPORTS` | File → File | Import/require dependency |
| `INHERITS` | Class → Class | Inheritance (Python) |
| `IMPLEMENTS_DOMAIN` | Any → DomainEntity | Code implements a business concept |

**LLM-populated properties** (set by `secrin analyze`):

| Property | Type | Description |
|---|---|---|
| `summary` | String | Plain-English description |
| `summary_embedding` | Float[] | Vector for semantic search |
| `summarized_at` | String | ISO-8601 timestamp |

### Supported languages

Python · TypeScript · TSX · JavaScript · JSX

---

## Git Hook

Install once per repo, then never think about it again:

```bash
secrin install-hooks
```

After every `git commit`, Secrin automatically:
1. Detects changed files via `git diff-tree HEAD`
2. Deletes stale Neo4j nodes for changed/deleted files
3. Re-parses and re-inserts updated files
4. Re-summarizes and re-embeds new nodes
5. Regenerates affected module pages + `architecture.md`

```bash
# Uninstall
rm .git/hooks/post-commit
```

---

## Team Workflow

```bash
# One-time per repo (run by one engineer, commit the result)
secrin init
secrin graph build --repo .
secrin analyze
secrin domains
secrin generate
git add .secrin.yml docs/wiki/
git commit -m "feat: add Secrin knowledge graph"
secrin install-hooks

# Every engineer after cloning
git clone https://github.com/your-org/your-repo
secrin init           # loads defaults from .secrin.yml, just fill in password
secrin status         # verify everything is connected
secrin chat "where should I add the new billing endpoint?"
```

**Shared Neo4j (AuraDB):** set the AuraDB URI in `.secrin.yml` and everyone shares the same
up-to-date graph. Only the person running `secrin analyze` needs an LLM API key.

---

## Contributing

```bash
poetry install
poetry run secrin --help
poetry run python scripts/verify.py   # check Neo4j + Qdrant + Gateway

# Run a specific command
poetry run secrin graph build --repo .
poetry run secrin analyze
poetry run secrin chat "how does X work?"
```

To add a language, extend `packages/cli/core/parser.py` with the new tree-sitter binding
and add its extension to `SUPPORTED_EXTENSIONS`.

Open an issue, propose a feature, or jump into the codebase.

> The goal isn't just to index code.
> The goal is to remember as a team.
