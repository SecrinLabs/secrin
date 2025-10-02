from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from db.models.user import User
from db.index import SessionLocal
from api.utils.auth import decode_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class Auth:
    # Add new user
    def add_user(self, email: str, username: str, password: str):
        session: Session = SessionLocal()
        try:
            user = session.query(User).filter(User.email == email).first()
            if user:
                raise HTTPException(status_code=400, detail="Email not available")
            
            hashed_password = pwd_context.hash(password)
            
            user = User(
                email=email,
                username=username,
                password_hash=hashed_password
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def invite_user(self, email: str, username: str) -> User:
        session: Session = SessionLocal()
        try:
            # Check if email already exists
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email not available")

            # Create user with pending status, password_hash=None
            user = User(
                email=email,
                username=username,
                password_hash=None,       # password to be set later via invite link
                status=0,                 # 0 = pending
            )

            session.add(user)
            session.commit()
            session.refresh(user)
            return user

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()

    # Update existing user
    def update_user(self, user_id: int, **kwargs):
        session: Session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # Get existing user
    def get_user(self, user_id: int):
        session: Session = SessionLocal()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def get_user_by_email(self, email: str):
        session: Session = SessionLocal()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    # Verify password
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    # Login user
    def login_user(self, email: str, password: str):
        user = self.get_user_by_email(email)
        if not user:
            return None  # user not found
        if not self.verify_password(password, user.password_hash):
            return None  # invalid password
        return user
    
def get_db():
    db: Session = SessionLocal()  # create a new DB session
    try:
        yield db  # this will be injected into your route
    finally:
        db.close()
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        user_guid = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    user = db.query(User).filter(User.guid == user_guid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user