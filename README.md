# Secrin

Secrin is a personal intelligence layer for engineering teams. It stitches together context scattered across GitHub, issues, docs, and chat into answers you can use right now.

> Developers don’t lack information, they lack a way to recombine it fast. Secrin reduces context fragmentation by capturing signals (code, PRs, commits, comments, docs), indexing them, and making them queryable in real time.

## What it does

- Acts like a memory extension for your team ask about code, decisions, and history, get precise context back
- Local‑first, developer‑first RAG engine with a knowledge graph backbone
- Pluggable connectors (starting with GitHub) that turn repos and activity into queryable context

## How it works (at a glance)

- Ingests repositories and activity, parses structure with Tree‑sitter, and stores relationships in Neo4j
- A FastAPI backend exposes versioned routes (v1) and simple connectors (e.g., GitHub)
- Designed to grow into a living knowledge graph across your engineering tools

## Quickstart

Prerequisites:
- Python 3.13+
- Poetry
- Neo4j database

Setup:
```bash
# 1. Clone and install
git clone https://github.com/SecrinLabs/secrin.git
cd secrin
poetry install

# 2. Configure (see CONFIGURATION.md)
cp .env.example .env
# Edit .env with your Neo4j details

# 3. Validate setup
python -m packages.config.cli validate

# 4. Run API
poetry run python run_api.py
```

Verify:
```bash
# Health check
curl http://localhost:8000/v1/health

# Config summary
python -m packages.config.cli summary
```

📖 **Configuration:** See [CONFIGURATION.md](CONFIGURATION.md) for setup details.

## Community & Support

Questions, ideas, or feedback? Please open an issue in this repository.
