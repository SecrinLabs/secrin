
import os
from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime, timedelta

from api.models.auth import UserInvite, UserLogin
from api.core.auth import Auth
from api.utils.standard_response import standard_response
from api.utils.auth import create_access_token, generate_invite_token
from config import get_logger, settings
from mails.factory import EmailFactory, MailType
from mails.types import MailType

logger = get_logger(__name__)

router = APIRouter()

@router.post("/invite-user")
def invite_user(request: UserInvite):
    logger.info(f"Invite attempt for email={request.email}")

    try:
        auth = Auth()
        user = auth.invite_user(request.email, request.username)
        logger.info(f"✅ User created with pending status user_id={user.id}, email={user.email}")

        # Generate invite token
        token = generate_invite_token(user.email)
        invite_link = f"{settings.FRONTEND_URL}/set-password?token={token}"

        # Render email template
        html_body = EmailFactory.render(
            MailType.INVITE,
            {"invite_link": invite_link, "user_name": user.username}
        )

        # send_email(to=user.email, subject="You're invited!", html_body=html_body)

        return standard_response(
            success=True,
            message="Signup successful",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ Signup failed for email={request.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.post("/login")
def user_login(request: UserLogin):
    logger.info(f"Login attempt for email={request.email}")

    auth = Auth()
    try:
        user = auth.login_user(request.email, request.password)
    except Exception as e:
        logger.error(f"❌ Login DB lookup failed for email={request.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

    if not user:
        logger.warning(f"⚠️ Invalid login attempt for email={request.email}")
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Generate JWT with GUID as subject
    token = create_access_token(str(user.guid))

    logger.info(f"✅ Login successful for user_id={user.id}, email={user.email}")

    return standard_response(
        success=True,
        message="Login successful",
        data={
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "userGUID": user.guid
            },
            "access_token": token
        }
    )
