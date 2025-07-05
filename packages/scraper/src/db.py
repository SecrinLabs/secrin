from sqlalchemy.orm import sessionmaker
from .models import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
