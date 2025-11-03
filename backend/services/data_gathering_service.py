from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.db.models import User, Source
from backend.services.affinity_service import get_company_details, find_company_by_url
from backend.services.google_service import search_files, get_docs_service
from backend.services.perplexity_service import search_company_comprehensive, get_company_website

import os

def extract_text_from_doc(doc_content: Dict) -> str:
    """Extract plain text from Google Docs API response."""
    text = ""
    if "body" in doc_content and "content" in doc_content["body"]:
        for element in doc_content["body"]["content"]:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                if "elements" in paragraph:
                    for elem in paragraph["elements"]:
                        if "textRun" in elem:
                            text += elem["textRun"].get("content", "")
    return text

def gather_affinity_data(company_id: str) -> Dict[str, Any]:
    """
    Gather company data from Affinity CRM.
    """
    try:
        affinity_data = get_company_details(company_id)
        return {
            "success": True,
            "data": affinity_data,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }

def gather_drive_data(user: User, db: Session, company_name: str) -> Dict[str, Any]:
    """
    Search Google Drive for files related to the company and extract content.
    """
    try:
        # Search for files containing the company name
        drive_files = search_files(user, db, company_name, max_results=10)
        
        if not drive_files:
            return {
                "success": True,
                "files": [],
                "processed_files": [],
                "error": None
            }
        
        # Get Google Docs service to read document content
        docs_service = get_docs_service(user, db)
        processed_files = []
        
        for file in drive_files:
            file_data = {
                "id": file.get("id"),
                "name": file.get("name"),
                "mimeType": file.get("mimeType"),
                "webViewLink": file.get("webViewLink"),
                "createdTime": file.get("createdTime"),
                "modifiedTime": file.get("modifiedTime"),
                "content": None,
                "content_error": None
            }
            
            # Try to extract content from Google Docs
            if file.get("mimeType") == "application/vnd.google-apps.document":
                try:
                    doc_content = docs_service.documents().get(
                        documentId=file["id"]
                    ).execute()
                    file_data["content"] = extract_text_from_doc(doc_content)
                except Exception as e:
                    file_data["content_error"] = str(e)
            
            processed_files.append(file_data)
        
        return {
            "success": True,
            "files": drive_files,
            "processed_files": processed_files,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "files": [],
            "processed_files": [],
            "error": str(e)
        }

def gather_perplexity_data(company_name: str, description: str = None) -> Dict[str, Any]:
    """
    Gather comprehensive company research data including stats from Perplexity.
    """
    try:
        # Use enhanced comprehensive search with stats AND description
        from backend.services.perplexity_service import search_company_comprehensive_with_stats
        
        perplexity_data = search_company_comprehensive_with_stats(company_name, description)  
        return {
            "success": True,
            "data": perplexity_data,
            "error": None
        }
    except Exception as e:
        print(f"Perplexity error: {str(e)}")
        return {
            "success": False,
            "data": {
                "company_name": company_name,
                "categories": {},
                "stats_categories": {},
                "overall_success": False,
                "stats_success": False,
                "errors": [f"Perplexity API unavailable: {str(e)}"]
            },
            "error": str(e)
        }

def gather_and_store_company_data(
    user: User,
    db: Session,
    company_name: str,
    description: str = None,
    company_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gather company data from multiple sources and store in database.
    Auto-discovers Affinity company by URL if company_id not provided.
    """
    errors = []
    
    results = {
        "company_name": company_name,
        "company_id": None,
        "affinity_success": False,
        "drive_success": False,
        "perplexity_success": False,
        "errors": [],
        "source_id": None
    }
    
    # 1. Auto-discover Affinity company if ID not provided
    discovered_company_id = company_id
    
    if not discovered_company_id:
        print(f"Auto-discovering Affinity company for: {company_name}")
        
        # Step 1: Get company website from Perplexity
        print("  Getting company website from Perplexity...")
        company_url = get_company_website(company_name)
        
        if not company_url:
            results["errors"].append("Could not find company website via Perplexity")
            print("  ❌ Could not find company website")
        else:
            print(f"  ✅ Found website: {company_url}")
            
            # Step 2: Find company in Affinity list 315335 by URL
            print("  Searching Affinity list 315335 for matching company...")
            AFFINITY_LIST_ID = 315335
            affinity_company = find_company_by_url(AFFINITY_LIST_ID, company_url)
            
            if not affinity_company:
                results["errors"].append(f"Could not find company in Affinity list {AFFINITY_LIST_ID} with URL: {company_url}")
                print(f"  ❌ Could not find company in Affinity list")
            else:
                discovered_company_id = str(affinity_company.get("id"))
                print(f"  ✅ Found company in Affinity with ID: {discovered_company_id}")
    
    # 2. Gather Affinity data (if we have a company ID)
    if discovered_company_id:
        results["company_id"] = discovered_company_id
        print(f"Gathering Affinity data for company ID: {discovered_company_id}")
        affinity_result = gather_affinity_data(discovered_company_id)
        results["affinity_success"] = affinity_result["success"]
        if not affinity_result["success"]:
            results["errors"].append(f"Affinity error: {affinity_result['error']}")
    else:
        print("⚠️ No Affinity company ID available, skipping Affinity data gathering")
        results["errors"].append("No Affinity company ID found - could not auto-discover")
    
    # 3. Gather Google Drive data
    print(f"Gathering Google Drive data for company: {company_name}")
    drive_result = gather_drive_data(user, db, company_name)
    results["drive_success"] = drive_result["success"]
    if not drive_result["success"]:
        results["errors"].append(f"Google Drive error: {drive_result['error']}")
    
    # 4. Gather comprehensive Perplexity data with description
    print(f"Gathering comprehensive Perplexity data for company: {company_name}")
    if description:
        print(f"  Using description: {description}")
    perplexity_result = gather_perplexity_data(company_name, description)  # Pass description
    results["perplexity_success"] = perplexity_result["success"]
    if not perplexity_result["success"]:
        results["errors"].append(f"Perplexity error: {perplexity_result['error']}")


    # 5. Store all data in the database
    try:
        source = Source(
            user_id=user.id,
            company_name=company_name,
            company_description=description,  # Store description in DB
            affinity_data=affinity_result["data"] if affinity_result["success"] else None,
            perplexity_data=perplexity_result["data"] if perplexity_result["success"] else None,
            drive_data={
                "files": drive_result["processed_files"] if drive_result["success"] else [],
                "search_success": drive_result["success"],
                "error": drive_result["error"]
            }
        )
        
        db.add(source)
        db.commit()
        db.refresh(source)
        
        results["source_id"] = source.id
        results["storage_success"] = True
        
        print(f"Successfully stored data for {company_name} with source ID: {source.id}")
        
    except Exception as e:
        db.rollback()
        results["storage_success"] = False
        results["errors"].append(f"Database storage error: {str(e)}")
        print(f"Failed to store data: {str(e)}")
    
    return results

def get_stored_company_data(db: Session, source_id: int) -> Dict[str, Any]:
    """
    Retrieve stored company data by source ID.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        return {"error": "Source not found"}
    
    return {
        "id": source.id,
        "company_name": source.company_name,
        "affinity_data": source.affinity_data,
        "perplexity_data": source.perplexity_data,
        "drive_data": source.drive_data,
        "created_at": source.created_at
    }

def list_user_sources(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    List all data sources for a user.
    """
    sources = db.query(Source).filter(Source.user_id == user_id).order_by(Source.created_at.desc()).all()
    
    return [
        {
            "id": source.id,
            "company_name": source.company_name,
            "has_affinity_data": source.affinity_data is not None,
            "has_perplexity_data": source.perplexity_data is not None,
            "has_drive_data": bool(source.drive_data and source.drive_data.get("files")),
            "created_at": source.created_at
        }
        for source in sources
    ]


def get_stored_company_data(db: Session, source_id: int) -> Dict[str, Any]:
    """Retrieve stored company data for memo generation"""
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        return {"error": "Source not found"}
    
    return {
        "source_id": source_id,  
        "company_name": source.company_name,
        "affinity_data": source.affinity_data,
        "perplexity_data": source.perplexity_data,
        "gmail_data": source.gmail_data,
        "drive_data": source.drive_data
    }


