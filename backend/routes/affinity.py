from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.auth import get_current_user
from backend.db.models import User
from backend.services.affinity_service import get_companies, get_company_details

router = APIRouter()

@router.get("/affinity/companies")
async def list_affinity_companies(
    page_url: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get list of companies from Affinity CRM."""
    try:
        companies = get_companies(page_url)
        return companies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}")

@router.get("/affinity/companies/{company_id}")
async def get_affinity_company(
    company_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information for a specific company from Affinity."""
    try:
        company_details = get_company_details(company_id)
        return company_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch company details: {str(e)}")