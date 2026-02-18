import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job

from packages.config.settings import Settings
from .models.config import LLMConfig

logger = logging.getLogger(__name__)

settings = Settings()

REDIS_URL = settings.REDIS_URL

app = FastAPI(title="Arc42gen API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis + RQ setup
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue(connection=redis_conn, default_timeout=7200)  # 2 hour timeout


class PublicJobRequest(BaseModel):
    """Request to submit a public doc generation job (no GitHub commit)."""
    source_repo_url: str
    local_output_dir: str = "./docs"


class JobSubmitRequest(BaseModel):
    """Request to submit a doc generation job."""
    source_repo_url: str
    branch: str = "main"
    github_token: str
    owner: str  # GitHub owner of docs repo
    repo_name: str  # Docs repo name
    source_owner: str  # Owner of source repo
    source_name: str  # Name of source repo
    project_id: str
    local_output_dir: str = "./docs"


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued, running, success, failed, cancelled
    progress: int = 0
    current_step: Optional[str] = None
    step_number: Optional[int] = None
    total_steps: Optional[int] = None
    substep: Optional[int] = None
    substep_total: Optional[int] = None
    substep_message: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


def _build_config_dict() -> dict:
    """Build the LLM/generation config from server settings."""
    provider = settings.ARC42GEN_LLM_PROVIDER

    model = settings.ARC42GEN_LLM_MODEL
    if not model:
        model = LLMConfig.DEFAULT_MODELS.get(provider, "")

    api_key_map = {
        "gemini": settings.GEMINI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "ollama": "ollama",
    }
    api_key = api_key_map.get(provider, "")

    if provider != "ollama" and not api_key:
        env_var = LLMConfig.API_KEY_ENV_VARS.get(provider, "LLM_API_KEY")
        raise HTTPException(
            status_code=500,
            detail=f"No API key configured for {provider}. Set {env_var} in your .env file",
        )

    return {
        "llm": {
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "max_tokens": settings.ARC42GEN_MAX_TOKENS,
            "base_url": settings.OLLAMA_BASE_URL if provider == "ollama" else "",
            "timeout": settings.OLLAMA_TIMEOUT if provider == "ollama" else 0,
        },
        "repository": {
            "include": settings.ARC42GEN_INCLUDE_PATTERNS,
            "exclude": settings.ARC42GEN_EXCLUDE_PATTERNS,
        },
        "arc42": {
            "sections": settings.ARC42GEN_SECTIONS,
            "diagram_style": settings.ARC42GEN_DIAGRAM_STYLE,
            "output_format": settings.ARC42GEN_OUTPUT_FORMAT,
        },
        "decomposition": {
            "max_module_size": settings.ARC42GEN_MAX_MODULE_SIZE,
            "max_depth": settings.ARC42GEN_MAX_DEPTH,
        },
    }


@app.post("/public/generate", response_model=JobSubmitResponse)
async def submit_public_job(request: PublicJobRequest) -> JobSubmitResponse:
    """Submit a public doc generation job (no GitHub commit). Returns instantly with a job_id."""
    logger.info("=" * 60)
    logger.info("PUBLIC JOB SUBMIT")
    logger.info("  repo: %s", request.source_repo_url)
    logger.info("=" * 60)

    repo_url = request.source_repo_url
    if not repo_url.endswith(".git"):
        repo_url = f"{repo_url}.git"

    config_dict = _build_config_dict()

    job = queue.enqueue(
        "packages.arc42gen.jobs.generate_only",
        repo_url=repo_url,
        config_dict=config_dict,
        local_output_dir=request.local_output_dir,
        job_timeout=7200,
        result_ttl=86400,
    )

    logger.info("Public job enqueued: %s", job.id)
    return JobSubmitResponse(job_id=job.id, status="queued")


@app.post("/jobs", response_model=JobSubmitResponse)
async def submit_job(request: JobSubmitRequest) -> JobSubmitResponse:
    """Submit a doc generation job. Returns instantly with a job_id."""
    logger.info("=" * 60)
    logger.info("JOB SUBMIT")
    logger.info("  repo: %s/%s", request.source_owner, request.source_name)
    logger.info("  docs_repo: %s/%s", request.owner, request.repo_name)
    logger.info("  project_id: %s", request.project_id)
    logger.info("=" * 60)

    # Build the repo URL with authentication
    repo_url = request.source_repo_url
    if request.github_token and repo_url.startswith("https://github.com/"):
        repo_url = repo_url.replace(
            "https://github.com/",
            f"https://x-access-token:{request.github_token}@github.com/",
        )
    if not repo_url.endswith(".git"):
        repo_url = f"{repo_url}.git"

    config_dict = _build_config_dict()

    job = queue.enqueue(
        "packages.arc42gen.jobs.generate_and_commit",
        repo_url=repo_url,
        branch=request.branch,
        github_token=request.github_token,
        owner=request.owner,
        repo_name=request.repo_name,
        source_owner=request.source_owner,
        source_name=request.source_name,
        project_id=request.project_id,
        config_dict=config_dict,
        local_output_dir=request.local_output_dir,
        job_timeout=7200,  # 2 hours
        result_ttl=86400,  # keep result 24 hours
    )

    logger.info("Job enqueued: %s", job.id)
    return JobSubmitResponse(job_id=job.id, status="queued")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the status and progress of a job."""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    meta = job.meta or {}

    # Map RQ job status to our status
    if job.is_queued:
        status = "queued"
    elif job.is_started:
        status = meta.get("status", "running")
    elif job.is_finished:
        result = job.result or {}
        status = "success" if result.get("success") else "failed"
    elif job.is_failed:
        status = "failed"
    elif job.is_canceled:
        status = "cancelled"
    else:
        status = "unknown"

    error = None
    result = None

    if job.is_finished:
        result = job.result
        if isinstance(result, dict) and not result.get("success"):
            error = result.get("error")
    elif job.is_failed:
        error = str(job.exc_info) if job.exc_info else "Job failed"

    return JobStatusResponse(
        job_id=job_id,
        status=status,
        progress=meta.get("progress", 0),
        current_step=meta.get("current_step"),
        step_number=meta.get("step_number"),
        total_steps=meta.get("total_steps"),
        substep=meta.get("substep"),
        substep_total=meta.get("substep_total"),
        substep_message=meta.get("substep_message"),
        result=result if job.is_finished else None,
        error=error,
    )


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a queued or running job."""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.is_queued or job.is_started:
        job.cancel()
        logger.info("Job cancelled: %s", job_id)
        return {"job_id": job_id, "status": "cancelled"}

    return {"job_id": job_id, "status": job.get_status(), "message": "Job already finished"}


@app.get("/jobs")
async def list_jobs():
    """List recent jobs (for debugging)."""
    jobs = []

    # Get jobs from different registries
    for registry_name, registry in [
        ("queued", queue),
        ("started", queue.started_job_registry),
        ("finished", queue.finished_job_registry),
        ("failed", queue.failed_job_registry),
    ]:
        if registry_name == "queued":
            job_ids = queue.job_ids[:20]
        else:
            job_ids = registry.get_job_ids()[:20]

        for jid in job_ids:
            try:
                job = Job.fetch(jid, connection=redis_conn)
                meta = job.meta or {}
                jobs.append({
                    "job_id": jid,
                    "status": meta.get("status", registry_name),
                    "progress": meta.get("progress", 0),
                    "current_step": meta.get("current_step"),
                    "enqueued_at": str(job.enqueued_at) if job.enqueued_at else None,
                })
            except Exception:
                pass

    return {"jobs": jobs}


@app.get("/health")
async def health():
    """Health check endpoint."""
    provider = settings.ARC42GEN_LLM_PROVIDER
    model = settings.ARC42GEN_LLM_MODEL or LLMConfig.DEFAULT_MODELS.get(provider, "")

    # Check Redis connectivity
    redis_ok = False
    try:
        redis_conn.ping()
        redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if redis_ok else "degraded",
        "provider": provider,
        "model": model,
        "redis": "connected" if redis_ok else "disconnected",
        "queue_size": queue.count if redis_ok else None,
    }
