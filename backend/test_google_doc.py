#!/usr/bin/env python3
"""
Simple test script for Google Doc creation.
Run from project root: python backend/test_google_doc.py
OR from backend directory: python -m test_google_doc (with __main__.py setup)
"""
import sys
import os
from pathlib import Path

# Add project root to path so 'backend' imports work
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from backend.database import SessionLocal
from backend.db.models import User
from backend.services.document_service import build_section_blocks
from backend.services.google_service import create_google_doc_from_blocks, get_drive_service, _get_drive_id, _get_folder_id

def test_google_doc_creation():
    """Test Google Doc creation with sample data"""
    db = SessionLocal()
    
    try:
        # Get first user (or modify to use a specific user)
        user = db.query(User).first()
        if not user:
            print("❌ No users found in database. Please create a user first.")
            return
        
        print(f"✅ Using user: {user.email}")
        
        # Create sample sections dict
        class MockSection:
            def __init__(self, name, content):
                self.section_name = name
                self.content = content
                self.data_sources = []
        
        # Sample sections for testing
        sections_dict = {
            "executive_summary": MockSection(
                "executive_summary",
                "This is a test executive summary. The company is doing well."
            ),
            "company_snapshot": MockSection(
                "company_snapshot",
                "Company Name: Test Company\nIndustry: Technology\nFounded: 2020"
            ),
            "people": MockSection(
                "people",
                "The team consists of experienced professionals:\n- CEO: John Doe\n- CTO: Jane Smith"
            ),
            "product": MockSection(
                "product",
                "The product is innovative and solves real problems."
            )
        }
        
        # Sample assessment sections
        assessment_sections = {
            "assessment_people": MockSection(
                "assessment_people",
                "Rating: 8/10\nStrong leadership team with relevant experience."
            ),
            "assessment_product": MockSection(
                "assessment_product",
                "Rating: 7/10\nSolid product with good market fit."
            )
        }
        
        print("📝 Building section blocks...")
        blocks = build_section_blocks(sections_dict, assessment_sections)
        print(f"✅ Created {len(blocks)} blocks")
        
        # Get Investments folder ID
        print("🔍 Finding Investments folder...")
        drive_service = get_drive_service(user, db)
        drive_id = _get_drive_id(drive_service, "Wyld VC")
        print(f"✅ Found drive: Wyld VC (ID: {drive_id})")
        
        investments_folder_id = _get_folder_id(drive_service, "Investments", drive_id)
        print(f"✅ Found folder: Investments (ID: {investments_folder_id})")
        
        # Create Google Doc
        print("📄 Creating Google Doc...")
        doc_title = "Test IC Memo: Test Company"
        doc_url = create_google_doc_from_blocks(
            user=user,
            db=db,
            title=doc_title,
            blocks=blocks,
            parent_folder_id=investments_folder_id
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"📄 Google Doc created: {doc_url}")
        print(f"📍 Location: Wyld VC → Investments folder")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Testing Google Doc Creation\n")
    test_google_doc_creation()

