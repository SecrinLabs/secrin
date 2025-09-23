import requests
from fastapi import HTTPException

from db.index import SessionLocal
from db.models.integration import Integration, IntegrationType
from db.models.repository import Repository
from db.models.githubcommits import GithubCommit, GithubCommitFile

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

def get_integration_type(integration_name) -> IntegrationType:
    if integration_name == "github":
        return IntegrationType.github
    return None


def remove_integration(user_id: int, integration_name: str) -> bool:
    session = SessionLocal()
    try:
        integration_type = get_integration_type(integration_name)
        if not integration_type:
            return False

        integration = (
            session.query(Integration)
            .filter(
                Integration.user_id == user_id,
                Integration.type == integration_type,
            )
            .first()
        )

        if not integration:
            return False
        
            # Delete repos
        session.query(Repository).filter(Repository.user_id == user_id).delete(synchronize_session=False)

        # Delete commits (files will cascade-delete)
        session.query(GithubCommit).filter(GithubCommit.user_id == user_id).delete(synchronize_session=False)

        session.delete(integration)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
