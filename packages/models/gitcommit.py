from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from . import Base

class GitCommit(Base):
    __tablename__ = "git_commits"

    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String, nullable=False)
    commit_hash = Column(String, unique=True, nullable=False)
    message = Column(Text, nullable=False)
    author = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    files = Column(JSONB, nullable=False)
    diff = Column(Text, nullable=False)
