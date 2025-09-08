from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

from config import settings

Base = declarative_base()

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
