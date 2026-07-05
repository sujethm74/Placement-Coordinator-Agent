"""
Database configuration.

Defaults to local SQLite for easy dev setup. To use PostgreSQL in
production, just set the DATABASE_URL environment variable, e.g.:

    export DATABASE_URL="postgresql://user:password@localhost:5432/placement_db"

No code changes are required to switch — SQLAlchemy handles both.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./placement.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
