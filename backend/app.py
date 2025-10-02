import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from db import models

# Import routers
from routes import auth, memo, data, affinity

# Create database tables (only in development)
if os.getenv("ENVIRONMENT") != "production":
    models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IC Memo Generator API",
    description="Investment Committee Memo Generation System",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://icmemo-frontend-khp3cr2i6q-uc.a.run.app",
    "https://icmemo-frontend-742031099725.us-central1.run.app",
]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(memo.router, prefix="/api/memo", tags=["memo"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(affinity.router, prefix="/api/affinity", tags=["affinity"])

@app.get("/")
async def root():
    return {"message": "IC Memo Generator API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": os.getenv("ENVIRONMENT", "development")}