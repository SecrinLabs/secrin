# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     ForeignKey,
#     Text,
# )
# from sqlalchemy.orm import relationship
# from db.index import Base

# class GithubCommitFile(Base):
#     __tablename__ = "githubcommitfiles"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     commit_sha = Column(String(64), ForeignKey("githubcommits.sha", ondelete="CASCADE"), nullable=False)
#     filename = Column(Text)
#     status = Column(Text)  # added / modified / removed
#     additions = Column(Integer)
#     deletions = Column(Integer)
#     changes = Column(Integer)
#     patch = Column(Text)

#     # Relationship: each file belongs to one commit
#     commit = relationship("GithubCommit", back_populates="files")

#     def __repr__(self):
#         return f"<GithubCommitFile filename={self.filename} status={self.status}>"