# 🧠 DevSecrin - AI-Powered Developer Context Engine

> **Intelligent codebase understanding through AI reasoning and knowledge graphs**

DevSecrin transforms disconnected development tools (Git, Jira, Confluence) into a unified AI-powered context layer. Ask natural language questions about your codebase and get insights about *why* code was written, not just *what* changed.

![devsecrin_arch](https://github.com/SecrinLabs/devsecrin/blob/main/static/img/image.png)

## 🚀 Key Features

- **AI-Powered Q&A**: "Why did we switch to microservices?" → Get context from commits, issues, and docs
- **Multi-Source Integration**: Connects Git, GitHub Issues, PRs etc
- **Knowledge Graphs**: Links related code changes, decisions, and documentation
- **Semantic Search**: Vector embeddings for intelligent code understanding

## 🛠️ Tech Stack

**Backend**: Python, FastAPI, PostgreSQL, ChromaDB  
**AI/ML**: Ollama (DeepSeek-R1, MxBai embeddings), Gemini support  
**Infrastructure**: Docker

## 📦 Quick Start

```bash
git clone https://github.com/SecrinLabs/devsecrin.git
cd devsecrin

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Run migrations
python migration/runner.py

# Start services
python start_api.py  # API: http://localhost:8000
```

## 💡 Use Cases

- **Code Reviews**: Understand the context behind complex changes
- **Onboarding**: New developers quickly grasp project decisions
- **Technical Debt**: Track evolution of architectural decisions
- **Documentation**: Auto-generate context-aware explanations

## 🎯 Project Impact

- Reduces developer onboarding time
- Improves code review quality through historical context
- Enables data-driven technical decisions
- Bridges the gap between code and business requirements

--- 

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