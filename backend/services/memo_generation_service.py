import json
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.db.models import MemoRequest, MemoSection, Source  # ADD Source
from backend.services.gpt_service import generate_text
from backend.services.rag_service import build_company_knowledge_base, retrieve_context_for_section
import re

# Load memo prompts
def load_memo_prompts() -> Dict[str, Any]:
    """Load memo prompts from JSON file"""
    prompts_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', 'memo_prompts.json')
    with open(prompts_path, 'r') as f:
        return json.load(f)

def get_stored_company_data(db: Session, source_id: int) -> Dict[str, Any]:
    """Retrieve stored company data for memo generation"""
    source = db.query(Source).filter(Source.id == source_id).first()
    
    if not source:
        return {"error": "Source not found"}
    
    return {
        "source_id": source_id,
        "company_name": source.company_name,
        "company_description": source.company_description,  # ADD THIS LINE
        "affinity_data": source.affinity_data,
        "perplexity_data": source.perplexity_data,
        "gmail_data": source.gmail_data,
        "drive_data": source.drive_data
    }

def format_affinity_data(affinity_data: Dict[str, Any]) -> str:
    """Format Affinity CRM data for prompts"""
    if not affinity_data:
        return "No CRM data available."
    
    formatted_sections = []
    key_fields = [
        'name', 'stage', 'industry', 'description', 'website',
        'funding_stage', 'last_funding_amount', 'total_funding',
        'valuation', 'employees', 'headquarters', 'founded_date'
    ]
    
    for field in key_fields:
        if field in affinity_data and affinity_data[field]:
            formatted_sections.append(f"{field.replace('_', ' ').title()}: {affinity_data[field]}")
    
    return "\n".join(formatted_sections) if formatted_sections else "Limited CRM data available."

def generate_memo_section_with_rag(
    section_key: str,
    prompt: str,
    company_data: Dict[str, Any],
    faiss_index,
    chunks: List[Dict[str, Any]],
    db: Session,
    memo_request_id: int
) -> Dict[str, Any]:
    """Generate a single memo section using RAG and GPT"""
    
    try:
        print(f"Generating section: {section_key}")
        
        # Retrieve relevant context using RAG
        rag_context = retrieve_context_for_section(
            section_key,
            prompt,
            faiss_index,
            chunks,
            company_data.get("company_name", ""),
            top_k=8
        )
        
        # Format Affinity data
        affinity_section = format_affinity_data(company_data.get("affinity_data", {}))
        
        company_name = company_data.get("company_name", "the company")
        company_description = company_data.get("company_description", "")
        
        # Create enhanced prompt with RAG context
        enhanced_prompt = f"""

COMPANY: {company_name}
{f"DESCRIPTION: {company_description}" if company_description else ""}

{prompt}

You are generating a section of a wider memo, so while you should tie everything together at the end, don't have an explicit conclusion section.

=== CRM DATA (Source: Crunchbase) ===
{affinity_section}

=== RELEVANT RESEARCH & DATA (Retrieved via semantic search) ===
{rag_context['context']}

IMPORTANT INSTRUCTIONS:
1. Base your response ONLY on the data provided above
2. When citing information, reference the citation numbers [1], [2], etc.
3. All CRM data should be cited as "Source: Crunchbase"
4. Prioritize quantitative data, specific metrics, and statistics
5. If specific information is not available, clearly state that rather than making assumptions
6. Include specific numbers, percentages, growth rates, and financial figures when mentioned

SOURCES USED: {len(rag_context['sources'])} unique sources found
"""
        
        # Generate content using GPT
        system_message = """
You are a venture capital investment analyst at Wyld VC, drafting a data-driven Investment Committee (IC) memo.
Write in a neutral, factual tone but emphasize analytical insight.
Always back claims with specific data and citations [1], [2], etc.
Avoid marketing language or speculation; use quantitative metrics and relative comparisons (e.g., "30% higher than peers").
Each section must be self-contained, concise (300–500 words), and logically structured for a reader who will skim.
End each section with a short insight summary (2–3 sentences) highlighting key implications or open questions.
"""
        
        content = generate_text(
            enhanced_prompt,
            system_message,
            model="gpt-4-turbo-preview",
            max_tokens=2000,
            temperature=0.2
        )
        
        # Add Crunchbase to sources if Affinity data was used
        sources = rag_context['sources'].copy()
        if company_data.get("affinity_data"):
            sources.append("Crunchbase (via Affinity CRM)")
        
        # Store the section with source information
        memo_section = MemoSection(
            memo_request_id=memo_request_id,
            section_name=section_key,
            content=content,
            data_sources=sources,  # Include Crunchbase
            status="completed"
        )
        
        db.add(memo_section)
        db.commit()
        db.refresh(memo_section)
        
        print(f"✅ Section '{section_key}' generated successfully with {len(sources)} sources")
        
        return {
            "status": "success",
            "section_name": section_key,
            "section_id": memo_section.id,
            "content": content,
            "data_sources_used": sources,
        }
        
    except Exception as e:
        print(f"❌ Error generating section '{section_key}': {str(e)}")
        
        memo_section = MemoSection(
            memo_request_id=memo_request_id,
            section_name=section_key,
            content="",
            status="failed",
            error_log=str(e)
        )
        db.add(memo_section)
        db.commit()
        
        return {
            "status": "failed",  # FIXED
            "section_name": section_key,
            "error": str(e)  # FIXED
        }

def generate_comprehensive_memo(
    company_data: Dict[str, Any],
    db: Session,
    memo_request_id: int
) -> Dict[str, Any]:
    """Generate all memo sections systematically using RAG, maintaining global citations"""
    
    print(f"Starting comprehensive memo generation for memo request {memo_request_id}")
    
    # === GLOBAL CITATION MAP ===
    global_citation_map = {}
    next_citation_num = 1
    
    # === BUILD KNOWLEDGE BASE ===
    print("Building knowledge base with embeddings...")
    faiss_index, chunks = build_company_knowledge_base(db, company_data.get("source_id"))
    
    if not faiss_index:
        return {
            "status": "failed",
            "error": "Failed to build knowledge base from company data",
            "sections_completed": [],
            "sections_failed": []
        }
    
    print(f"✅ Knowledge base built with {len(chunks)} chunks")
    
    # === LOAD PROMPTS ===
    try:
        prompts = load_memo_prompts()
    except Exception as e:
        return {
            "status": "failed",
            "error": f"Failed to load memo prompts: {str(e)}",
            "sections_completed": [],
            "sections_failed": []
        }
    
    results = {
        "status": "in_progress",
        "total_sections": 0,
        "sections_completed": [],
        "sections_failed": [],
        "generation_summary": {}
    }
    
    # === SECTION LISTS ===
    main_sections = [
        "executive_summary",
        "company_snapshot", 
        "people",
        "market_opportunity",
        "competitive_landscape",
        "product",
        "financial",
        "traction_validation",
        "deal_considerations"
    ]
    
    assessment_sections = [
        ("assessment_people", "people"),
        ("assessment_market_opportunity", "market_opportunity"),
        ("assessment_product", "product"),
        ("assessment_financials", "financials"),
        ("assessment_traction_validation", "traction_validation"),
        ("assessment_deal_considerations", "deal_considerations")
    ]
    
    # === PROCESS MAIN SECTIONS ===
    for section in main_sections:
        if section in prompts:
            result = generate_memo_section_with_rag(
                section,
                prompts[section],
                company_data,
                faiss_index,
                chunks,
                db,
                memo_request_id
            )
            
            if result["status"] == "success":
                # ---- GLOBAL CITATION REMAPPING ----
                section_text = result["content"]
                section_sources = result.get("data_sources_used", [])
                
                for local_idx, source in enumerate(section_sources, 1):
                    if source not in global_citation_map:
                        global_citation_map[source] = next_citation_num
                        next_citation_num += 1
                    
                    # Replace [1], [2], etc. with global index
                    section_text = re.sub(
                        rf'\[{local_idx}\]',
                        f'[{global_citation_map[source]}]',
                        section_text
                    )
                
                # Update stored section content in DB
                section_obj = db.query(MemoSection).filter(MemoSection.id == result["section_id"]).first()
                if section_obj:
                    section_obj.content = section_text
                    db.commit()
                
                results["sections_completed"].append(result)
            else:
                results["sections_failed"].append(result)
        else:
            print(f"⚠️ Prompt not found for section: {section}")
    
    # === PROCESS ASSESSMENT SECTIONS ===
    for assessment_key, prompt_key in assessment_sections:
        if "assessment_summary" in prompts and prompt_key in prompts["assessment_summary"]:
            result = generate_memo_section_with_rag(
                assessment_key,
                prompts["assessment_summary"][prompt_key],
                company_data,
                faiss_index,
                chunks,
                db,
                memo_request_id
            )
            
            if result["status"] == "success":
                section_text = result["content"]
                section_sources = result.get("data_sources_used", [])
                
                for local_idx, source in enumerate(section_sources, 1):
                    if source not in global_citation_map:
                        global_citation_map[source] = next_citation_num
                        next_citation_num += 1
                    
                    section_text = re.sub(
                        rf'\[{local_idx}\]',
                        f'[{global_citation_map[source]}]',
                        section_text
                    )
                
                section_obj = db.query(MemoSection).filter(MemoSection.id == result["section_id"]).first()
                if section_obj:
                    section_obj.content = section_text
                    db.commit()
                
                results["sections_completed"].append(result)
            else:
                results["sections_failed"].append(result)
        else:
            print(f"⚠️ Assessment prompt not found for: {assessment_key}")
    
    # === FINALIZE ===
    results["total_sections"] = len(results["sections_completed"]) + len(results["sections_failed"])
    results["success_rate"] = (
        len(results["sections_completed"]) / results["total_sections"]
        if results["total_sections"] > 0 else 0
    )
    
    if len(results["sections_failed"]) == 0:
        results["status"] = "completed"
    elif len(results["sections_completed"]) > 0:
        results["status"] = "partial_success"
    else:
        results["status"] = "failed"
    
    results["generation_summary"] = {
        "total_sections": results["total_sections"],
        "successful": len(results["sections_completed"]),
        "failed": len(results["sections_failed"]),
        "success_rate": f"{results['success_rate']*100:.1f}%"
    }
    
    print(f"Memo generation completed: {results['success_rate']*100:.1f}% success rate")
    print(f"📚 Global citation count: {len(global_citation_map)} sources mapped up to [{next_citation_num - 1}]")
    
    return results

def compile_final_memo(db: Session, memo_request_id: int) -> str:
    """Compile all completed sections into a final memo with global citations"""

    # Fetch completed sections for this memo
    sections = db.query(MemoSection).filter(
        MemoSection.memo_request_id == memo_request_id,
        MemoSection.status == "completed"
    ).all()

    if not sections:
        return "No completed sections found for this memo."

    memo_parts = []
    all_sources = set()

    # Define logical display order
    section_order = [
        "executive_summary", "company_snapshot", "people",
        "market_opportunity", "competitive_landscape", "product",
        "financial", "traction_validation", "deal_considerations",
        "assessment_people", "assessment_market_opportunity",
        "assessment_product", "assessment_financials",
        "assessment_traction_validation", "assessment_deal_considerations"
    ]

    # Build body of the memo
    for section_name in section_order:
        section = next((s for s in sections if s.section_name == section_name), None)
        if section and section.content:
            title = section_name.replace("_", " ").title()
            memo_parts.append(f"## {title}\n\n{section.content.strip()}")
            if section.data_sources:
                all_sources.update(section.data_sources)

    # Build Sources section
    if all_sources:
        memo_parts.append("\n## Sources\n")
        # Sort alphabetically for consistent order
        sorted_sources = sorted(list(all_sources))
        for idx, source in enumerate(sorted_sources, 1):
            memo_parts.append(f"[{idx}] {source}")

    return "\n\n".join(memo_parts)

def load_short_memo_prompts() -> Dict[str, Any]:
    """Load short memo prompts from JSON file"""
    prompts_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', 'memo_prompts.json')
    with open(prompts_path, 'r') as f:
        data = json.load(f)
        short_memo_prompts = data.get("short_memo", {})
        print(f"Loaded short memo prompts: {list(short_memo_prompts.keys())}")
        return short_memo_prompts

def generate_short_memo(
    company_data: Dict[str, Any],
    db: Session,
    memo_request_id: int
) -> Dict[str, Any]:
    """Generate a 1-page memo with 6 key sections"""
    # Define short memo sections first
    short_sections = [
        "problem",
        "solution",
        "company_brief",
        "startup_overview", 
        "founder_team",
        "deal_traction",
        "competitive_landscape",
        "remarks"
    ]
    
    try:
        # Get source_id from company_data
        source_id = company_data.get("source_id")
        if not source_id:
            raise ValueError("source_id not found in company_data")
            
        # Build knowledge base
        knowledge_base, all_sources = build_company_knowledge_base(db, source_id)
        
        # Load short memo prompts
        short_prompts = load_short_memo_prompts()
        
        results = {
            "status": "completed",
            "sections_completed": [],
            "sections_failed": [],
            "sources_used": list(all_sources)
        }
        
        # Generate each section
        for section_name in short_sections:
            try:
                prompt = short_prompts.get(section_name, f"Generate content for {section_name}")
                print(f"Using prompt for {section_name}: {prompt[:50]}...")
                
                # Use RAG to get relevant context
                context_data = retrieve_context_for_section(
                    section_name,
                    prompt,
                    knowledge_base,
                    all_sources,
                    company_data.get("company_name", "Unknown Company")
                )
                
                # Generate section content
                section_result = generate_memo_section_with_rag(
                    section_name,
                    prompt,
                    company_data,
                    knowledge_base,
                    all_sources,
                    db,
                    memo_request_id
                )
                
                print(f"Generated content for {section_name}: {section_result.get('content', 'NO CONTENT')[:100]}...")
                
                # Save to database
                memo_section = MemoSection(
                    memo_request_id=memo_request_id,
                    section_name=section_name,
                    content=section_result["content"],
                    data_sources=context_data.get('sources', []),
                    status="completed"
                )
                db.add(memo_section)
                db.commit()
                
                print(f"✅ Saved {section_name} to database")
                results["sections_completed"].append(section_name)
                
            except Exception as e:
                print(f"Error generating {section_name}: {str(e)}")
                results["sections_failed"].append(section_name)
                
                # Save failed section
                memo_section = MemoSection(
                    memo_request_id=memo_request_id,
                    section_name=section_name,
                    content="",
                    status="failed",
                    error_log=str(e)
                )
                db.add(memo_section)
                db.commit()
        
        # Update overall status
        if results["sections_failed"]:
            results["status"] = "partial"
        else:
            results["status"] = "completed"
            
        return results
        
    except Exception as e:
        print(f"Error in generate_short_memo: {str(e)}")
        return {
            "status": "failed",
            "sections_completed": [],
            "sections_failed": short_sections,
            "sources_used": [],
            "error": str(e)
        }

def compile_short_memo(db: Session, memo_request_id: int) -> str:
    """Compile all completed short memo sections into a final memo with global citations"""
    sections = db.query(MemoSection).filter(
        MemoSection.memo_request_id == memo_request_id,
        MemoSection.status == "completed"
    ).all()
    
    if not sections:
        return "No completed sections found."
    
    # Define the order for short memo sections
    section_order = [
        "company_brief", "startup_overview", "founder_team",
        "deal_traction", "competitive_landscape", "remarks"
    ]
    
    # Create a mapping of section names to content
    section_map = {section.section_name: section.content for section in sections}
    
    memo_parts = []
    all_sources = set()
    
    # Add sections in the correct order
    for section_name in section_order:
        if section_name in section_map:
            memo_parts.append(f"## {section_name.replace('_', ' ').title()}")
            memo_parts.append(section_map[section_name])
            
            # Collect sources from this section
            section_obj = next((s for s in sections if s.section_name == section_name), None)
            if section_obj and section_obj.data_sources:
                all_sources.update(section_obj.data_sources)
    
    # Build Sources section
    if all_sources:
        memo_parts.append("\n## Sources\n")
        # Sort alphabetically for consistent order
        sorted_sources = sorted(list(all_sources))
        for idx, source in enumerate(sorted_sources, 1):
            memo_parts.append(f"[{idx}] {source}")
    
    return "\n\n".join(memo_parts)
