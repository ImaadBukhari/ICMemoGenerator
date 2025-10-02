from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database import get_db
from db.models import User
from routes.auth import get_current_user
from services.affinity_service import AffinityService

router = APIRouter()

@router.get("/companies")
async def search_companies(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for companies in Affinity"""
    try:
        affinity = AffinityService()
        companies = affinity.search_companies(query)
        return {"companies": companies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search companies: {str(e)}")

@router.get("/company/{company_id}")
async def get_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed company information from Affinity"""
    try:
        affinity = AffinityService()
        company_data = affinity.get_company_data(company_id)
        return company_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Company not found: {str(e)}")