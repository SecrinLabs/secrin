from sqlalchemy import Column, Integer, String, Text

from . import Base

class Sitemap(Base):
    __tablename__ = "Docs"

    Id = Column(Integer, primary_key=True, index=True)
    Site = Column(String, nullable=False)
    URL = Column(String, unique=True, nullable=False)
    Slug = Column(String, nullable=False)
    Markdown = Column(Text, nullable=False)
