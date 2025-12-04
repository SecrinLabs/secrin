# 🚀 Secrin Setup Guide

Welcome to Secrin! This guide covers two ways to run the project:

1. **☁️ Hybrid Mode (Recommended):** Cloud DB + Gemini API. Fast, lightweight, runs on any laptop.  
2. **🔒 Local Mode:** Local Docker DB + Ollama. Privacy-focused, requires good hardware (16GB+ RAM).

---

## 🛠️ 1. Prerequisites (Check these first!)
Open your terminal and check these versions. If missing, install them.

- **Git:** `git --version`  
- **Python (3.10+):** `python --version`  
- **Node.js (v20+):** `node -v`  
- **Poetry:** `pip install poetry`  
- **(Optional) Docker:** Required only if you choose "Local Mode".  
- **(Optional) Ollama:** Required only if you choose "Local Mode".

---

## 🔑 2. Credentials & Services
Choose **Option A** (Easier) or **Option B** (Private).

### Option A — Hybrid (Cloud DB + Gemini)
1. **Database:** Go to https://console.neo4j.io  
    - Create a **Free Instance**.  
    - ⚠️ **Copy the password immediately.** You won't see it again.  
    - Copy the URI (example: `neo4j+s://abc12345.databases.neo4j.io`).  
2. **AI Model:** Get a key from Google AI Studio: https://aistudio.google.com/app/apikey

### Option B — Fully Local (Docker + Ollama)
1. **Database:** Run this Docker command to start Neo4j locally:
```bash
docker run --restart always --publish=7474:7474 --publish=7687:7687 --env NEO4J_AUTH=neo4j/password neo4j:latest
```
2. **AI Model:** Install Ollama and pull the model:
```bash
ollama pull llama3.2
ollama serve
```

---

## 🖥️ 3. Backend Setup (Terminal 1)

### Step 3.1 — Install dependencies
```bash
git clone https://github.com/SecrinLabs/secrin.git
cd secrin
poetry install
```

### Step 3.2 — Configure environment (.env)
Create the .env file from the example:

```bash
cp .env.example .env
```

Open `.env` and paste the configuration matching your choice from Step 2.

Option A (Hybrid / Gemini) — example `.env`:

```Bash
# --- Database (Neo4j Aura) ---
NEO4J_URI=neo4j+s://<YOUR_INSTANCE_ID>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASS=<YOUR_SAVED_PASSWORD>
NEO4J_DB=neo4j

# --- Embedding (Local CPU/GPU) ---
EMBEDDING_PROVIDER=sentence_transformer
SENTENCE_TRANSFORMER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# --- LLM (Gemini) ---
LLM_PROVIDER=gemini
GOOGLE_API_KEY=<YOUR_GEMINI_KEY>
```

Option B (Local / Ollama) — example `.env`:

```Bash
# --- Database (Local Docker) ---
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=password
NEO4J_DB=neo4j

# --- Embedding (Ollama) ---
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIMENSION=1024

# --- LLM (Ollama) ---
LLM_PROVIDER=ollama
LLM_MODEL_OLLAMA=llama3.2
```

### Step 3.3 — Launch backend
```bash
# 1. Verify connection
poetry run setup

# 2. Start server
poetry run server
```
Success: you should see Uvicorn running on http://0.0.0.0:8000.

---

## 🎨 4. Frontend Setup (Terminal 2)

Open a new terminal window:
```bash
cd secrin/apps/web
```

### Step 4.1 — Install dependencies
The project prefers pnpm. Try these methods in order.

Method 1 — Standard:
```bash
corepack enable
pnpm install
```

Method 2 — If you get "Permission Denied" (Windows) (PowerShell):

```powershell
iwr https://get.pnpm.io/install.ps1 -useb | iex
```
Then retry Method 1.

Method 3 — Fallback to npm:
```bash
npm install
```

### Step 4.2 — Start UI
```bash
cp .env.example .env
pnpm dev   # OR 'npm run dev' if you used Method 3
```
Success: open http://localhost:3000

---

## 🚀 5. First Run & Ingestion
- The graph will be blank on first login. This is normal.  
- Login using your Neo4j credentials.  
- Hybrid users: if `neo4j+s://` fails to connect, try `bolt+s://`.

Ingest data:
1. Go to "Integrations" in the sidebar.  
2. Paste a GitHub URL (example: `https://github.com/SecrinLabs/secrin`).  
3. Click "Ingest".  
4. Watch the backend terminal — it will clone the repo and embed it.  
5. When the backend terminal says "Finished", go to the Graph tab to view your data.

---

## ❓ Troubleshooting — Common Errors

- "No routing servers available"  
  1. Check if Neo4j Aura is "Paused" in the console. Resume it.  
  2. Try using `bolt+s://` instead of `neo4j+s://`.  
  3. Try a mobile hotspot (some Wi‑Fi blocks port 7687).

- "Database does not exist"  
  - Neo4j Aura Free tier only allows the database name `neo4j`. Check your `.env`.

- "Command pnpm not found"  
  - Restart your terminal after installing it. If it still fails, in PowerShell run:
```powershell
$env:PATH = "$env:LOCALAPPDATA\pnpm;$env:PATH"
```

- "Unsupported LLM provider: gemini"  
  - You are running an old version. `git pull` the latest changes or check `llm_factory.py`.