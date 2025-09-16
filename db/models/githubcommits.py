from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from db.index import Base

class GithubCommit(Base):
    __tablename__ = "githubcommits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sha = Column(String(64), unique=True, nullable=False)
    message = Column(Text)
    author_name = Column(Text)
    author_email = Column(Text)
    author_date = Column(DateTime(timezone=True))
    committer_name = Column(Text)
    committer_email = Column(Text)
    committer_date = Column(DateTime(timezone=True))
    html_url = Column(Text)
    raw_payload = Column(JSONB)
    inserted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: one commit → many files
    files = relationship("GithubCommitFile", back_populates="commit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GithubCommit sha={self.sha} user_id={self.user_id}>"
    
class GithubCommitFile(Base):
    __tablename__ = "githubcommitfiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    commit_sha = Column(String(64), ForeignKey("githubcommits.sha", ondelete="CASCADE"), nullable=False)
    filename = Column(Text)
    status = Column(Text)  # added / modified / removed
    additions = Column(Integer)
    deletions = Column(Integer)
    changes = Column(Integer)
    patch = Column(Text)

    # Relationship: each file belongs to one commit
    commit = relationship("GithubCommit", back_populates="files")

    def __repr__(self):
        return f"<GithubCommitFile filename={self.filename} status={self.status}>"