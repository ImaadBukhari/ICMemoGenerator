import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    """Health check endpoint"""
    try:
        from database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {
            "status": "healthy", 
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database": "Connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database_error": str(e)
        }