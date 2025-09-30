import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from backend.db.models import GoogleToken, User

# Config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents"
]

def _get_user_creds(user: User, db: Session) -> Credentials:
    """
    Build Google Credentials object from stored tokens for a given user.
    """
    token_record = (
        db.query(GoogleToken).filter(GoogleToken.user_id == user.id).first()
    )
    if not token_record:
        raise ValueError("No Google tokens found for user")

    creds = Credentials(
        token=token_record.access_token,
        refresh_token=token_record.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    # If token refreshed, update DB
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_record.access_token = creds.token
        token_record.expiry = creds.expiry
        db.commit()

    return creds

def get_drive_service(user: User, db: Session):
    """Return an authenticated Google Drive service client."""
    creds = _get_user_creds(user, db)
    return build("drive", "v3", credentials=creds)

def get_docs_service(user: User, db: Session):
    """Return an authenticated Google Docs service client."""
    creds = _get_user_creds(user, db)
    return build("docs", "v1", credentials=creds)

def search_files(user: User, db: Session, query: str, max_results: int = 20):
    """
    Search for files in Google Drive for the given user.
    """
    service = get_drive_service(user, db)
    results = service.files().list(
        q=f"name contains '{query}' and trashed = false",
        pageSize=max_results,
        fields="files(id, name, mimeType, webViewLink, createdTime, modifiedTime)"
    ).execute()
    return results.get("files", [])

def create_doc(user: User, db: Session, title: str, content: dict):
    """
    Create a new Google Doc and insert structured content.
    """
    service = get_docs_service(user, db)

    # Create doc
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    # Insert content
    requests = []
    for section, text in content.items():
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": f"{section}\n{text}\n\n"
            }
        })

    if requests:
        service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()

    return f"https://docs.google.com/document/d/{doc_id}/edit"