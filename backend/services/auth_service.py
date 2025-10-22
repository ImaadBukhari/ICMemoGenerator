"""
Google OAuth 2.0 authentication service
"""
import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests

from backend.database import get_db
from backend.db.models import User

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "yourcompany.com")

def verify_google_token(token: str) -> Dict[str, Any]:
    """Verify Google OAuth token and return user info"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )
        return idinfo
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")

def validate_domain(email: str) -> bool:
    """Validate that email is from allowed domain"""
    if not email or "@" not in email:
        return False
    
    domain = email.split("@")[1].lower()
    return domain == ALLOWED_DOMAIN.lower()

def get_or_create_user(db: Session, email: str) -> User:
    """Get existing user or create new user"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def get_current_user(authorization: Optional[str] = Depends(lambda: None), db: Session = Depends(get_db)) -> User:
    """Dependency to get current authenticated user from Google OAuth token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Remove "Bearer " prefix if present
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    try:
        # Verify Google token
        idinfo = verify_google_token(token)
        email = idinfo.get("email")
        
        if not email:
            raise HTTPException(status_code=401, detail="No email in token")
        
        # Validate domain
        if not validate_domain(email):
            raise HTTPException(status_code=403, detail=f"Access denied. Only {ALLOWED_DOMAIN} emails allowed")
        
        # Get or create user
        user = get_or_create_user(db, email)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def get_current_user_optional(db: Session = Depends(get_db)) -> Optional[User]:
    """Optional authentication - returns None if not authenticated"""
    try:
        # This would need to be called with a token in a real implementation
        # For now, return None to indicate no authentication
        return None
    except:
        return None