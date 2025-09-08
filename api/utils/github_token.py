import base64
import time
import jwt
import requests
from fastapi import HTTPException

from config import settings

GITHUB_APP_ID = settings.GITHUB_APP_ID
PRIVATE_KEY_B64 = settings.GITHUB_APP_SEC_KEY  # base64 string from env


def generate_jwt() -> str:
    """Generate a GitHub App JWT using RS256 with base64-decoded private key."""
    private_key = base64.b64decode(PRIVATE_KEY_B64).decode("utf-8")

    now = int(time.time())
    payload = {
        "iat": now - 60,        # issued at
        "exp": now + (10 * 60), # expires in 10 minutes
        "iss": GITHUB_APP_ID,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


def get_github_access_token(installation_id: int) -> str:
    """
    Get an installation access token for a GitHub App installation.
    Used internally (not exposed as API).
    """
    try:
        app_jwt = generate_jwt()

        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.post(url, headers=headers)

        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json()
            )

        data = response.json()
        return data["token"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub token exchange failed: {str(e)}")
