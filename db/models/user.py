import uuid
from sqlalchemy import Column, Integer, String, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID

from db.index import Base
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    guid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=True)
    password_hash = Column(Text, nullable=False)
    github_installation_id = Column(BigInteger, nullable=True)

