from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from api.utils.standard_response import standard_response
from config import settings
from api.models.connect import InstallationToken, SaveRepository
from db.index import SessionLocal
from db.models.user import User
from db.models.repository import Repository
from api.utils.github_token import get_github_access_token
from api.core.connect import get_repositories

router = APIRouter()

# GitHub App credentials
GITHUB_APP_ID = settings.GITHUB_APP_ID
PRIVATE_KEY_B64 = settings.GITHUB_APP_SEC_KEY  # base64 string from env

@router.post("/github/save-installation-token")
def github_save_installation_token(request: InstallationToken):
    try:
        session: Session = SessionLocal()

        # find user
        user = session.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # save installation ID
        user.github_installation_id = int(request.installation_token)
        session.commit()
        session.refresh(user)

        # get installation access token
        access_token = get_github_access_token(user.github_installation_id)

        # fetch repos for this installation
        repos = get_repositories(access_token)

        return standard_response(
            success=True,
            message="Installation token saved, repos fetched",
            data={
                "repos": repos.get("repositories", [])
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@router.post("/github/save-repository")
def save_repository(request: SaveRepository):
    try:
        session: Session = SessionLocal()

        # check if user exists
        user = session.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # save each repo
        for repo in request.repository_list:
            stmt = insert(Repository).values(
                user_id=request.user_id,
                repo_name=repo.name,
                repo_url=repo.url
            ).on_conflict_do_update(
                index_elements=["user_id", "repo_url"],  # matches your unique constraint
                set_={
                    "repo_name": repo.name  # update repo_name if it changes
                }
            )
            session.execute(stmt)

        session.commit()

        return standard_response(
            success=True,
            message="Repositories saved successfully",
            data={"count": len(request.repository_list)}
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()