from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine


Base = declarative_base()

engine = create_engine("postgresql://postgres:10514912@localhost:5432/devsecrin")