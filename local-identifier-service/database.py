"""Database connection and setup."""
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from config import get_settings

settings = get_settings()
engine = sqlalchemy.create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
