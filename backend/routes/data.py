from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from db.models import User, Source
from routes.auth import get_current_user
from services.data_gathering_service import gather_and_store_company_data

router = APIRouter()

class DataGatheringRequest(BaseModel):
    company_id: str
    company_name: str

class DataGatheringResponse(BaseModel):
    company_name: str
    company_id: str
    affinity_success: bool
    drive_success: bool
    perplexity_success: bool
    storage_success: bool
    errors: List[str]
    source_id: Optional[int] = None

@router.post("/gather", response_model=DataGatheringResponse)
async def gather_company_data(
    request: DataGatheringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Gather company data from Affinity and Google Drive and store in database."""
    try:
        result = gather_and_store_company_data(
            user=current_user,
            db=db,
            company_id=request.company_id,
            company_name=request.company_name
        )
        return DataGatheringResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to gather company data: {str(e)}")

@router.get("/source/{source_id}")
async def get_source_data(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get stored company data by source ID."""
    source = db.query(Source).filter(
        Source.id == source_id,
        Source.user_id == current_user.id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return {
        "id": source.id,
        "company_name": source.company_name,
        "affinity_data": source.affinity_data,
        "perplexity_data": source.perplexity_data,
        "drive_data": source.drive_data,
        "created_at": source.created_at
    }

@router.get("/sources")
async def list_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all stored company data sources for current user."""
    sources = db.query(Source).filter(
        Source.user_id == current_user.id
    ).order_by(Source.created_at.desc()).all()
    
    return [
        {
            "id": source.id,
            "company_name": source.company_name,
            "created_at": source.created_at
        }
        for source in sources
    ]