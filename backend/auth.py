from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.db.models import User

router = APIRouter()

def get_current_user(db: Session = Depends(get_db)):
    """Dependency to get current authenticated user"""
    # For development, create or get a test user
    user = db.query(User).first()
    if not user:
        user = User(
            email="test@example.com"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

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