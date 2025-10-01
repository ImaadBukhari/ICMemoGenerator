from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from db.models import User
from typing import Optional

security = HTTPBearer(auto_error=False)  # Make it optional

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user.
    For now, this is a simple implementation for testing.
    """
    # For demo purposes, we'll just get the first user or create one
    user = db.query(User).first()
    if not user:
        # Create a demo user if none exists
        user = User(email="demo@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user