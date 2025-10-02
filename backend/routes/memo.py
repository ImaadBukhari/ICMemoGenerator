from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os

from database import get_db
from db.models import User, MemoRequest, MemoSection
from routes.auth import get_current_user
from services.memo_generation_service import (
    generate_comprehensive_memo, 
    compile_final_memo
)
from services.data_gathering_service import get_stored_company_data
from services.document_service import (
    generate_word_document,
    get_document_summary
)

router = APIRouter()

class MemoGenerationRequest(BaseModel):
    source_id: int

class SectionResult(BaseModel):
    section_name: str
    status: str
    content_length: Optional[int] = None
    data_sources_used: Optional[List[str]] = None
    section_id: Optional[int] = None
    error: Optional[str] = None
    stats_included: Optional[bool] = False

class MemoResponse(BaseModel):
    memo_request_id: int
    status: str
    generation_summary: Optional[Dict[str, Any]] = None
    sections_completed: Optional[List[SectionResult]] = None
    sections_failed: Optional[List[SectionResult]] = None
    final_memo: Optional[str] = None
    error: Optional[str] = None

@router.post("/generate", response_model=MemoResponse)
async def generate_memo(
    request: MemoGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate an IC memo from stored company data using section-by-section approach."""
    try:
        company_data = get_stored_company_data(db, request.source_id)
        
        if "error" in company_data:
            raise HTTPException(status_code=404, detail=company_data["error"])
        
        memo_request = MemoRequest(
            user_id=current_user.id,
            company_name=company_data["company_name"],
            sources_id=request.source_id,
            status="pending"
        )
        db.add(memo_request)
        db.commit()
        db.refresh(memo_request)
        
        try:
            generation_result = generate_comprehensive_memo(
                company_data, 
                db, 
                memo_request.id
            )
            
            final_memo = compile_final_memo(db, memo_request.id)
            
            memo_request.status = generation_result["status"]
            db.commit()
            
            return MemoResponse(
                memo_request_id=memo_request.id,
                status=generation_result["status"],
                generation_summary=generation_result["generation_summary"],
                sections_completed=[SectionResult(**section) for section in generation_result["sections_completed"]],
                sections_failed=[SectionResult(**section) for section in generation_result["sections_failed"]],
                final_memo=final_memo if generation_result["status"] in ["completed", "partial_success"] else None
            )
        except Exception as e:
            memo_request.status = "failed"
            memo_request.error_log = str(e)
            db.commit()
            
            return MemoResponse(
                memo_request_id=memo_request.id,
                status="failed",
                error=str(e)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")

@router.get("/{memo_id}/sections")
async def get_memo_sections(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sections for a memo with their status."""
    memo_request = db.query(MemoRequest).filter(
        MemoRequest.id == memo_id,
        MemoRequest.user_id == current_user.id
    ).first()
    
    if not memo_request:
        raise HTTPException(status_code=404, detail="Memo request not found")
    
    sections = db.query(MemoSection).filter(
        MemoSection.memo_request_id == memo_id
    ).all()
    
    return {
        "sections": [
            {
                "section_name": section.section_name,
                "status": section.status,
                "content_length": len(section.content) if section.content else 0,
                "error": section.error_log
            }
            for section in sections
        ]
    }

@router.get("/{memo_id}")
async def get_memo_status(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the status of a memo generation request."""
    memo_request = db.query(MemoRequest).filter(
        MemoRequest.id == memo_id,
        MemoRequest.user_id == current_user.id
    ).first()
    
    if not memo_request:
        raise HTTPException(status_code=404, detail="Memo request not found")
    
    return {
        "id": memo_request.id,
        "company_name": memo_request.company_name,
        "status": memo_request.status,
        "drive_link": memo_request.drive_link,
        "error_log": memo_request.error_log,
        "created_at": memo_request.created_at
    }

class DocumentGenerationResponse(BaseModel):
    memo_request_id: int
    status: str
    document_path: Optional[str] = None
    filename: Optional[str] = None
    document_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/{memo_id}/generate-document", response_model=DocumentGenerationResponse)
async def generate_document(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate Word document from memo sections."""
    try:
        result = generate_word_document(db, memo_id)
        return DocumentGenerationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

@router.get("/{memo_id}/download")
async def download_document(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the generated Word document."""
    memo_request = db.query(MemoRequest).filter(
        MemoRequest.id == memo_id,
        MemoRequest.user_id == current_user.id
    ).first()
    
    if not memo_request:
        raise HTTPException(status_code=404, detail="Memo request not found")
    
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_docs")
    
    for filename in os.listdir(docs_dir):
        if filename.startswith(f"IC_Memo_{memo_request.company_name}"):
            file_path = os.path.join(docs_dir, filename)
            return FileResponse(
                file_path,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename=filename
            )
    
    raise HTTPException(status_code=404, detail="Document not found")