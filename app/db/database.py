import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")  # Load environment variables from .env

# Decide which database to use - prioritize SQLITE for local development
SQLALCHEMY_DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URL") or os.environ.get("SQLITE_URL")

# If no environment URL is provided, use absolute path for SQLite
if not SQLALCHEMY_DATABASE_URL:
    db_path = PROJECT_ROOT / "fitaccess.db"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# SQLite needs this extra argument
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()