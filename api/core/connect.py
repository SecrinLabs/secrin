import requests
from fastapi import HTTPException

GITHUB_API_URL = "https://api.github.com"

def get_repositories(installation_token: str):
    """
    Fetch repositories accessible to a GitHub App installation.
    
    Args:
        installation_token (str): Installation access token returned from GitHub.

    Returns:
        dict: API response containing repositories.
    """
    url = f"{GITHUB_API_URL}/installation/repositories"
    headers = {
        "Authorization": f"Bearer {installation_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json()
        )

    return response.json()
