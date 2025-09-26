from sqlalchemy.orm import Session
from db.models.user import User
from db.index import SessionLocal
from passlib.context import CryptContext
from fastapi import HTTPException


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
            print(session.query(User).first())
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