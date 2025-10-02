import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Don't create tables on startup in production
# from database import engine
# from db import models
# if os.getenv("ENVIRONMENT") != "production":
#     models.Base.metadata.create_all(bind=engine)

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

# Include routers - only add working ones
try:
    from routes import auth
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    print("✅ Auth routes loaded")
except Exception as e:
    print(f"⚠️  Auth routes failed: {e}")

try:
    from routes import data
    app.include_router(data.router, prefix="/api/data", tags=["data"])
    print("✅ Data routes loaded")
except Exception as e:
    print(f"⚠️  Data routes failed: {e}")

try:
    from routes import affinity
    app.include_router(affinity.router, prefix="/api/affinity", tags=["affinity"])
    print("✅ Affinity routes loaded")
except Exception as e:
    print(f"⚠️  Affinity routes failed: {e}")

# Skip memo routes for now if they import missing Memo model
try:
    from routes import memo
    app.include_router(memo.router, prefix="/api/memo", tags=["memo"])
    print("✅ Memo routes loaded")
except Exception as e:
    print(f"⚠️  Memo routes failed: {e}")

@app.get("/")
async def root():
    return {"message": "IC Memo Generator API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": os.getenv("ENVIRONMENT", "development")}