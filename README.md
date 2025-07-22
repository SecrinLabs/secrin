# DevSecrin 🧠📘

**AI-powered Developer Context Engine that transforms scattered development knowledge into actionable insights.**

DevSecrin connects your Git repositories, issue trackers, and documentation to create a unified knowledge layer, making it easy to understand why code was written, how features evolved, and what decisions shaped your codebase.

## Who it's for 👥

- **Developers** joining new teams or working with unfamiliar codebases
- **Senior Engineers** looking to share institutional knowledge efficiently
- **Team Leads** wanting to improve code review quality and onboarding
- **Product Managers** seeking to understand technical context behind features

## How it works ⚡

DevSecrin operates as a three-layer system:

1. **Data Collection**: Ingests code, issues, and documentation from GitHub, Jira, Confluence, and local repositories
2. **Knowledge Graph**: Builds relationships between code changes, issues, and documentation using AI embeddings and graph analysis
3. **Intelligent Retrieval**: Combines vector similarity search with graph traversal to provide contextual answers

_For detailed technical architecture, see [docs/architecture.md](docs/architecture.md)_

## How to run it 🐳

### Quick Start with Docker (Recommended)

```bash
# Clone and start all services
git clone https://github.com/SecrinLabs/devsecrin.git
cd devsecrin
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### Development Setup

```bash
# Install dependencies
git clone https://github.com/SecrinLabs/devsecrin.git
cd devsecrin
python3 setup.py  # Automated setup script

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start development server
pnpm run devsecrin
```

## Demo 📺

> 🎬 **Demo coming soon** - We're preparing a comprehensive video walkthrough showing DevSecrin in action with a real codebase.

_Want to try it now? Follow the setup instructions above and explore with your own repositories._

## Core Features ✨

- **🔌 Multi-source Integration**: Connects Git, Jira, GitHub Issues, Confluence, and local repositories
- **🧠 Graph-Enhanced RAG**: Combines vector search with relationship analysis for better context
- **💬 Natural Language Queries**: Ask questions like "Why did we switch from Redis to Kafka?"
- **🔒 Privacy-First**: All processing happens locally using Ollama - no external AI services
- **⚡ Real-time Updates**: WebSocket support for live collaboration and notifications
- **🐳 Easy Deployment**: Full Docker support with automated setup scripts

## Documentation 📚

- **[Architecture Overview](docs/architecture.md)** - Detailed system design and component interaction
- **[Use Cases](docs/use-cases.md)** - How DevSecrin helps with onboarding, code review, and debugging
- **[How it Works](docs/how-it-works.md)** - AI pipeline, data collectors, and storage schema
- **[Configuration Guide](.env.example)** - Environment setup and integration configuration

## Project Structure 📁

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
├── docs/             # Documentation
├── docker-compose.yml
└── .env.example      # Configuration template
```

## Tech Stack 🛠️

- **Backend**: FastAPI, Python, PostgreSQL, SQLAlchemy
- **AI/ML**: Ollama, ChromaDB, NetworkX (Knowledge Graph)
- **Frontend**: Next.js, React, TailwindCSS, TypeScript
- **Integrations**: GitHub API, Confluence API, Web Scraping
- **Deployment**: Docker, Docker Compose

## Contributing 🤝

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Community 💬

- **Documentation**: Check our [docs/](docs/) folder for detailed guides
- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/SecrinLabs/devsecrin/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/SecrinLabs/devsecrin/discussions)

---

**Built with ❤️ by [SecrinLabs](https://github.com/SecrinLabs) for the developer community**

> _"Every line of code has a story. DevSecrin helps you remember why it was written."_
