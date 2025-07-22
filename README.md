# 🧠 DevSecrin

*"Every line of code has a story. DevSecrin helps you remember why it was written."*

DevSecrin is a lightweight Developer Context Engine that helps you ask **why** behind your codebase—by connecting Git commits, issues, and documentation through AI reasoning and graph-based retrieval.

## 🌟 System Architecture

![devsecrin_arch](https://github.com/user-attachments/assets/3bf40c77-2d7a-49de-a016-c22dcc1ede52)

Modern software teams are overwhelmed with disconnected tools—Git, Jira, Confluence, Notion, and more. Developers often struggle to recall the rationale behind code changes, architecture decisions, or feature implementations. DevSecrin solves this by creating a unified context layer that feeds this collective knowledge into AI systems—so developers don't just see *what* changed, but *why* it changed.

## ⚙️ Requirements

Make sure the following are installed on your machine:

- **PostgreSQL** – running locally or remotely
- **Ollama** – with models:
  - `deepseek-r1:1.5b` – for AI reasoning
  - `mxbai-embed-large:latest` – for embeddings
- **Python 3.8+** – for backend AI modules
- **Node.js (v20+) & pnpm** – for TypeScript services

## � Quick Start (Local)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/devsecrin.git
cd devsecrin

# 2. Install dependencies
pnpm install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env  # Then edit `.env` with your details

# 4. Initialize the database
python packages/dbup/runner.py

# 5. Start the app
pnpm run devsecrin
```

Once running:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000

## ✨ What Can It Do?

🔍 **Ask questions like:**
- "Why did we move to Kafka?"
- "What's the history of this function?"

🧠 **Pull insights from:**
- Git commits & PRs
- Jira / GitHub Issues
- Confluence, Notion docs

🔗 **Graph-enhanced retrieval** using AI + embeddings

## 🧩 Core Features

- Multi-source integration (Git, Issues, Docs)
- Semantic understanding via embeddings
- Knowledge graphs to link related changes
- Natural language QA with history-aware AI
- Web UI + REST API for interaction

## 🔧 Project Structure

```
devsecrin/
├── apps/        # api and frontend
├── packages/
│   ├── ai/      # embedding, reasoning
│   ├── db/      # models and migrations
│   └── scraper/ # data ingestion
├── .env.example
```

## 🤝 Contribute

We love feedback and PRs!
See CONTRIBUTING.md for how to get involved.

## � Contact

Built with ❤️ by [@jenilsavani9](https://github.com/jenilsavani9)  
Connect on [LinkedIn](https://www.linkedin.com/in/jenil-savani/)

---

*"In a world full of files and functions—context is your compass."*
