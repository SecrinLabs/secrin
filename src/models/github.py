from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Repository(Base):
    __tablename__ = 'repositories'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    owner = Column(String)
    url = Column(String)

    pull_requests = relationship("PullRequest", back_populates="repo")
    issues = relationship("Issue", back_populates="repo")

class PullRequest(Base):
    __tablename__ = 'pull_requests'
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('repositories.id'))
    number = Column(Integer)
    title = Column(String)
    url = Column(String)
    merged_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    repo = relationship("Repository", back_populates="pull_requests")
    issues = relationship("Issue", secondary="pull_request_issues", back_populates="pull_requests")

class Issue(Base):
    __tablename__ = 'issues'
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('repositories.id'))
    number = Column(Integer)
    title = Column(String)
    url = Column(String)
    closed_at = Column(DateTime)

    repo = relationship("Repository", back_populates="issues")
    pull_requests = relationship("PullRequest", secondary="pull_request_issues", back_populates="issues")

pull_request_issues = Table(
    "pull_request_issues", Base.metadata,
    Column("pull_request_id", ForeignKey("pull_requests.id"), primary_key=True),
    Column("issue_id", ForeignKey("issues.id"), primary_key=True),
)

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    slug = Column(String)
    path = Column(String)
    content = Column(Text)
    tags = Column(ARRAY(String))
    embedding = Column(Vector(768))  # assuming 768-d vector
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
