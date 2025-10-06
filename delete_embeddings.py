import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import SessionLocal
from backend.db.models import DocumentEmbedding

db = SessionLocal()
try:
    # Delete ALL old embeddings
    deleted = db.query(DocumentEmbedding).delete()
    db.commit()
    print(f"✅ Deleted {deleted} old embeddings")
finally:
    db.close()