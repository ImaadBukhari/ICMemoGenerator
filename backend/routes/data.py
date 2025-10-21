from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.db.models import User
from backend.database import get_db
from backend.mock_auth import get_current_user
from backend.services.data_gathering_service import (
    gather_and_store_company_data,
    get_stored_company_data,
    list_user_sources
)

# This file handles data gathering from Affinity and Google Drive, and storing it in the database
router = APIRouter()

class DataGatheringRequest(BaseModel):
    company_id: str
    company_name: str
    description: Optional[str] = None

class DataGatheringResponse(BaseModel):
    company_name: str
    company_id: str
    affinity_success: bool
    drive_success: bool
    perplexity_success: bool
    storage_success: bool
    errors: List[str]
    source_id: Optional[int] = None


# ✅ Add this preflight handler
@router.options("/data/gather")
async def options_gather_company_data():
    """
    Preflight CORS handler for /data/gather.
    Returns the necessary headers for browsers to allow POST from the frontend.
    """
    return {}


@router.post("/data/gather", response_model=DataGatheringResponse)
async def gather_company_data(
    request: DataGatheringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Gather company data from Affinity and Google Drive and store in database.
    """
    try:
        result = gather_and_store_company_data(
            user=current_user,
            db=db,
            company_id=request.company_id,
            company_name=request.company_name,
            description=request.description
        )
        return DataGatheringResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to gather company data: {str(e)}")


@router.get("/data/source/{source_id}")
async def get_source_data(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get stored company data by source ID.
    """
    try:
        data = get_stored_company_data(db, source_id)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve source data: {str(e)}")


@router.get("/data/sources")
async def list_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all data sources for the current user.
    """
    try:
        sources = list_user_sources(db, current_user.id)
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")
