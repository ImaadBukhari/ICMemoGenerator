from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os

from backend.db.models import User, MemoRequest, MemoSection
from backend.database import get_db, SessionLocal  # ADD SessionLocal import
from backend.auth import get_current_user
from backend.services.data_gathering_service import get_stored_company_data
from backend.services.memo_generation_service import generate_comprehensive_memo, compile_final_memo
from backend.services.document_service import generate_word_document, get_document_summary

#This file handles memo generation and document creation

from fastapi import APIRouter, Depends
from backend.auth.firebase_auth import verify_firebase_token

router = APIRouter()

@router.post("/data/gather")
async def gather_data(
    payload: dict,
    user=Depends(verify_firebase_token)
):
    # You can now access user info
    user_uid = user.get("uid")
    print(f"Authenticated request from UID: {user_uid}")

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
    message: Optional[str] = None

def generate_memo_background(company_data: Dict, memo_request_id: int):
    """Background task to generate memo sections"""
    # CREATE A NEW DATABASE SESSION FOR THIS BACKGROUND TASK
    db = SessionLocal()
    try:
        generation_result = generate_comprehensive_memo(
            company_data, 
            db, 
            memo_request_id
        )
        
        # Update memo request status
        memo_request = db.query(MemoRequest).filter(MemoRequest.id == memo_request_id).first()
        if memo_request:
            memo_request.status = generation_result["status"]
            db.commit()
    except Exception as e:
        print(f"Background generation error: {str(e)}")
        memo_request = db.query(MemoRequest).filter(MemoRequest.id == memo_request_id).first()
        if memo_request:
            memo_request.status = "failed"
            memo_request.error_log = str(e)
            db.commit()
    finally:
        db.close()  # ALWAYS CLOSE THE SESSION

@router.post("/memo/generate")
async def generate_memo(
    request: MemoGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start memo generation in background and return immediately"""
    try:
        company_data = get_stored_company_data(db, request.source_id)
        
        if "error" in company_data:
            raise HTTPException(status_code=404, detail=company_data["error"])
        
        # Create memo request
        memo_request = MemoRequest(
            user_id=current_user.id,
            company_name=company_data["company_name"],
            sources_id=request.source_id,
            status="in_progress"
        )
        db.add(memo_request)
        db.commit()
        db.refresh(memo_request)
        
        # Start generation in background - DON'T PASS db SESSION
        background_tasks.add_task(
            generate_memo_background,
            company_data,
            memo_request.id  # Only pass the ID, not the session
        )
        
        # Return immediately with memo_request_id
        return {
            "memo_request_id": memo_request.id,
            "status": "in_progress",
            "message": "Memo generation started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start memo generation: {str(e)}")

# ... keep all other routes exactly the same ...
# ... rest of the routes stay the same ...

@router.get("/memo/{memo_id}/sections")
async def get_memo_sections(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all sections for a memo with their status.
    """
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
        "memo_id": memo_id,
        "company_name": memo_request.company_name,
        "overall_status": memo_request.status,
        "sections": [
            {
                "id": section.id,
                "section_name": section.section_name,
                "status": section.status,
                "content_length": len(section.content) if section.content else 0,
                "data_sources": section.data_sources,
                "error_log": section.error_log,
                "created_at": section.created_at
            }
            for section in sections
        ]
    }

@router.get("/memo/{memo_id}/compile")
async def get_compiled_memo(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the compiled final memo document.
    """
    memo_request = db.query(MemoRequest).filter(
        MemoRequest.id == memo_id,
        MemoRequest.user_id == current_user.id
    ).first()
    
    if not memo_request:
        raise HTTPException(status_code=404, detail="Memo request not found")
    
    final_memo = compile_final_memo(db, memo_id)
    
    return {
        "memo_id": memo_id,
        "company_name": memo_request.company_name,
        "status": memo_request.status,
        "final_memo": final_memo
    }


@router.get("/memo/{memo_id}")
async def get_memo_status(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a memo generation request.
    """
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

@router.get("/memo/list")
async def list_user_memos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all memo requests for the current user.
    """
    memos = db.query(MemoRequest).filter(
        MemoRequest.user_id == current_user.id
    ).order_by(MemoRequest.created_at.desc()).all()
    
    return [
        {
            "id": memo.id,
            "company_name": memo.company_name,
            "status": memo.status,
            "drive_link": memo.drive_link,
            "created_at": memo.created_at
        }
        for memo in memos
    ]

class DocumentGenerationResponse(BaseModel):
    memo_request_id: int
    status: str
    document_path: Optional[str] = None
    filename: Optional[str] = None
    document_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/memo/{memo_id}/generate-document", response_model=DocumentGenerationResponse)
async def generate_memo_document(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a Word document from completed memo sections.
    """
    try:
        # Verify memo belongs to user
        memo_request = db.query(MemoRequest).filter(
            MemoRequest.id == memo_id,
            MemoRequest.user_id == current_user.id
        ).first()
        
        if not memo_request:
            raise HTTPException(status_code=404, detail="Memo request not found")
        
        # Generate Word document
        document_path = generate_word_document(db, memo_id)
        
        if document_path:
            # Get document summary
            doc_summary = get_document_summary(db, memo_id)
            filename = os.path.basename(document_path)
            
            return DocumentGenerationResponse(
                memo_request_id=memo_id,
                status="success",
                document_path=document_path,
                filename=filename,
                document_summary=doc_summary
            )
        else:
            return DocumentGenerationResponse(
                memo_request_id=memo_id,
                status="failed",
                error="Failed to generate Word document"
            )
            
    except Exception as e:
        return DocumentGenerationResponse(
            memo_request_id=memo_id,
            status="failed",
            error=str(e)
        )

@router.get("/memo/{memo_id}/download")
async def download_memo_document(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the generated Word document for a memo.
    """
    try:
        # Verify memo belongs to user
        memo_request = db.query(MemoRequest).filter(
            MemoRequest.id == memo_id,
            MemoRequest.user_id == current_user.id
        ).first()
        
        if not memo_request:
            raise HTTPException(status_code=404, detail="Memo request not found")
        
        # Generate document if it doesn't exist
        document_path = generate_word_document(db, memo_id)
        
        if not document_path or not os.path.exists(document_path):
            raise HTTPException(status_code=404, detail="Document not found or generation failed")
        
        filename = os.path.basename(document_path)
        
        return FileResponse(
            path=document_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")

@router.get("/memo/{memo_id}/document-summary")
async def get_memo_document_summary(
    memo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary of document generation status and section completion.
    """
    memo_request = db.query(MemoRequest).filter(
        MemoRequest.id == memo_id,
        MemoRequest.user_id == current_user.id
    ).first()
    
    if not memo_request:
        raise HTTPException(status_code=404, detail="Memo request not found")
    
    return get_document_summary(db, memo_id)