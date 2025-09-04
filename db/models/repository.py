from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from db.index import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(255), nullable=False)