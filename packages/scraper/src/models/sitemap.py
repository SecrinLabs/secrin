from sqlalchemy import Column, Integer, String, Text
from . import Base

class Sitemap(Base):
    __tablename__ = "software_docs"

    id = Column(Integer, primary_key=True, index=True)
    site = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    slug = Column(String, nullable=False)
    markdown = Column(Text, nullable=False)
