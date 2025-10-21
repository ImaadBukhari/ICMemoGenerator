"""
Mock authentication for local testing
"""
from backend.db.models import User

# Mock user for local testing
MOCK_USER = User(
    id=1,
    email="test@example.com"
)

def get_current_user():
    """Mock authentication function for local testing"""
    return MOCK_USER
