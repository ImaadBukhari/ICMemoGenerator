from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

from backend.db.models import Base
from backend.routes.auth import router as auth_router
from backend.routes.memo import router as memo_router
from backend.routes.affinity import router as affinity_router
from backend.routes.data import router as data_router

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IC Memo Generator", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(memo_router, prefix="/api")
app.include_router(affinity_router, prefix="/api")
app.include_router(data_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "IC Memo Generator API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}