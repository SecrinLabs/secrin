import uuid
from sqlalchemy import Column, Integer, String, Text, SmallInteger
from sqlalchemy.dialects.postgresql import UUID

from db.index import Base
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    guid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), nullable=True)
    password_hash = Column(Text, nullable=True)
    status = Column(SmallInteger, nullable=False, default=0)  # 0 = pending, 1 = active

