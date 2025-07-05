from sqlalchemy import Column, Integer, String, Boolean, JSON

from . import Base

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_connected = Column(Boolean, nullable=False)
    config = Column(JSON, nullable=True)