from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text

Base = declarative_base()

class Sitemap(Base):
    __tablename__ = "scraped_docs"

    id = Column(Integer, primary_key=True, index=True)
    site = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    slug = Column(String, nullable=False)
    markdown = Column(Text, nullable=False)
