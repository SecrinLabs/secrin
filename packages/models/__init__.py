from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine

DATABASE_URL="postgresql://postgres:10514912@localhost:5432/devsecrin"

Base = declarative_base()

engine = create_engine(DATABASE_URL)