# DevSecrin Installation Guide

Welcome to DevSecrin! This guide will help you set up the Developer Context Engine on your system.

## 🎯 Quick Start (Recommended)

### Option 1: Automated Setup Script (Easiest)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/devsecrin.git
   cd devsecrin
   ```

2. **Run the setup script:**
   ```bash
   python3 setup.py
   ```

3. **Follow the prompts** - The script will automatically:
   - Check prerequisites
   - Install dependencies
   - Set up the database
   - Create configuration files
   - Install required AI models

4. **Start the application:**
   ```bash
   ./start.sh  # On Linux/Mac
   # or
   start.bat   # On Windows
   ```

### Option 2: Docker (Recommended for Production)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/devsecrin.git
   cd devsecrin
   ```

2. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Wait for services to start** (first time may take 5-10 minutes for AI model download)

4. **Access the application:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000

## 📋 Manual Installation

### Prerequisites

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Node.js 20+** - [Download here](https://nodejs.org/)
- **PostgreSQL 13+** - [Download here](https://www.postgresql.org/download/)
- **Ollama** - [Download here](https://ollama.ai/)

### Step 1: Install Ollama and AI Model

1. Install Ollama from https://ollama.ai/
2. Start Ollama service
3. Install the required model:
   ```bash
   ollama pull deepseek-r1:1.5b
   ```

### Step 2: Database Setup

1. **Install PostgreSQL** and create a database:
   ```sql
   CREATE DATABASE devsecrin;
   CREATE USER devsecrin WITH PASSWORD 'devsecrin';
   GRANT ALL PRIVILEGES ON DATABASE devsecrin TO devsecrin;
   ```

### Step 3: Project Setup

1. **Clone and setup:**
   ```bash
   git clone https://github.com/yourusername/devsecrin.git
   cd devsecrin
   ```

2. **Install pnpm** (if not already installed):
   ```bash
   npm install -g pnpm
   ```

3. **Create Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   # or
   venv\Scripts\activate     # On Windows
   ```

4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Node.js dependencies:**
   ```bash
   pnpm install
   ```

6. **Setup database:**
   ```bash
   python packages/dbup/runner.py
   ```

### Step 4: Configuration

1. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file** with your settings:
   ```env
   DATABASE_URL=postgresql://devsecrin:devsecrin@localhost/devsecrin
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=deepseek-r1:1.5b
   GITHUB_TOKEN=your_github_token_here
   ```

### Step 5: Start the Application

```bash
pnpm run devsecrin
```

## 🔧 Configuration

### GitHub Integration

1. **Generate a GitHub Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create a new token with `repo` and `read:org` permissions
   - Add it to your `.env` file

2. **Configure repository:**
   ```env
   GITHUB_TOKEN=your_token_here
   GITHUB_OWNER=your_username
   GITHUB_REPO=your_repository
   ```

### Confluence Integration

1. **Generate API Token:**
   - Go to Atlassian Account Settings → Security → API tokens
   - Create a new token

2. **Configure in .env:**
   ```env
   CONFLUENCE_URL=https://your-domain.atlassian.net
   CONFLUENCE_USERNAME=your_email@example.com
   CONFLUENCE_API_TOKEN=your_api_token
   ```

### Custom AI Models

To use a different AI model:

1. **Install the model:**
   ```bash
   ollama pull your-model:tag
   ```

2. **Update .env:**
   ```env
   OLLAMA_MODEL=your-model:tag
   ```

## 🚀 Usage

### Web Interface

1. Open http://localhost:3000 in your browser
2. Configure your integrations in the settings
3. Start asking questions about your codebase!

### API Usage

The API is available at http://localhost:8000

Example request:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Why did we switch from Redis to Kafka?"}'
```

### Command Line

You can also use the Python interface directly:
```bash
python -c "from packages.ai.newindex import run_graph_generator; print(run_graph_generator('Your question here'))"
```

## 🔍 Troubleshooting

### Common Issues

1. **Ollama not responding:**
   - Ensure Ollama service is running
   - Check if the model is downloaded: `ollama list`

2. **Database connection errors:**
   - Verify PostgreSQL is running
   - Check database credentials in .env

3. **Memory issues:**
   - Ensure you have at least 8GB RAM
   - Consider using smaller AI models

4. **Node.js version issues:**
   - Update to Node.js 20+
   - Clear node_modules and reinstall

### Getting Help

1. **Check the logs:**
   ```bash
   tail -f logs/app.log
   ```

2. **Run in debug mode:**
   ```bash
   DEBUG=true pnpm run devsecrin
   ```

3. **Create an issue** on GitHub with:
   - Your OS and version
   - Error messages
   - Steps to reproduce

## 📊 Performance Optimization

### For Large Codebases

1. **Increase database limits:**
   ```env
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=30
   ```

2. **Optimize vector search:**
   ```env
   CHROMA_COLLECTION_SIZE=100000
   EMBEDDING_BATCH_SIZE=100
   ```

3. **Use GPU acceleration** (if available):
   ```env
   OLLAMA_GPU_LAYERS=35
   ```

## 🔄 Updates

To update DevSecrin:

1. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

2. **Update dependencies:**
   ```bash
   pip install -r requirements.txt
   pnpm install
   ```

3. **Run migrations:**
   ```bash
   python packages/dbup/runner.py
   ```

4. **Restart the application**

## 🛡️ Security

### Production Deployment

1. **Use strong passwords:**
   ```env
   DATABASE_PASSWORD=your_strong_password
   ```

2. **Enable SSL:**
   ```env
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```

3. **Set up reverse proxy** (nginx/Apache)

4. **Use environment-specific configs**

### API Security

The API includes built-in security features:
- Rate limiting
- Input validation
- CORS protection
- Authentication (when enabled)

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
