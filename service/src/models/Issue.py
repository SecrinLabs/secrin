from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from . import Base

class PullRequest(Base):
    __tablename__ = "PullRequest"

    Id = Column(Integer, primary_key=True)
    Number = Column(Integer, unique=True, nullable=False)
    Title = Column(String, nullable=False)
    Url = Column(String, nullable=True)
    MergedAt = Column(DateTime, nullable=True)
    Body = Column(String, nullable=True)
    Diff = Column(String, nullable=True)

    ClosedIssue = relationship("Issue", back_populates="PR", cascade="all, delete-orphan")

class Issue(Base):
    __tablename__ = "Issue"

    Id = Column(Integer, primary_key=True)
    Number = Column(Integer, nullable=False)
    Title = Column(String, nullable=False)
    Url = Column(String, nullable=True)
    ClosedAt = Column(DateTime, nullable=True)
    Body = Column(String, nullable=True)

    PRID = Column(Integer, ForeignKey("PullRequest.Id"), nullable=False)
    PR = relationship("PullRequest", back_populates="ClosedIssue")
