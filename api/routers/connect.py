from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from api.utils.standard_response import standard_response
from config import settings
from api.models.connect import InstallationToken, SaveRepository, DisconnectService, GetAllIntegrations
from db.index import SessionLocal
from db.models.user import User
from db.models.integration import Integration, IntegrationType
from db.models.repository import Repository
from api.utils.github_token import get_github_access_token
from api.core.connect import get_repositories, remove_integration
from engine.ingest.main import update_vectorstore
from engine.query.main import qa_chain
from engine.main import run_embedder_v2

from service.main import run_scraper_by_name

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
        integration = session.query(Integration).filter(Integration.user_id == request.user_id, Integration.type == IntegrationType.github).first()
        
        if integration:
            # update config
            integration.config = {"installation_token": request.installation_token}
        else:
            # create new integration
            integration = Integration(
                user_id=request.user_id,
                type=IntegrationType.github,
                config={"installation_token": request.installation_token}
            )
            session.add(integration)
    
        session.commit()
        session.refresh(integration)

        # get installation access token
        access_token = get_github_access_token(request.installation_token)

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
            message="success",
            data={
                "repos": res
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/disconnect")
def disconnect_service(request: DisconnectService):
    try:
        removed = remove_integration(request.user_id, request.service_type)

        if not removed:
            return standard_response(
                success=False,
                message=f"No integration found for {request.service_type}",
                data=None,
            )

        return standard_response(
            success=True,
            message=f"Successfully disconnected {request.service_type}",
            data={},  # replace with real payload if needed
        )

    except Exception as e:
        print(f"Error while disconnecting service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/integrations")
def get_user_integrations(request: GetAllIntegrations):
    try:
        session = SessionLocal()
        integrations = (
            session.query(Integration)
            .filter(Integration.user_id == request.user_id)
            .all()
        )

        # Convert ORM objects to dicts (assuming Integration has `id`, `type`, `created_at` etc.)
        integration_list = [
            {
                "id": integration.id,
                "type": integration.type.value if hasattr(integration.type, "value") else integration.type,
            }
            for integration in integrations
        ]

        return standard_response(
            success=True,
            message=f"success",
            data={"integrations": integration_list},
        )

    except Exception as e:
        print(f"Error while fetching integrations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        session.close()


# TODO: accept user id from frontend
# TODO: response is in not valid format
@router.get("/")
def run_scrapper():
    try:
        # run_scraper_by_name(IntegrationType.github, 4)
        run_embedder_v2()
        return standard_response(
            success=True,
            message="success",
            data={
                "repos": "demo"
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))