from sqlalchemy import Column, Integer, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from db.index import Base
import enum

class IntegrationType(enum.Enum):
    github = "github"
    discord = "discord"
    slack = "slack"

class Integration(Base):
    __tablename__ = "integration"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(IntegrationType, name="integration_type"), nullable=False)
    config = Column(JSON, nullable=False, default=dict)