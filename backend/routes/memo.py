from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os

from backend.db.models import User, MemoRequest, MemoSection
from backend.database import get_db, SessionLocal
from backend.auth import get_current_user
from backend.services.data_gathering_service import get_stored_company_data
from backend.services.memo_generation_service import generate_comprehensive_memo, generate_short_memo, compile_final_memo, compile_short_memo
from backend.services.document_service import generate_word_document, generate_short_word_document, get_document_summary, generate_google_doc

#This file handles memo generation and document creation

router = APIRouter()

class MemoGenerationRequest(BaseModel):
    source_id: int
    memo_type: str = "full"  # "full" or "short"

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

def generate_memo_background(company_data: Dict, memo_request_id: int, memo_type: str = "full"):
    """Background task to generate memo sections"""
    print(f"Starting background generation for memo {memo_request_id}, type: {memo_type}")
    db = SessionLocal()
    try:
        if memo_type == "short":
            from backend.services.memo_generation_service import generate_short_memo
            generation_result = generate_short_memo(
                company_data, 
                db, 
                memo_request_id
            )
        else:
            generation_result = generate_comprehensive_memo(
                company_data, 
                db, 
                memo_request_id
            )
        
        print(f"Generation result: {generation_result}")
        
        # Update memo request status
        memo_request = db.query(MemoRequest).filter(MemoRequest.id == memo_request_id).first()
        if memo_request:
            memo_request.status = generation_result["status"]
            db.commit()
            
        print(f"Memo generation completed with status: {generation_result['status']}")
    except Exception as e:
        print(f"Background generation error: {str(e)}")
        import traceback
        traceback.print_exc()
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
        print(f"Creating memo request with type: {request.memo_type}")
        memo_request = MemoRequest(
            user_id=current_user.id,
            company_name=company_data["company_name"],
            sources_id=request.source_id,
            memo_type=request.memo_type,
            status="in_progress"
        )
        db.add(memo_request)
        db.commit()
        db.refresh(memo_request)
        print(f"Created memo request {memo_request.id} with type: {memo_request.memo_type}")
        
        # Start generation in background - DON'T PASS db SESSION
        background_tasks.add_task(
            generate_memo_background,
            company_data,
            memo_request.id,  # Only pass the ID, not the session
            request.memo_type  # Pass memo type
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
            "memo_type": memo.memo_type,
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
    doc_url: Optional[str] = None  # Google Doc URL

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
        
        # Generate Google Doc
        print(f"Generating Google Doc for memo {memo_id}, type: {memo_request.memo_type}")
        
        # Get all sections
        sections = db.query(MemoSection).filter(
            MemoSection.memo_request_id == memo_id,
            MemoSection.status == "completed"
        ).all()
        
        if not sections:
            return DocumentGenerationResponse(
                memo_request_id=memo_id,
                status="failed",
                error="No completed sections found"
            )
        
        # Build sections dict
        sections_dict = {section.section_name: section for section in sections}
        
        # Generate Google Doc
        doc_url = generate_google_doc(
            user=current_user,
            db=db,
            sections_dict=sections_dict,
            company_name=memo_request.company_name
        )
        
        # Get document summary
        doc_summary = get_document_summary(db, memo_id)
        
        return DocumentGenerationResponse(
            memo_request_id=memo_id,
            status="success",
            document_path=doc_url,  # Store URL in document_path field for backward compatibility
            filename=None,  # No filename for Google Docs
            document_summary=doc_summary,
            doc_url=doc_url  # Add new field
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
    Get the Google Doc URL for a memo (redirects to Google Docs).
    Note: Documents are now created as Google Docs in the Investments folder.
    """
    try:
        # Verify memo belongs to user
        memo_request = db.query(MemoRequest).filter(
            MemoRequest.id == memo_id,
            MemoRequest.user_id == current_user.id
        ).first()
        
        if not memo_request:
            raise HTTPException(status_code=404, detail="Memo request not found")
        
        # Get all sections
        sections = db.query(MemoSection).filter(
            MemoSection.memo_request_id == memo_id,
            MemoSection.status == "completed"
        ).all()
        
        if not sections:
            raise HTTPException(status_code=404, detail="No completed sections found")
        
        # Build sections dict
        sections_dict = {section.section_name: section for section in sections}
        
        # Generate Google Doc
        doc_url = generate_google_doc(
            user=current_user,
            db=db,
            sections_dict=sections_dict,
            company_name=memo_request.company_name
        )
        
        return {"doc_url": doc_url, "message": "Document created in Google Drive Investments folder"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

class TestFormatRequest(BaseModel):
    source_id: Optional[int] = None
    sections: Optional[Dict[str, str]] = None
    company_name: str

@router.post("/doc/test-format")
async def test_document_format(
    request: TestFormatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test document formatting without full memo generation.
    Allows rapid iteration on formatting changes.
    """
    try:
        sections_dict = {}
        
        if request.source_id:
            # Find memo request with this source_id
            memo_request = db.query(MemoRequest).filter(
                MemoRequest.sources_id == request.source_id
            ).order_by(MemoRequest.created_at.desc()).first()
            
            if memo_request:
                # Get sections from memo request
                sections = db.query(MemoSection).filter(
                    MemoSection.memo_request_id == memo_request.id,
                    MemoSection.status == "completed"
                ).all()
                sections_dict = {section.section_name: section for section in sections}
            else:
                raise HTTPException(status_code=404, detail=f"No memo found for source_id {request.source_id}")
        elif request.sections:
            # Use provided sections
            class MockSection:
                def __init__(self, name, content):
                    self.section_name = name
                    self.content = content
                    self.data_sources = []
            sections_dict = {k: MockSection(k, v) for k, v in request.sections.items()}
        else:
            raise HTTPException(status_code=400, detail="Either source_id or sections must be provided")
        
        # Generate Google Doc
        doc_url = generate_google_doc(
            user=current_user,
            db=db,
            sections_dict=sections_dict,
            company_name=request.company_name
        )
        
        return {
            "status": "success",
            "doc_url": doc_url,
            "message": "Test document created in Google Drive Investments folder"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test document: {str(e)}")

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