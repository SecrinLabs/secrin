
import os
from fastapi import APIRouter, HTTPException
from jose import jwt, JWTError

from api.models.auth import UserInvite, UserLogin, SetPassword, ContactMessage
from api.core.auth import Auth
from api.utils.standard_response import standard_response
from api.utils.auth import create_access_token, generate_invite_token, validate_invite_token
from config import get_logger, settings
from mails.factory import EmailFactory, MailType
from mails.types import MailType

logger = get_logger(__name__)

router = APIRouter()

@router.post("/invite-user")
async def invite_user(request: UserInvite):
    logger.info(f"Invite attempt for email={request.email}")

    try:
        auth = Auth()
        user = auth.invite_user(request.email, request.username)
        logger.info(f"✅ User created with pending status user_id={user.id}, email={user.email}")

        # Generate invite token
        token = generate_invite_token(user.email)
        invite_link = f"{settings.FRONTEND_URL}/auth/invite?token={token}"

        EmailFactory.send(
            MailType.INVITE,
            user.email,
            {"invite_link": invite_link, "user_name": user.username},
            subject="You're invited!"
        )

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
    
@router.post("/set-password")
def set_password(request: SetPassword):    
    try:
        user_email = validate_invite_token(request.token)
        if not user_email:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    auth = Auth()
    user = auth.get_user_by_email(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.status == 1:
        raise HTTPException(status_code=400, detail="Password already set")
    
    auth.update_user_password(user, request.password)

    return {
        "success": True,
        "message": "Password set successfully, you can now log in",
        "data": {
            "user": {"email": user.email}
        },
    }
    
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

@router.post("/new-user-interest")
async def send_contact_email(data: ContactMessage):
    try:
        # Construct HTML email
        html = f"""
        <h3>New Contact Message</h3>
        <p><b>Name:</b> {data.name}</p>
        <p><b>Email:</b> {data.email}</p>
        <p><b>Subject:</b> {data.subject}</p>
        """

        EmailFactory.send(
            MailType.WAITINGLIST,
            "jenilsavani1@gmail.com",
            {"name": data.name, "email": data.email, "subject": data.subject},
            subject="new interested user!"
        )


        return standard_response(
            success=True,
            message="Login successful",
            data={}
        )

    except Exception as e:
        print("Error sending email:", e)
        raise HTTPException(status_code=500, detail="Failed to send email.")