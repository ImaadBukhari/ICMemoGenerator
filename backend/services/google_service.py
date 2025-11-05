import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from backend.db.models import GoogleToken, User

# Secret Manager import (optional)
try:
    from google.cloud import secretmanager
    HAS_SECRET_MANAGER = True
except ImportError:
    HAS_SECRET_MANAGER = False

# Config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "icmemogenerator-475014")
DRIVE_TOKEN_SECRET_NAME = os.getenv("DRIVE_TOKEN_SECRET_NAME", "google-drive-oauth-tokens")
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",  # Full Drive access for domain sharing
    "https://www.googleapis.com/auth/documents"
]

def _get_creds_from_secret_manager() -> Optional[Credentials]:
    """
    Get Google Drive credentials from Google Cloud Secret Manager.
    Returns None if Secret Manager is not available or tokens not found.
    Raises ValueError with detailed error message if Secret Manager access fails.
    """
    if not HAS_SECRET_MANAGER:
        error_msg = "Secret Manager not available (google-cloud-secret-manager not installed)"
        print(f"⚠️ {error_msg}")
        raise ValueError(error_msg)
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{GOOGLE_CLOUD_PROJECT}/secrets/{DRIVE_TOKEN_SECRET_NAME}"
        
        # Get the latest version of the secret
        version_path = f"{secret_path}/versions/latest"
        print(f"🔍 Attempting to access Secret Manager: {version_path}")
        print(f"   Project: {GOOGLE_CLOUD_PROJECT}")
        print(f"   Secret Name: {DRIVE_TOKEN_SECRET_NAME}")
        
        response = client.access_secret_version(request={"name": version_path})
        
        # Parse token data
        token_data = json.loads(response.payload.data.decode("UTF-8"))
        print(f"✅ Successfully retrieved token from Secret Manager")
        
        # Validate required fields
        if not token_data.get("token") or not token_data.get("refresh_token"):
            error_msg = f"Secret Manager token missing required fields (token or refresh_token). Secret: {DRIVE_TOKEN_SECRET_NAME}, Project: {GOOGLE_CLOUD_PROJECT}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Create credentials object
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id") or GOOGLE_CLIENT_ID,
            client_secret=token_data.get("client_secret") or GOOGLE_CLIENT_SECRET,
            scopes=token_data.get("scopes", SCOPES),
        )
        
        # If token expired, refresh it
        if creds.expired and creds.refresh_token:
            try:
                print("🔄 Refreshing expired Secret Manager token...")
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Failed to refresh Secret Manager token: {str(e)}")
                import traceback
                traceback.print_exc()
                raise ValueError(f"Google Drive token expired and could not be refreshed: {str(e)}")
        
        print("✅ Using credentials from Secret Manager (investments@wyldvc.com)")
        return creds
        
    except ValueError:
        # Re-raise ValueError as-is (these are our validation errors)
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        detailed_error = (
            f"Secret Manager access failed: {error_type}: {error_msg}. "
            f"Project: {GOOGLE_CLOUD_PROJECT}, "
            f"Secret: {DRIVE_TOKEN_SECRET_NAME}. "
            f"Please verify the secret exists and the Cloud Run service account has 'Secret Manager Secret Accessor' role."
        )
        print(f"❌ Secret Manager error: {error_type}: {error_msg}")
        print(f"   Project: {GOOGLE_CLOUD_PROJECT}")
        print(f"   Secret Name: {DRIVE_TOKEN_SECRET_NAME}")
        import traceback
        traceback.print_exc()
        raise ValueError(detailed_error)

def _get_user_creds(user: User, db: Session) -> Credentials:
    """
    Build Google Credentials object from Secret Manager or user's stored tokens.
    Priority: Secret Manager first (investments@wyldvc.com), then user tokens.
    """
    # Try Secret Manager first (for investments@wyldvc.com - this is the primary method)
    secret_manager_error = None
    try:
        secret_manager_creds = _get_creds_from_secret_manager()
        if secret_manager_creds:
            return secret_manager_creds
    except ValueError as e:
        # Capture the Secret Manager error for inclusion in final error message
        secret_manager_error = str(e)
        print(f"⚠️ Secret Manager failed: {secret_manager_error}")
    
    # Fall back to user's stored tokens (only if Secret Manager fails)
    print("⚠️ Secret Manager token not available, trying user tokens...")
    token_record = (
        db.query(GoogleToken).filter(GoogleToken.user_id == user.id).first()
    )
    if not token_record:
        error_msg = (
            "No Google Drive access available. "
        )
        if secret_manager_error:
            error_msg += f"Secret Manager error: {secret_manager_error}. "
        else:
            error_msg += (
                "Secret Manager token (investments@wyldvc.com) is not configured. "
            )
        error_msg += (
            "User has not connected Google Drive. "
            "Please ensure Secret Manager token is set up correctly in Cloud Secret Manager."
        )
        raise ValueError(error_msg)

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

    print("✅ Using user's Google tokens")
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

def _get_drive_id(service, drive_name: str) -> str:
    """Get a shared drive ID by name."""
    response = service.drives().list().execute()
    for d in response.get('drives', []):
        if d['name'].lower() == drive_name.lower():
            return d['id']
    raise ValueError(f"Shared drive '{drive_name}' not found")

def _get_folder_id(service, folder_name: str, drive_id: str, parent_id: str = None) -> str:
    """Get a folder ID by name, optionally within a parent folder."""
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query,
        corpora="drive",
        driveId=drive_id,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields="files(id, name)"
    ).execute()

    folders = results.get('files', [])
    if not folders:
        raise ValueError(f"Folder '{folder_name}' not found (parent: {parent_id})")
    return folders[0]['id']

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

def create_google_doc_from_blocks(user: User, db: Session, title: str, blocks: List[Dict[str, Any]], parent_folder_id: str = None) -> str:
    """
    Create a Google Doc from structured blocks and optionally move it to a folder.
    
    Args:
        user: User object
        db: Database session
        title: Document title
        blocks: List of block dicts with 'type' and 'content'/'items'/'table_data'
        parent_folder_id: Optional folder ID to move the document to
        
    Returns:
        Google Doc web view URL
    """
    docs_service = get_docs_service(user, db)
    drive_service = get_drive_service(user, db)
    
    # Create empty document
    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    
    # Build content and track formatting positions
    requests = []
    current_index = 1  # Start at beginning of document
    
    # Track formatting ranges for later application
    formatting_ranges = []  # (type, start_idx, end_idx, bold_ranges)
    
    for block in blocks:
        block_type = block.get('type')
        
        if block_type == 'title':
            # Title: size 12pt, bold
            text = block.get('content', '')
            start_idx = current_index
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": f"{text}\n"
                }
            })
            current_index += len(text) + 1
            formatting_ranges.append(('title', start_idx, current_index - 1, []))
            
        elif block_type == 'subtitle':
            # Subtitle: size 10pt, not bold
            text = block.get('content', '')
            start_idx = current_index
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": f"{text}\n"
                }
            })
            current_index += len(text) + 1
            formatting_ranges.append(('subtitle', start_idx, current_index - 1, []))
            
        elif block_type == 'section_heading':
            # Section heading: size 12pt, bold
            text = block.get('content', '')
            start_idx = current_index
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": f"{text}\n"
                }
            })
            current_index += len(text) + 1
            formatting_ranges.append(('section_heading', start_idx, current_index - 1, []))
            
        elif block_type == 'subsection_header':
            # Subsection header: size 10pt, bold
            text = block.get('content', '')
            start_idx = current_index
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": f"{text}\n"
                }
            })
            current_index += len(text) + 1
            formatting_ranges.append(('subsection_header', start_idx, current_index - 1, []))
            
        elif block_type == 'bold_header':
            # Bold header: size 10pt, bold, new line
            text = block.get('content', '')
            start_idx = current_index
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": f"{text}\n"
                }
            })
            current_index += len(text) + 1
            formatting_ranges.append(('bold_header', start_idx, current_index - 1, []))
            
        elif block_type == 'paragraph':
            # Paragraph: size 10pt, not bold (with potential inline bold ranges)
            text = block.get('content', '').strip()
            bold_ranges = block.get('bold_ranges', [])
            if text:
                start_idx = current_index
                requests.append({
                    "insertText": {
                        "location": {"index": current_index},
                        "text": f"{text}\n\n"
                    }
                })
                current_index += len(text) + 2
                formatting_ranges.append(('paragraph', start_idx, current_index - 2, bold_ranges))
                
        elif block_type == 'bullet_list':
            # Bullet list: size 10pt, not bold
            items = block.get('items', [])
            for item in items:
                text = str(item).strip()
                if text:
                    requests.append({
                        "insertText": {
                            "location": {"index": current_index},
                            "text": f"• {text}\n"
                        }
                    })
                    current_index += len(f"• {text}\n")
            requests.append({
                "insertText": {
                    "location": {"index": current_index},
                    "text": "\n"
                }
            })
            current_index += 1
            
        elif block_type == 'table':
            # Table: skip - we're not using tables anymore
            # This block type is kept for backward compatibility but won't be processed
            pass
    
    # Execute text insertion requests first
    if requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests}
        ).execute()
    
    # Get updated document to apply formatting
    document = docs_service.documents().get(documentId=doc_id).execute()
    body = document.get('body', {})
    content = body.get('content', [])
    
    # Build format requests by walking through document and matching with blocks
    format_requests = []
    block_idx = 0
    
    # Walk through document content and match with blocks
    for element in content:
        if 'paragraph' in element:
            para = element['paragraph']
            if 'elements' in para and len(para['elements']) > 0:
                # Get the text run to find its indices
                first_elem = para['elements'][0]
                if 'textRun' in first_elem:
                    start_idx = first_elem.get('startIndex', 0)
                    text_run = first_elem['textRun']
                    text_content = text_run.get('content', '')
                    
                    # Find the end index - strip trailing newlines but keep the range valid
                    text_stripped = text_content.rstrip('\n')
                    if not text_stripped:
                        # Empty paragraph, skip it
                        continue
                    
                    end_idx = start_idx + len(text_stripped)
                    
                    # Skip if empty range
                    if start_idx >= end_idx:
                        continue
                    
                    # Match with block based on position
                    # Skip empty paragraph blocks
                    while block_idx < len(blocks):
                        block = blocks[block_idx]
                        block_type = block.get('type')
                        
                        # Skip empty paragraph blocks
                        if block_type == 'paragraph':
                            text = block.get('content', '').strip()
                            if not text:
                                block_idx += 1
                                continue
                            break
                        else:
                            break
                    
                    if block_idx >= len(blocks):
                        continue
                    
                    block = blocks[block_idx]
                    block_type = block.get('type')
                    
                    if block_type in ['title', 'section_heading']:
                        # Size 12pt, bold
                        format_requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": start_idx,
                                    "endIndex": end_idx
                                },
                                "textStyle": {
                                    "fontSize": {"magnitude": 12, "unit": "PT"},
                                    "bold": True
                                },
                                "fields": "fontSize,bold"
                            }
                        })
                        block_idx += 1
                        
                    elif block_type == 'subtitle':
                        # Size 10pt, not bold
                        format_requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": start_idx,
                                    "endIndex": end_idx
                                },
                                "textStyle": {
                                    "fontSize": {"magnitude": 10, "unit": "PT"},
                                    "bold": False
                                },
                                "fields": "fontSize,bold"
                            }
                        })
                        block_idx += 1
                        
                    elif block_type == 'subsection_header':
                        # Size 10pt, bold
                        format_requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": start_idx,
                                    "endIndex": end_idx
                                },
                                "textStyle": {
                                    "fontSize": {"magnitude": 10, "unit": "PT"},
                                    "bold": True
                                },
                                "fields": "fontSize,bold"
                            }
                        })
                        block_idx += 1
                        
                    elif block_type == 'bold_header':
                        # Size 10pt, bold (detected title patterns)
                        format_requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": start_idx,
                                    "endIndex": end_idx
                                },
                                "textStyle": {
                                    "fontSize": {"magnitude": 10, "unit": "PT"},
                                    "bold": True
                                },
                                "fields": "fontSize,bold"
                            }
                        })
                        block_idx += 1
                        
                    elif block_type == 'paragraph':
                        # Size 10pt, not bold (with inline bold ranges)
                        text = block.get('content', '').strip()
                        bold_ranges = block.get('bold_ranges', [])
                        if text:
                            # Set base style
                            format_requests.append({
                                "updateTextStyle": {
                                    "range": {
                                        "startIndex": start_idx,
                                        "endIndex": end_idx
                                    },
                                    "textStyle": {
                                        "fontSize": {"magnitude": 10, "unit": "PT"},
                                        "bold": False
                                    },
                                    "fields": "fontSize,bold"
                                }
                            })
                            # Apply bold formatting for ranges
                            for bold_start, bold_end in bold_ranges:
                                if bold_start < len(text) and bold_end <= len(text):
                                    bold_start_idx = start_idx + bold_start
                                    bold_end_idx = start_idx + bold_end
                                    if bold_start_idx < bold_end_idx and bold_end_idx <= end_idx:
                                        format_requests.append({
                                            "updateTextStyle": {
                                                "range": {
                                                    "startIndex": bold_start_idx,
                                                    "endIndex": bold_end_idx
                                                },
                                                "textStyle": {
                                                    "bold": True
                                                },
                                                "fields": "bold"
                                            }
                                        })
                            block_idx += 1
    
    # Handle bullet list items separately - they appear as separate paragraphs
    bullet_block_idx = 0
    bullet_item_idx = 0
    for element in content:
        if 'paragraph' in element:
            para = element['paragraph']
            if 'elements' in para and len(para['elements']) > 0:
                first_elem = para['elements'][0]
                if 'textRun' in first_elem:
                    text_run = first_elem['textRun']
                    text_content = text_run.get('content', '')
                    # Check if it's a bullet (starts with bullet character)
                    if text_content.strip().startswith('•'):
                        start_idx = first_elem.get('startIndex', 0)
                        end_idx = start_idx + len(text_content.rstrip('\n'))
                        
                        if start_idx < end_idx:
                            format_requests.append({
                                "updateTextStyle": {
                                    "range": {
                                        "startIndex": start_idx,
                                        "endIndex": end_idx
                                    },
                                    "textStyle": {
                                        "fontSize": {"magnitude": 10, "unit": "PT"},
                                        "bold": False
                                    },
                                    "fields": "fontSize,bold"
                                }
                            })
    
    # Apply formatting
    if format_requests:
        # Filter out any requests with invalid ranges
        valid_requests = []
        for req in format_requests:
            if 'updateTextStyle' in req:
                range_obj = req['updateTextStyle']['range']
                if range_obj['startIndex'] < range_obj['endIndex']:
                    valid_requests.append(req)
        
        if valid_requests:
            # Process in chunks
            chunk_size = 100
            for i in range(0, len(valid_requests), chunk_size):
                chunk = valid_requests[i:i + chunk_size]
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": chunk}
                ).execute()
    
    # Tables are now handled as formatted text, so no table insertion needed
    
    # Share with domain (wyldvc.com) - make it available to anyone in the domain with edit access
    try:
        permission = {
            'type': 'domain',
            'role': 'writer',
            'domain': 'wyldvc.com'
        }
        drive_service.permissions().create(
            fileId=doc_id,
            body=permission,
            supportsAllDrives=True
        ).execute()
        print(f"✅ Document shared with wyldvc.com domain")
    except Exception as e:
        print(f"Warning: Could not share document with domain: {e}")
    
    return f"https://docs.google.com/document/d/{doc_id}/edit"