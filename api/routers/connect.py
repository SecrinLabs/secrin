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
from engine.ingest.main import update_vectorstore
from engine.query.main import qa_chain

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
async def save_repository(request: SaveRepository):  # <-- I assume it's SaveRepositoryList, not SaveRepository
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
                repo_id=repo.id,
                repo_name=repo.name,
                full_name=repo.full_name,
                repo_url=repo.html_url,
                description=repo.description,
                private=repo.private,
                language=repo.language,
                topics=repo.topics,
                stargazers_count=repo.stargazers_count,
                forks_count=repo.forks_count,
                watchers_count=repo.watchers_count,
                default_branch=repo.default_branch,
                open_issues_count=repo.open_issues_count,
                has_issues=repo.has_issues,
                has_discussions=repo.has_discussions,
                archived=repo.archived,
                created_at=repo.created_at,
                updated_at=repo.updated_at,
                pushed_at=repo.pushed_at,
                clone_url=repo.clone_url,
                owner_login=repo.owner.login if repo.owner else None,
                owner_type=repo.owner.type if repo.owner else None,
            ).on_conflict_do_update(
                index_elements=["user_id", "repo_url"],  # unique constraint must exist on these
                set_={
                    "repo_name": repo.name,
                    "description": repo.description,
                    "language": repo.language,
                    "topics": repo.topics,
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count,
                    "watchers_count": repo.watchers_count,
                    "open_issues_count": repo.open_issues_count,
                    "updated_at": repo.updated_at,
                    "pushed_at": repo.pushed_at,
                    "owner_login": repo.owner.login if repo.owner else None,
                    "owner_type": repo.owner.type if repo.owner else None,
                }
            )

            session.execute(stmt)

        await update_vectorstore()

        session.commit()

        return standard_response(
            success=True,
            message="Repositories saved successfully",
            data={"count": len(request.repository_list)},
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

from pydantic import BaseModel

class GetAns(BaseModel):
    query: str

@router.post("/github/get-ans")
async def get_ans(request: GetAns):
    try:
        res = qa_chain(request.query)
        return standard_response(
            success=True,
            message="Installation token saved, repos fetched",
            data={
                "repos": res
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))