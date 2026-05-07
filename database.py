"""database.py

This file contains everything related to the database connection:
- MySQL connection URL
- SQLAlchemy engine
- SessionLocal (DB session factory)
- Base class for ORM models
- get_db dependency (FastAPI uses it to get a DB session per request)

Beginner note:
A "session" is how SQLAlchemy talks to the database.
We create one session per request, then close it after the request finishes.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _build_database_url() -> str:
    """Build a MySQL URL from environment variables.

    You can set these environment variables (recommended):
    - DB_USER
    - DB_PASSWORD
    - DB_HOST
    - DB_PORT
    - DB_NAME

    Example URL produced:
    mysql+pymysql://root:password@localhost:3306/student_db
    """

    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "password")
    # Using "localhost" is beginner-friendly and matches common MySQL user creation like:
    # CREATE USER 'student_user'@'localhost' ...
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "student_db")

    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


SQLALCHEMY_DATABASE_URL = _build_database_url()

# The engine is the "starting point" for SQLAlchemy.
# pool_pre_ping=True helps avoid stale connections.
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# SessionLocal creates database sessions.
# autocommit=False and autoflush=False are common beginner-friendly defaults.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is used to create ORM models (tables).
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session.

    Usage:
        def route(db: Session = Depends(get_db)):
            ...
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
