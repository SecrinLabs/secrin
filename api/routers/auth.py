from datetime import timedelta, datetime
from jose import jwt

from fastapi import APIRouter, HTTPException
from api.models.auth import UserSignup, UserLogin
from api.core.auth import Auth
from api.utils.standard_response import standard_response
from api.utils.auth import create_access_token

from config import settings

router = APIRouter()

@router.post("/signup")
def user_signup(request: UserSignup):
    try:
        auth = Auth()
        user = auth.add_user(request.email, request.username, request.password)
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
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/login")
def user_login(request: UserLogin):
    auth = Auth()
    try:
        user = auth.login_user(request.email, request.password)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Generate JWT with GUID as subject
    token = create_access_token(str(user.guid))

    # ⚡ Optional: generate JWT token here instead of raw user
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