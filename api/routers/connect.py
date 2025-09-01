import base64
import time
import jwt
import requests
from fastapi import APIRouter, HTTPException

from api.utils.standard_response import standard_response
from config import settings
from api.models.connect import GithubConnect

router = APIRouter()

# GitHub App credentials
GITHUB_APP_ID = settings.GITHUB_APP_ID
PRIVATE_KEY_B64 = settings.GITHUB_APP_SEC_KEY  # base64 string from env

def generate_jwt():
    """Generate a GitHub App JWT using RS256 with base64-decoded private key."""
    # Decode base64 -> PEM string
    private_key = base64.b64decode(PRIVATE_KEY_B64).decode("utf-8")

    now = int(time.time())
    payload = {
        "iat": now - 60,        # issued at
        "exp": now + (10 * 60), # max 10 min allowed
        "iss": GITHUB_APP_ID
    }

    # Sign with RS256
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


@router.post("/github/get-installation-token")
def github_app_auth(request: GithubConnect):
    try:
        # 1. Create JWT
        app_jwt = generate_jwt()

        # 2. Exchange JWT for installation access token
        url = f"https://api.github.com/app/installations/{request.installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.post(url, headers=headers)

        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail=response.json())

        access_token = response.json()["token"]

        return standard_response(
            success=True,
            message="GitHub installation token generated",
            data={
                "access_token": access_token,
                "expires_at": response.json()["expires_at"]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
