from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the directory of this file
current_dir = Path(__file__).parent

# Load .env from the backend directory
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Import Base from models so it can be re-exported
from backend.db.models import Base

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables. Check your .env file.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Export SessionLocal so background tasks can use it
__all__ = ['Base', 'engine', 'SessionLocal', 'get_db']