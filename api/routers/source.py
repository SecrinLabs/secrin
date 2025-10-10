from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.dialects.postgresql import insert

from api.utils.standard_response import standard_response
from api.models.source import ConnectedSourceDTO, GetRemainingRepositoryDTO, RemoveRepositoryDTO, AddRepositoryDTO
from api.utils.github_token import get_github_access_token
from api.core.auth import get_current_user
from api.core.connect import get_repositories
from db.models.repository import Repository
from db.models.user import User
from db.models.integration import Integration, IntegrationType
from db.index import SessionLocal
from service.main import run_scraper_by_name
from semantic.pipeline.github import GitHubPipeline

from config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/get-all-integrations")
def get_connected_source(request: ConnectedSourceDTO, user: User = Depends(get_current_user)):
    try:
        logger.info(f"get all integrations for user")
        session = SessionLocal()

        integrations = []

        github_repos = (
            session.query(Repository)
            .filter(Repository.user_id == user.id)
            .all()
        )

        for repo in github_repos:
            integrations.append({
                "id": repo.id,
                "type": "repository",
                "name": repo.repo_name,
                "metadata": {
                    "url": repo.repo_url,
                    "repo_id": repo.repo_id,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None
                }
            })

        return standard_response(
            success=True,
            message="success",
            data={"integrations": integrations},
        )

    except Exception as e:
        logger.error("Error fetching all integrations", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        session.close()

@router.post("/github/get-remaining-repository")
def get_remaining_repository_to_connect(request: GetRemainingRepositoryDTO, user: User = Depends(get_current_user)):
    try:
        session = SessionLocal()

        integration = session.query(Integration).filter(Integration.user_id == user.id, Integration.type == IntegrationType.github).first()            

        installation_token = None
        if integration and integration.config:
            installation_token = integration.config.get("installation_token")

        if not installation_token:
            raise HTTPException(status_code=404, detail="Some error occured")
        
        # get installation access token
        access_token = get_github_access_token(int(installation_token))

        # fetch repos for this installation
        repos = get_repositories(access_token)
        repos_list = repos.get("repositories", [])

        savedRepo = session.query(Repository).filter(Repository.user_id == user.id).all()
        saved_repo_ids = {repo.repo_id for repo in savedRepo}
        
        remaining_repos = [
            {
                "url": r["html_url"],   # GitHub gives full repo URL here
                "repo_id": r["id"],
                "name": r["name"]
            }
            for r in repos_list
            if r["id"] not in saved_repo_ids
        ]

        return standard_response(
            success=True,
            message="success",
            data={"repositorys": remaining_repos},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        session.close()

@router.post("/github/remove-repository")
def remove_repository(request: RemoveRepositoryDTO, user: User = Depends(get_current_user)):
    try:
        session = SessionLocal()

        # find the repo to delete
        repo = session.query(Repository).filter(
            Repository.user_id == user.id,
            Repository.repo_id == request.repo_id
        ).first()

        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

        # delete it
        session.delete(repo)
        session.commit()

        return standard_response(
            success=True,
            message="Repository removed successfully",
            data={},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        session.close()

@router.post("/github/add-repository")
def remove_repository(request: AddRepositoryDTO, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    try:
        session = SessionLocal()

        # find the repo to delete
        repo = session.query(Repository).filter(
            Repository.user_id == user.id,
            Repository.repo_id == request.repo_id
        ).first()

        if repo:
            raise HTTPException(status_code=200, detail="repository alredy added")

        integration = session.query(Integration).filter(Integration.user_id == user.id, Integration.type == IntegrationType.github).first()            

        installation_token = None
        if integration and integration.config:
            installation_token = integration.config.get("installation_token")

        if not installation_token:
            raise HTTPException(status_code=404, detail="Some error occured")
        
        # get installation access token
        access_token = get_github_access_token(int(installation_token))

        # fetch repos for this installation
        repos = get_repositories(access_token)
        repos_list = repos.get("repositories", [])

        # find the repo with requested repo_id
        repo = next((r for r in repos_list if r["id"] == request.repo_id), None)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found in GitHub account")
        
        # save the repo
        stmt = insert(Repository).values(
            user_id=user.id,
            repo_id=repo["id"],
            repo_name=repo["name"],
            full_name=repo.get("full_name"),
            repo_url=repo.get("html_url"),
            description=repo.get("description"),
            private=repo.get("private"),
            language=repo.get("language"),
            topics=repo.get("topics"),
            stargazers_count=repo.get("stargazers_count"),
            forks_count=repo.get("forks_count"),
            watchers_count=repo.get("watchers_count"),
            default_branch=repo.get("default_branch"),
            open_issues_count=repo.get("open_issues_count"),
            has_issues=repo.get("has_issues"),
            has_discussions=repo.get("has_discussions"),
            archived=repo.get("archived"),
            created_at=repo.get("created_at"),
            updated_at=repo.get("updated_at"),
            pushed_at=repo.get("pushed_at"),
            clone_url=repo.get("clone_url"),
            owner_login=repo["owner"]["login"] if repo.get("owner") else None,
            owner_type=repo["owner"]["type"] if repo.get("owner") else None,
        )
        
        session.execute(stmt)
        session.commit()

        # update vectorstore here
        background_tasks.add_task(run_scraper_by_name, IntegrationType.github, user.id)
        gitHubPipeline = GitHubPipeline(str(user.guid))
        background_tasks.add_task(gitHubPipeline.embed_github_commits, user.id)


        return standard_response(
            success=True,
            message="Repository removed successfully",
            data={},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        session.close()