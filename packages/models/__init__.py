from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from packages.config import get_config

config = get_config()

Base = declarative_base()

engine = create_engine(config.database_url)