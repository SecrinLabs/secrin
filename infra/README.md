Devsecrin infra: Docker build and run

This folder contains Docker-related files to run the FastAPI backend in a container.

Files:
- Dockerfile - builds the API image
- docker-compose.yml - compose file to run services needed for local dev (Redis, optional Ollama). Postgres is not required in compose — use your managed DB (e.g. Supabase) and set DATABASE_URL in `infra/.env`.
- entrypoint.sh - container entrypoint that prepares folders and runs uvicorn
- .dockerignore - files excluded from build context

Quick start (from project root):

Build image:
```bash
docker build -t devsecrin-api:latest -f infra/Dockerfile .
```

Run with Docker (example using a managed DB like Supabase):
```bash
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://<user>:<password>@db.<project>.supabase.co:5432/<database>" \
  -e API_PORT=8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/gemini_store:/app/gemini_store \
  -v $(pwd)/chroma_store:/app/chroma_store \
  devsecrin-api:latest
```

Or use docker-compose (recommended for local development):
```bash
cd infra
docker compose up --build
```

Notes:
- The entrypoint attempts to call `migration.runner.run()` if available. Adjust to your migration tooling.
- The image expects environment variables (DATABASE_URL, GEMINI_API_KEY, EMBEDDER_NAME, etc.) via an env file or docker-compose. If you run a managed DB (Supabase), set `DATABASE_URL` in `infra/.env` and do not run Postgres in Compose.
- Frontend is deployed separately (Vercel); this image only runs the backend and required services.
