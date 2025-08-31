from fastapi import APIRouter, HTTPException
from api.models.UserSignup import UserSignup
from api.models.UserLogin import UserLogin
from api.core.auth.index import Auth

router = APIRouter()

@router.post("/signup")
def user_signup(request: UserSignup):
    try:
        auth = Auth()
        user = auth.add_user(request.email, request.username, request.password)
        return {"user": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/login")
def user_login(request: UserLogin):
    try:
        auth = Auth()
        user = auth.login_user(request.email, request.password)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # ⚡ Optional: generate JWT token here instead of raw user
        return {"message": "Login successful", "user_id": user.id, "email": user.email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))