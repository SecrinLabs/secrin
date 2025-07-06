from .db import SessionLocal
from packages.models.integrations import Integration
from typing import List, Optional, Dict, Any
from apps.api.models.UpdateIntegrationRequest import UpdateIntegrationRequest
from sqlalchemy.orm import Session


def get_all_integrations(session: Optional[Session] = None) -> List[Dict[str, Any]]:
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
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
        if close_session:
            session.close()

def toggle_integration_connection(name: str, session: Optional[Session] = None) -> Dict[str, Any]:
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    try:
        integration = session.query(Integration).filter_by(name=name).first()
        if not integration:
            return {"error": "Integration not found"}
        integration.is_connected = not integration.is_connected
        session.commit()
        return {"message": "done", "is_connected": integration.is_connected}
    except Exception as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        if close_session:
            session.close()

def update_integration(request: UpdateIntegrationRequest, session: Optional[Session] = None) -> Dict[str, Any]:
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    try:
        integration = session.query(Integration).filter_by(name=request.name).first()
        if not integration:
            return {"error": "Integration not found"}
        integration.is_connected = request.is_connected
        integration.config = request.config
        session.commit()
        return {"message": "Updated", "name": request.name, "is_connected": request.is_connected, "config": request.config}
    except Exception as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        if close_session:
            session.close()
