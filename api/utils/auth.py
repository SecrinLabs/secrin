from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError

from config import settings

def create_access_token(sub: str, expires_minutes: int = 60*24*7) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = {"sub": sub, "exp": expire}
    return jwt.encode(to_encode, settings.SESSION_SECRET_KEY, algorithm=settings.SESSION_ALGORITHM)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=[settings.SESSION_ALGORITHM])
        user_guid = payload.get("sub")
        if user_guid is None:
            raise JWTError("Missing subject claim")
        return user_guid
    except JWTError:
        raise JWTError("Token invalid or expired")
    
def generate_invite_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.now() + timedelta(days=7),
        "purpose": "invite"
    }
    return jwt.encode(payload, settings.SESSION_SECRET_KEY, algorithm=settings.SESSION_ALGORITHM)


def validate_invite_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=[settings.SESSION_ALGORITHM])
        if payload.get("purpose") != "invite":
            raise JWTError(status_code=400, detail="Invalid token purpose")
        return payload["email"]
    except jwt.ExpiredSignatureError:
        raise JWTError(status_code=400, detail="Invite token expired")
    except jwt.InvalidTokenError:
        raise JWTError(status_code=400, detail="Invalid token")