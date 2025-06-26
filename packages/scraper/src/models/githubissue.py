from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models import Base

class PullRequest(Base):
    __tablename__ = "pull_request"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    merged_at = Column(DateTime, nullable=False)

    closing_issues = relationship("Issue", back_populates="pull_request", cascade="all, delete-orphan")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    closed_at = Column(DateTime, nullable=False)

    pull_request_id = Column(Integer, ForeignKey("pull_request.id"), nullable=False)
    pull_request = relationship("PullRequest", back_populates="closing_issues")
