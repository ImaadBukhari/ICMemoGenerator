#!/usr/bin/env python3
"""
Simple Google Drive Token Generator

This script generates OAuth tokens for investments@wyldvc.com to access Google Drive.
It opens a browser automatically - just sign in and authorize.

Usage:
    python generate_drive_token.py

The output file will be: backend/drive_tokens.json
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/drive',  # Full Drive access for domain sharing
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents'
]

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "drive_tokens.json"
)

def main():
    # Get credentials from environment
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")
        print("\nSet them in your environment or .env file:")
        print("  export GOOGLE_CLIENT_ID='your-client-id'")
        print("  export GOOGLE_CLIENT_SECRET='your-client-secret'")
        return
    
    print("🔐 Google Drive Token Generator")
    print("=" * 50)
    print("\nThis will open a browser window.")
    print("Please sign in as investments@wyldvc.com and authorize the application.")
    print("\n⚠️  Make sure 'http://localhost:8080/' is in your OAuth authorized redirect URIs!\n")
    
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/"]
            }
        },
        SCOPES
    )
    
    # Use port 8080 to match your OAuth config
    # The redirect URI will be http://localhost:8080/
    try:
        creds = flow.run_local_server(port=8080)
    except Exception as e:
        if "redirect_uri_mismatch" in str(e).lower():
            print("\n❌ Redirect URI mismatch error!")
            print("\nTo fix this:")
            print("1. Go to Google Cloud Console > APIs & Services > Credentials")
            print("2. Click on your OAuth 2.0 Client ID")
            print("3. Under 'Authorized redirect URIs', add: http://localhost:8080/")
            print("4. Make sure to include the trailing slash!")
            print("5. Save and try again")
        raise
    
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
        'expiry': creds.expiry.isoformat() if creds.expiry else None
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"\n✅ Token saved to: {OUTPUT_FILE}")
    print("\nNext steps:")
    print("1. Upload this JSON file to Google Cloud Secret Manager:")
    print("   gcloud secrets create google-drive-oauth-tokens --data-file=backend/drive_tokens.json")
    print("   (or use 'gcloud secrets versions add' if it already exists)")
    print("2. The service will automatically use these tokens for Drive access")
    print("\n⚠️  Keep this file secure and don't commit it to git!")

if __name__ == '__main__':
    main()

