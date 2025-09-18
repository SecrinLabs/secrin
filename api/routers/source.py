from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from api.utils.standard_response import standard_response
from db.index import SessionLocal
from api.models.source import ConnectedSourceDTO
from db.models.repository import Repository

from config import settings

router = APIRouter()

@router.post("/get-all-integrations")
def get_connected_source(request: ConnectedSourceDTO):
    try:
        session = SessionLocal()

        integrations = []

        github_repos = (
            session.query(Repository)
            .filter(Repository.user_id == request.user_id)
            .all()
        )

        for repo in github_repos:
            integrations.append({
                "id": repo.id,
                "type": "repository",
                "name": repo.name,
                "metadata": {
                    "url": repo.url,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None
                }
            })

        return standard_response(
            success=True,
            message="success",
            data={"integrations": integrations},
        )

    except Exception as e:
        print(f"Error while fetching integrations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        session.close()
