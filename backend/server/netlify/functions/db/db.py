# src/python_be/server/db_sync.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ...utils.settings import settings

DATABASE_URL = settings.DATABASE_URL  # e.g. "postgresql://user:pass@host:port/dbname"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    """
    Yields a SQLAlchemy Session (sync). Caller must close it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
