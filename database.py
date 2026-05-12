import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()


def _build_database_url() -> str:

    # If you provide a full SQLAlchemy URL, we use it as-is.
    # Examples:
    # - mysql+pymysql://user:pass@localhost:3306/student_db
    # - postgresql+psycopg2://user:pass@localhost:5432/student_db
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    dialect = os.getenv("DB_DIALECT", "mysql").strip().lower()
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "password")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "student_db")

    if dialect in {"mysql", "mariadb"}:
        db_port = os.getenv("DB_PORT", "3306")
        return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    if dialect in {"postgres", "postgresql"}:
        db_port = os.getenv("DB_PORT", "5432")
        return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    raise ValueError(
        "Unsupported DB_DIALECT. Use 'mysql' or 'postgresql', or provide DATABASE_URL."
    )


SQLALCHEMY_DATABASE_URL = _build_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():


    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
