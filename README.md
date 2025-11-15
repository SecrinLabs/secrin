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
- Python 3.13
- Poetry

Setup:
1. Clone the repo and create your env file
	 - Copy `.env.example` to `.env` and fill values (see Configuration)
2. Install dependencies

```bash
poetry install
```

Run the API:

```bash
poetry run python run_api.py
```

Check it works:

```bash
# Welcome
curl http://localhost:8000/

# Health
curl http://localhost:8000/v1/health

# Connect a GitHub repo (sample)
curl -X POST http://localhost:8000/v1/connect/github \
	-H "Content-Type: application/json" \
	-d '{"repo_url": "https://github.com/facebook/react"}'
```

## Community & Support

Questions, ideas, or feedback? Please open an issue in this repository.
