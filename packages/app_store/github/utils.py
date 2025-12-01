import hashlib
import hmac
from typing import Optional
from fastapi import Request

class SignatureVerificationError(Exception):
    """Raised when GitHub signature verification fails."""
    pass

async def verify_github_signature(request: Request, secret: Optional[str]):
    """
    Verify that the request came from GitHub.
    Raises SignatureVerificationError if verification fails.
    """
    if not secret:
        # In a production environment, we must have a secret.
        raise SignatureVerificationError("Webhook secret is not configured")

    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise SignatureVerificationError("Missing X-Hub-Signature-256 header")

    body = await request.body()
    
    # Calculate expected signature
    hash_object = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise SignatureVerificationError("Invalid signature")
