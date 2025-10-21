import os
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from backend.database import get_db
from backend.db.models import User, GoogleToken
from backend.auth import get_current_user

# This file handles Google OAuth2 authentication and token management

router = APIRouter()

# Google OAuth2 configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents'
]

def create_flow():
    """Create Google OAuth2 flow"""
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow

@router.get("/auth/google/login")
async def google_login(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate Google OAuth2 login flow
    """
    try:
        flow = create_flow()
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Store state in session or database (you might want to use Redis for this)
        # For now, we'll store it in the user session or pass it in the authorization URL
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=f"{current_user.id}:{state}",  # Include user ID in state
            prompt='consent'  # Force consent to get refresh token
        )
        
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate Google OAuth: {str(e)}")

@router.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth2 callback
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code or state")
    
    try:
        # Parse user ID from state
        user_id_str, _ = state.split(':', 1)
        user_id = int(user_id_str)
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Exchange authorization code for tokens
        flow = create_flow()
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Store or update tokens in database
        existing_token = db.query(GoogleToken).filter(
            GoogleToken.user_id == user_id
        ).first()
        
        if existing_token:
            # Update existing token
            existing_token.access_token = credentials.token
            existing_token.refresh_token = credentials.refresh_token
            existing_token.expiry = credentials.expiry
        else:
            # Create new token record
            new_token = GoogleToken(
                user_id=user_id,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expiry=credentials.expiry
            )
            db.add(new_token)
        
        db.commit()
        
        # Redirect to frontend success page
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return RedirectResponse(url=f"{frontend_url}/dashboard?google_connected=true")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process Google callback: {str(e)}")

@router.delete("/auth/google/disconnect")
async def disconnect_google(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect user's Google account
    """
    try:
        token_record = db.query(GoogleToken).filter(
            GoogleToken.user_id == current_user.id
        ).first()
        
        if token_record:
            db.delete(token_record)
            db.commit()
            return {"message": "Google account disconnected successfully"}
        else:
            raise HTTPException(status_code=404, detail="No Google account connected")
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to disconnect Google account: {str(e)}")

@router.get("/auth/google/status")
async def google_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user has Google account connected
    """
    token_record = db.query(GoogleToken).filter(
        GoogleToken.user_id == current_user.id
    ).first()
    
    return {
        "connected": token_record is not None,
        "expires_at": token_record.expiry.isoformat() if token_record and token_record.expiry else None
    }