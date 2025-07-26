from sqlalchemy.orm import sessionmaker

from src.models import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
