"""
Database Connection and Session Factory for CloudGuard API.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
try:
    from app.config import settings
except ImportError:
    from .config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
