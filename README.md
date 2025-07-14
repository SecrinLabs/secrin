# DevSecrin 🧠📘

DevSecrin (Developer Secret Engine) is an AI-powered **Developer Context Engine** designed to enhance the reasoning and productivity of developers by bringing deep, structured historical knowledge from code, tickets, and documentation directly into their workflow.

> "Every line of code has a story. DevSecrin helps you remember why it was written."

## 🚀 Quick Start

### 🐳 Docker (Recommended)

```bash
git clone https://github.com/yourusername/devsecrin.git
cd devsecrin
docker-compose up -d
```

### 🔧 Automated Setup

```bash
git clone https://github.com/yourusername/devsecrin.git
cd devsecrin
python3 setup.py
```

### 🖥️ Manual Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## 🌟 System Architecture

![devsecrin_arch](https://github.com/user-attachments/assets/3bf40c77-2d7a-49de-a016-c22dcc1ede52)

Modern software teams are overwhelmed with disconnected tools—Git, Jira, Confluence, Notion, and more. Developers often struggle to recall the rationale behind code changes, architecture decisions, or feature implementations. DevSecrin solves this by creating a unified context layer that feeds this collective knowledge into AI systems—so developers don't just see *what* changed, but *why* it changed.

## 🧩 Core Features

### 🔌 Multi-source Integration

DevSecrin ingests and unifies data from:

* **Git Repositories**: Parses commit history, diffs, and PR metadata
* **Issue Trackers** (Jira, GitHub Issues): Understands the intent and scope behind changes
* **Documentation** (Confluence, Notion, Sitemaps): Captures structured knowledge and decisions
* **Local Repositories**: Enables offline codebase analysis

### � Graph-Enhanced RAG

* **Knowledge Graph**: Builds relationships between code, issues, PRs, and documentation
* **Contextual Embeddings**: All data is vectorized for semantic understanding
* **Smart Context Retrieval**: Finds related information across different sources

### 💬 Intelligent QA Layer

Ask natural language questions like:
* "Why did we switch from Redis to Kafka last quarter?"
* "What were the key design decisions in the payment module?"
* "Has this function been changed recently, and why?"
* "Show me all issues related to authentication"

### 🛠️ Developer-Friendly Tools

* **Web Interface**: Modern, responsive UI for easy interaction
* **REST API**: Integrate with your existing tools
* **Docker Support**: Easy deployment and scaling
* **Real-time Updates**: WebSocket support for live notifications

## 📦 Installation Options

### 🐳 Docker (Recommended for Production)

```bash
# Clone the repository
git clone https://github.com/yourusername/devsecrin.git
cd devsecrin

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### 🔧 Automated Setup (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/devsecrin.git
cd devsecrin

# Run the setup script
python3 setup.py

# Start the application
./start.sh  # Linux/Mac
# or
start.bat   # Windows
```

### 🖥️ Manual Installation

For detailed manual installation instructions, see [INSTALL.md](INSTALL.md).

## ⚙️ Configuration

### Quick Configuration

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```env
   # Required: Database
   DATABASE_URL=postgresql://user:pass@localhost:5432/devsecrin
   
   # Required: AI Model
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=deepseek-r1:1.5b
   
   # Optional: GitHub Integration
   GITHUB_TOKEN=your_github_token
   GITHUB_OWNER=your_username
   GITHUB_REPO=your_repository
   
   # Optional: Confluence Integration
   CONFLUENCE_URL=https://your-domain.atlassian.net
   CONFLUENCE_USERNAME=your_email@example.com
   CONFLUENCE_API_TOKEN=your_api_token
   ```

### Integration Setup

#### GitHub Integration
1. Go to [GitHub Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Create a new token with `repo` and `read:org` permissions
3. Add the token to your `.env` file

#### Confluence Integration
1. Go to [Atlassian Account Settings → API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new API token
3. Add your Confluence URL, username, and token to `.env`

## 🚀 Usage

### Web Interface

1. **Open the application:** http://localhost:3000
2. **Configure integrations** in the settings panel
3. **Start asking questions** about your codebase!

### API Usage

```bash
# Ask a question
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Why did we refactor the authentication system?"}'

# Get system status
curl "http://localhost:8000/health"
```

### Python SDK

```python
from packages.ai.newindex import run_graph_generator

# Ask a question directly
answer = run_graph_generator("What are the recent changes in the API?")
print(answer)
```

## 🔧 Development

### Prerequisites

- Python 3.8+
- Node.js 20+
- PostgreSQL 13+
- Ollama with deepseek-r1:1.5b model

### Local Development Setup

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
pnpm install

# Setup database
python packages/dbup/runner.py

# Start development server
pnpm run dev
```

### Project Structure

```
devsecrin/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── packages/
│   ├── ai/           # AI and RAG components
│   ├── db/           # Database models
│   ├── models/       # Data models
│   └── scraper/      # Web scraping tools
├── docker-compose.yml
├── Dockerfile
├── setup.py          # Automated setup script
└── INSTALL.md        # Detailed installation guide
```

## 🧱 Tech Stack

* **Backend**: FastAPI, Python, PostgreSQL, SQLAlchemy
* **AI/ML**: Ollama, ChromaDB, NetworkX (Knowledge Graph)
* **Frontend**: Next.js, React, TailwindCSS, TypeScript
* **Integrations**: GitHub API, Confluence API, Web Scraping
* **Deployment**: Docker, Docker Compose
* **Database**: PostgreSQL with ChromaDB for vector storage

## 🛣️ Roadmap

### ✅ v0.1 (Current)
* [x] GitHub integration with token-based auth
* [x] Confluence and sitemap ingestion
* [x] ChromaDB + Ollama RAG backend
* [x] Graph-enhanced RAG with knowledge graph
* [x] API for question answering
* [x] Web interface for integration management
* [x] Docker deployment support
* [x] Automated setup scripts

### 🚧 v0.2 (In Progress)
* [ ] Enhanced web UI with chat interface
* [ ] Real-time collaboration features
* [ ] Advanced filtering and search
* [ ] Performance optimizations
* [ ] Monitoring and analytics dashboard

### 🔮 v0.3 (Planned)
* [ ] VS Code extension
* [ ] DevJournal (local note-taking for decisions)
* [ ] Slack/Teams integration
* [ ] Advanced security features
* [ ] Multi-tenant support
* [ ] Cloud deployment options

## 🧠 Philosophy

DevSecrin is built on the belief that:

* **Context is everything** for developer productivity
* **AI must be grounded in history**, not hallucinations
* **Knowledge graphs** provide better context than simple vector search
* **Open source** and transparency win in the long term
* **Developer experience** should be seamless and intuitive

## � How It Works

1. **Data Ingestion**: Connects to your GitHub repositories, Confluence spaces, and documentation
2. **Knowledge Graph Building**: Creates relationships between code, issues, PRs, and documentation
3. **Vectorization**: Converts all content into embeddings for semantic search
4. **Context Retrieval**: When you ask a question, finds relevant context using both vector similarity and graph relationships
5. **AI Generation**: Feeds the enhanced context to the AI model for accurate, grounded answers

## 🎯 Use Cases

### For Developers
* **Code Review**: "What was the reasoning behind this design pattern?"
* **Bug Investigation**: "Are there any related issues to this error?"
* **Feature Planning**: "What similar features have we built before?"
* **Documentation**: "What's the history of this API endpoint?"

### For Team Leads
* **Architecture Decisions**: "Why did we choose this technology stack?"
* **Progress Tracking**: "What's the status of authentication improvements?"
* **Knowledge Transfer**: "What context does the new developer need?"

### For Product Managers
* **Feature Context**: "What user feedback led to this feature?"
* **Technical Debt**: "What are the recurring technical issues?"
* **Release Planning**: "What changes are in the upcoming release?"

## 🔧 Troubleshooting

### Common Issues

1. **Ollama not responding**: Ensure Ollama is running and the model is downloaded
2. **Database connection failed**: Check PostgreSQL is running and credentials are correct
3. **GitHub API rate limits**: Use a personal access token with appropriate permissions
4. **Memory issues**: Ensure you have at least 8GB RAM for the AI model

### Getting Help

* **Documentation**: Check [INSTALL.md](INSTALL.md) for detailed setup instructions
* **Issues**: Create an issue on GitHub with error details
* **Logs**: Check `logs/app.log` for detailed error information

## 📊 Performance

### Recommended System Requirements

* **RAM**: 8GB minimum, 16GB recommended
* **Storage**: 10GB for models and data
* **CPU**: Multi-core processor recommended
* **Network**: Good internet connection for initial model download

### Optimization Tips

* Use Docker for consistent performance
* Enable GPU acceleration if available
* Tune embedding batch sizes for your hardware
* Use database connection pooling for high load

## 🛡️ Security

* **API Security**: Built-in rate limiting and input validation
* **Data Privacy**: All data stays on your infrastructure
* **Token Security**: Secure handling of API tokens
* **Network Security**: Configurable CORS and SSL support

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

* **Ollama** for providing local AI model inference
* **ChromaDB** for vector database capabilities
* **FastAPI** for the excellent web framework
* **NetworkX** for graph processing capabilities

---

**Made with ❤️ by developers, for developers**

MIT License

## 🙌 Contributing

PRs, suggestions, and architecture feedback are welcome. The vision for DevSecrin is big—help us make it global.

## 📫 Contact

Built with 💻 by Jenil Savani. Connect on [LinkedIn](https://www.linkedin.com/in/jenil-savani/) or [GitHub](https://github.com/jenilsavani9).

---

> *"In a world full of files, functions, and frameworks—context is your compass. DevSecrin helps you find your way."*
