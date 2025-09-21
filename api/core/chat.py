import hmac
import hashlib
from fastapi import Request, HTTPException

from config import settings

async def verify_github_signature(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        raise HTTPException(status_code=401, detail="Missing signature")

    body = await request.body()  # raw request body (bytes)
    expected_signature = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")