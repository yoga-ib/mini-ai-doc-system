import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Phase-2 compliant DB config
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./app.db"   # SQLite default
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite requirement
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
