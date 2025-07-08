# DevSecrin 🧠📘

DevSecrin (Developer Secret Engine) is an AI-powered **Developer Context Engine** designed to enhance the reasoning and productivity of developers by bringing deep, structured historical knowledge from code, tickets, and documentation directly into their workflow.

> "Every line of code has a story. DevSecrin helps you remember why it was written."

## 🚀 Overview

### System Architecture
![devsecrin_arch](https://github.com/user-attachments/assets/3bf40c77-2d7a-49de-a016-c22dcc1ede52)

Modern software teams are overwhelmed with disconnected tools—Git, Jira, Confluence, Notion, and more. Developers often struggle to recall the rationale behind code changes, architecture decisions, or feature implementations. DevSecrin solves this by creating a unified context layer that feeds this collective knowledge into AI systems—so developers don't just see *what* changed, but *why* it changed.

## 🧩 Core Features

### 🔌 Multi-source Integration

DevSecrin ingests and unifies data from:

* **Git Repositories**: Parses commit history, diffs, and PR metadata
* **Issue Trackers** (Jira, GitHub Issues): Understands the intent and scope behind changes
* **Documentation** (Confluence, Notion, Sitemaps): Captures structured knowledge and decisions
* **Local Repositories**: Enables offline codebase analysis

### 📚 Contextual Embeddings

* All ingested data is vectorized using embeddings for semantic understanding
* Powered by Retrieval-Augmented Generation (RAG), enabling intelligent, memory-rich chat

### 💬 Intelligent QA Layer

* Ask natural language questions like:

  * "Why did we switch from Redis to Kafka last quarter?"
  * "What were the key design decisions in the payment module?"
  * "Has this function been changed recently, and why?"
* The engine retrieves relevant context (code, commit, docs) and feeds it to the LLM for precise answers

### 🛠️ Local-first Developer Tooling

* Electron-based app (planned) for desktop usability
* Works even without cloud sync
* Git-backed journaling to record architecture decisions and local history

## 🧱 Tech Stack

* **Backend**: FastAPI, Python, Postgres
* **Embedding & Retrieval**: Ollama, Chroma
* **Frontend**: Next.js (planned), TailwindCSS
* **Integrations**: GitHub, Confluence, Jira, Local FS
* **RAG**: Custom pipeline for semantic search and context composition

## 🛣️ Roadmap

### v0.1 (MVP - In Progress)

* [x] GitHub integration with token-based auth
* [x] Confluence and sitemap ingestion
* [x] ChromaDB + Ollama RAG backend
* [x] API for question answering
* [x] Basic frontend for integration
* [ ] Task run tracker and scheduler

### v0.2

* [ ] DevJournal (local note-taking for decisions)
* [ ] VS Code plugin for context injection
* [ ] Workspace-based sync across devices

## 🧠 Philosophy

DevSecrin is built on the belief that:

* **Context is everything** for developer productivity
* **AI must be grounded in history**, not hallucinations
* **Open tooling** and transparency win in the long term

## 📦 Getting Started

### Prerequisites
Install Ollama and the deepseek-r1:1.5b model locally

```bash
# Clone the repo
$ git clone https://github.com/{yourusername}/devsecrin.git
$ cd devsecrin

# Setup Python environment
$ python3 -m venv venv
$ source venv/bin/activate
$ source venv/bin/activate

# install node requirement
$ pnpm install

# run server
$ pnpm run devsecrin
```

## 📄 License

MIT License

## 🙌 Contributing

PRs, suggestions, and architecture feedback are welcome. The vision for DevSecrin is big—help us make it global.

## 📫 Contact

Built with 💻 by Jenil Savani. Connect on [LinkedIn](https://www.linkedin.com/in/jenil-savani/) or [GitHub](https://github.com/jenilsavani9).

---

> *"In a world full of files, functions, and frameworks—context is your compass. DevSecrin helps you find your way."*
