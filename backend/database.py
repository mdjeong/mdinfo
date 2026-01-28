from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import Settings

SQLALCHEMY_DATABASE_URL = Settings.get_database_url()

# SQLite는 check_same_thread=False 필요, PostgreSQL은 불필요
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL, MySQL 등
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
