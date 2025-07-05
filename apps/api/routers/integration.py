from fastapi import APIRouter, HTTPException

from packages.db.db import SessionLocal
from packages.models.integrations import Integration
from apps.api.models.UpdateIntegrationRequest import UpdateIntegrationRequest

router = APIRouter()

@router.get("/")
def list_integrations():
    session = SessionLocal()
    try:
        integrations = session.query(Integration).all()
        return [
            {
                "id": i.id,
                "name": i.name,
                "is_connected": i.is_connected,
                "config": i.config
            } for i in integrations
        ]
    finally:
        session.close()

@router.patch("/toggle")
def toggle_integration(name: str):
    session = SessionLocal()
    try:
        integration = session.query(Integration).filter_by(name=name).first()
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        integration.is_connected = not integration.is_connected
        session.commit()
        return {"message": "done", "is_connected": integration.is_connected}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@router.patch("/update")
def update_integration(request: UpdateIntegrationRequest):
    session = SessionLocal()
    try:
        integration = session.query(Integration).filter_by(name=request.name).first()
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        integration.is_connected = request.is_connected
        integration.config = request.config
        session.commit()
        return {"message": "Updated", "name": request.name, "is_connected": request.is_connected, "config": request.config}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
