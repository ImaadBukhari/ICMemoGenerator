import json
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.db.models import MemoRequest, MemoSection
from backend.services.gpt_service import generate_text
from backend.services.rag_service import build_company_knowledge_base, retrieve_context_for_section

def build_core_context(company_data, chunks, system_message):
    """Create a unified factual summary from all RAG and CRM data"""
    base_prompt = f"""
You are preparing an internal context brief for a VC investment memo.
Summarize all key factual information about the company concisely and accurately.

Include:
- Company name, founding year, HQ, and sector
- Core product and value proposition
- Market context or key trends
- Funding history and investors
- Key metrics (customers, ARR, employees)
- Geographic footprint

Do not include analysis, tone, or opinions — just facts. Keep under 400 words.
"""
    rag_text = "\n".join(c["text"] for c in chunks[:20])
    full_prompt = f"{base_prompt}\n\n=== RAW DATA ===\n{rag_text}"
    return generate_text(full_prompt, system_message, model="gpt-4-turbo-preview", temperature=0.2)


def format_affinity_data(affinity_data: Dict[str, Any]) -> str:
    """Format Affinity CRM data for prompts with Crunchbase attribution"""
    if not affinity_data:
        return "No CRM data available."
    
    formatted_sections = []
    
    # Add header with source attribution
    formatted_sections.append("=== CRM DATA (Source: Crunchbase) ===\n")
    
    key_fields = [
        'name', 'stage', 'industry', 'description', 'website',
        'funding_stage', 'last_funding_amount', 'total_funding',
        'valuation', 'employees', 'headquarters', 'founded_date'
    ]
    
    for field in key_fields:
        if field in affinity_data and affinity_data[field]:
            formatted_sections.append(f"{field.replace('_', ' ').title()}: {affinity_data[field]}")
    
    formatted_sections.append("\n[All CRM data sourced from Crunchbase via Affinity CRM]")
    
    return "\n".join(formatted_sections) if len(formatted_sections) > 2 else "Limited CRM data available."

# Load memo prompts
def load_memo_prompts() -> Dict[str, Any]:
    """Load memo prompts from JSON file"""
    prompts_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', 'memo_prompts.json')
    with open(prompts_path, 'r') as f:
        return json.load(f)

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

system_message = """
You are a senior investment analyst at Wyld VC, an AI-first venture capital firm investing primarily in early-stage (Seed–Series B) technology companies in Silicon Valley and the Middle East.

Your writing should reflect the tone and rigor of a top-tier venture capital investment committee.
- Be analytical, structured, and data-driven.
- Use concise, professional language that reads like a formal IC memo or equity research report.
- Prioritize intellectual honesty and clear reasoning; avoid marketing language or unsubstantiated optimism.
- Highlight both upside and risk with equal precision.
- When making qualitative judgments, anchor them in concrete data (traction, TAM, growth rates, retention, competitive position).
- Assume the reader is a sophisticated investor—avoid basic explanations and focus on insight and signal.

When uncertain, state assumptions explicitly rather than speculating.
Write in complete sentences, but keep paragraphs tight and efficient.
Do not include filler text, self-references, or generic conclusions.
"""


def generate_memo_section_with_rag(
    section_key: str,
    prompt: str,
    company_data: Dict[str, Any],
    faiss_index,
    chunks: List[Dict[str, Any]],
    db: Session,
    memo_request_id: int,
    core_context: Optional[str] = None
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
        
        # Format Affinity data with Crunchbase attribution - ADD THIS
        affinity_section = format_affinity_data(company_data.get("affinity_data", {}))
        
        # Create enhanced prompt
        enhanced_prompt = f"""
{prompt}

Use the following base company context for consistency:
{core_context}

Now, using only the additional context below, write the section:
{rag_context['context']}

Do not restate facts already covered in the base context.
End naturally without conclusions or transitions.
When citing information, reference the citation numbers [1], [2], etc.
All Affinity CRM data should be cited as "Source: Crunchbase"  # ADD THIS LINE
Prioritize quantitative data, specific metrics, and statistics
...
"""

        if section_key in ["market_opportunity", "competitive_landscape", "financial"]:
            # Analytical sections need lower temperature for precision
            max_tokens = 2500
            temperature = 0.3
        elif section_key.startswith("assessment_"):
            # Assessments need even more precision for ratings
            max_tokens = 1500
            temperature = 0.2
        elif section_key == "executive_summary":
            # Executive summary needs balance
            max_tokens = 2000
            temperature = 0.3
        elif section_key == "company_snapshot":
            max_tokens = 500
            temperature = 0.2
        else:
            # Descriptive sections (people, company_snapshot, product, traction_validation, deal_considerations)
            max_tokens = 2000
            temperature = 0.4

        # Generate content
        content = generate_text(
            enhanced_prompt,     
            system_message,       
            model="gpt-4-turbo-preview",
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Add Crunchbase to sources if Affinity data was used - ADD THIS
        sources = rag_context['sources'].copy()
        if company_data.get("affinity_data"):
            sources.append("Crunchbase (via Affinity CRM)")
        
        # Store the section with source information
        memo_section = MemoSection(
            memo_request_id=memo_request_id,
            section_name=section_key,
            content=content,
            data_sources=sources,  # Now includes Crunchbase
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
            "content_length": len(content),
            "data_sources_used": sources,
            "sources_count": len(sources)
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
            "status": "success",
            "section_name": section_key,
            "section_id": memo_section.id,
            "content_length": len(content),
            "data_sources_used": rag_context['sources'],
            "sources_count": len(rag_context['sources'])
        }

def generate_comprehensive_memo(
    company_data: Dict[str, Any],
    db: Session,
    memo_request_id: int
) -> Dict[str, Any]:
    """Generate all memo sections systematically using RAG"""
    
    print(f"Starting comprehensive memo generation for memo request {memo_request_id}")
    
    # Build FAISS index from company data
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
    
    # Load prompts
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
    
    # Generate main sections
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
    
    # Generate assessment sections
    assessment_sections = [
        ("assessment_people", "people"),
        ("assessment_market_opportunity", "market_opportunity"),
        ("assessment_product", "product"),
        ("assessment_financials", "financials"),
        ("assessment_traction_validation", "traction_validation"),
        ("assessment_deal_considerations", "deal_considerations")
    ]

    core_context = build_core_context(company_data, chunks, system_message)
    
    # Process main sections
    for section in main_sections:
        if section in prompts:
            result = generate_memo_section_with_rag(
            section,
            prompts[section],
            company_data,
            faiss_index,
            chunks,
            db,
            memo_request_id,
            core_context=core_context
        )
            
            if result["status"] == "success":
                results["sections_completed"].append(result)
            else:
                results["sections_failed"].append(result)
        else:
            print(f"⚠️ Prompt not found for section: {section}")
    
    # Process assessment sections
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
                results["sections_completed"].append(result)
            else:
                results["sections_failed"].append(result)
        else:
            print(f"⚠️ Assessment prompt not found for: {assessment_key}")
    
    # Calculate final results
    results["total_sections"] = len(results["sections_completed"]) + len(results["sections_failed"])
    results["success_rate"] = len(results["sections_completed"]) / results["total_sections"] if results["total_sections"] > 0 else 0
    
    # Determine final status
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
    
    return results

def compile_final_memo(db: Session, memo_request_id: int) -> str:
    """Compile all sections into final memo with sources"""
    sections = db.query(MemoSection).filter(
        MemoSection.memo_request_id == memo_request_id,
        MemoSection.status == "completed"
    ).all()
    
    memo_parts = []
    all_sources = set()
    
    section_order = [
        "executive_summary", "company_snapshot", "people", 
        "market_opportunity", "competitive_landscape", "product",
        "financial", "traction_validation", "deal_considerations"
    ]
    
    for section_name in section_order:
        section = next((s for s in sections if s.section_name == section_name), None)
        if section and section.content:
            memo_parts.append(f"## {section_name.replace('_', ' ').title()}\n\n{section.content}")
            if section.data_sources:
                all_sources.update(section.data_sources)
    
    # Add sources section
    if all_sources:
        memo_parts.append("\n## Sources\n")
        for i, source in enumerate(sorted(all_sources), 1):
            memo_parts.append(f"{i}. {source}")
    
    return "\n\n".join(memo_parts)