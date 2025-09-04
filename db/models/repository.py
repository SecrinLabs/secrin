from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, Boolean, Text, ARRAY
from sqlalchemy.orm import relationship
from db.index import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(255), nullable=False)
    repo_id = Column(BigInteger, nullable=True)                # GitHub repo id
    full_name = Column(String(255), nullable=True)             # owner/repo
    description = Column(Text, nullable=True)
    private = Column(Boolean, default=False)
    language = Column(String(50), nullable=True)
    topics = Column(ARRAY(String), nullable=True)              # Postgres array
    stargazers_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    watchers_count = Column(Integer, default=0)
    default_branch = Column(String(50), nullable=True)
    open_issues_count = Column(Integer, default=0)
    has_issues = Column(Boolean, default=True)
    has_discussions = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    pushed_at = Column(DateTime, nullable=True)
    clone_url = Column(Text, nullable=True)
    owner_login = Column(String(100), nullable=True)
    owner_type = Column(String(20), nullable=True)