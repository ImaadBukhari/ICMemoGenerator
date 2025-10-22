from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.database import get_db
from backend.db.models import User
from backend.services.auth_service import (
    verify_google_token, 
    validate_domain,
    get_or_create_user
)

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    credential: str  # Google OAuth credential

class AuthResponse(BaseModel):
    authenticated: bool = True
    user: dict

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Dependency to get current authenticated user from Google OAuth token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Remove "Bearer " prefix if present
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    try:
        # Verify Google token
        idinfo = verify_google_token(token)
        email = idinfo.get("email")
        
        if not email:
            raise HTTPException(status_code=401, detail="No email in token")
        
        # Validate domain
        if not validate_domain(email):
            raise HTTPException(status_code=403, detail="Access denied. Only company domain emails allowed")
        
        # Get or create user
        user = get_or_create_user(db, email)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@router.post("/auth/google-login", response_model=AuthResponse)
async def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Login with Google OAuth credential"""
    try:
        # Verify Google token
        idinfo = verify_google_token(request.credential)
        email = idinfo.get("email")
        
        if not email:
            raise HTTPException(status_code=401, detail="No email in Google token")
        
        # Validate domain
        if not validate_domain(email):
            raise HTTPException(status_code=403, detail="Access denied. Only company domain emails allowed")
        
        # Get or create user
        user = get_or_create_user(db, email)
        
        return AuthResponse(
            authenticated=True,
            user={
                "id": user.id,
                "email": user.email,
                "name": idinfo.get("name", ""),
                "picture": idinfo.get("picture", "")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(e)}")

@router.get("/auth/status")
async def auth_status(current_user: User = Depends(get_current_user)):
    """Check authentication status"""
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email
        }
    }

@router.post("/auth/verify")
async def verify_auth(current_user: User = Depends(get_current_user)):
    """Verify current authentication"""
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email
        }
    }

@router.get("/auth/test")
async def test_route():
    return {"message": "Auth router is working"}