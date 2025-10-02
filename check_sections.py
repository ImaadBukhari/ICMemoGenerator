import os
import sys
from sqlalchemy.orm import Session

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from backend.database import get_db
from backend.db.models import MemoRequest, MemoSection

def check_memo_sections():
    """Check what sections exist in the database"""
    
    db = next(get_db())
    
    # Get all memo requests
    memo_requests = db.query(MemoRequest).all()
    print(f"Found {len(memo_requests)} memo requests:")
    
    for memo in memo_requests:
        print(f"\nMemo ID: {memo.id}")
        print(f"Company: {memo.company_name}")
        print(f"Status: {memo.status}")
        print(f"Created: {memo.created_at}")
        
        # Get sections for this memo
        sections = db.query(MemoSection).filter(
            MemoSection.memo_request_id == memo.id
        ).all()
        
        print(f"Sections found: {len(sections)}")
        
        for section in sections:
            print(f"  - {section.section_name}: {section.status} ({len(section.content) if section.content else 0} chars)")
            if section.status == "failed" and section.error_log:
                print(f"    Error: {section.error_log}")
    
    db.close()

if __name__ == "__main__":
    check_memo_sections()