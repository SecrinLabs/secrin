from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine

from config import settings

Base = declarative_base()

engine = create_engine(settings.DATABASE_URL)