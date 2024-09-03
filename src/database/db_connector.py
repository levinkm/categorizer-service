
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.utils.config_utils import config

db_config = config["database"]
# database credentials
DATABASE_USER = db_config["user"]
DATABASE_PASSWORD = db_config["password"]
DATABASE_HOST = db_config["host"]
DATABASE_PORT = int(db_config["port"])
DATABASE_NAME = db_config["name"]

# engine instance
DATABASE_URL = f"mysql+mysqlconnector://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
engine = create_engine(DATABASE_URL, echo=True)

# base class for declarative models
Base = declarative_base()

# session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
