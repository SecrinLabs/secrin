from sqlalchemy.orm import sessionmaker

from packages.models import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
