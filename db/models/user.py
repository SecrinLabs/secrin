from sqlalchemy import Column, Integer, String, BigInteger, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=True)
    password_hash = Column(Text, nullable=False)
    github_installation_id = Column(BigInteger, nullable=True)
