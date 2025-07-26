from sqlalchemy import Column, Integer, String, Boolean, JSON

from . import Base

class Integration(Base):
    __tablename__ = "Integration"

    Id = Column(Integer, primary_key=True)
    Name = Column(String, nullable=False)
    IsOpen = Column(Boolean, nullable=False)
    Config = Column(JSON, nullable=True)