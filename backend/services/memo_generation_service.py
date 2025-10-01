import json
import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from db.models import MemoRequest, MemoSection
from services.gpt_service import generate_text

# Load memo prompts
def load_memo_prompts() -> Dict[str, Any]:
    """Load memo prompts from JSON file"""
    prompts_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', 'memo_prompts.json')
    with open(prompts_path, 'r') as f:
        return json.load(f)

# Mapping of memo sections to relevant Perplexity categories
SECTION_DATA_MAPPING = {
    "executive_summary": ["company_overview", "financial_analysis"],
    "company_snapshot": ["company_overview"],
    "people": ["team_and_investors"],
    "market_opportunity": ["market_analysis"],
    "competitive_landscape": ["competitive_landscape"],
    "product": ["technology_and_product"],
    "financial": ["financial_analysis"],
    "traction_validation": ["traction_and_metrics"],
    "deal_considerations": ["financial_analysis", "risks_and_challenges"],
    # Assessment sections (ratings) - now with stats emphasis
    "assessment_people": ["team_and_investors"],
    "assessment_market_opportunity": ["market_analysis"],
    "assessment_product": ["technology_and_product"],
    "assessment_financials": ["financial_analysis"],
    "assessment_traction_validation": ["traction_and_metrics"],
    "assessment_deal_considerations": ["financial_analysis", "risks_and_challenges"]
}

def extract_relevant_perplexity_data(
    perplexity_data: Dict[str, Any], 
    categories: List[str]
) -> str:
    """Extract and format relevant Perplexity data including stats for specific categories"""
    
    if not perplexity_data:
        return "No market research data available."
    
    relevant_sections = []
    
    # Extract regular research categories
    if perplexity_data.get("categories"):
        for category in categories:
            if category in perplexity_data["categories"]:
                category_data = perplexity_data["categories"][category]
                if category_data.get("search_successful") and category_data.get("content"):
                    title = category.replace('_', ' ').title()
                    content = category_data["content"]
                    # Truncate to avoid token limits
                    if len(content) > 2000:
                        content = content[:2000] + "... [truncated]"
                    relevant_sections.append(f"=== {title} ===\n{content}")
    
    # Always include relevant stats and metrics
    if perplexity_data.get("stats_categories"):
        stats_sections = []
        
        # Map memo sections to relevant stats categories
        stats_mapping = {
            "financial": ["financial_metrics", "operational_metrics"],
            "traction_validation": ["operational_metrics", "comparative_metrics"],
            "market_opportunity": ["market_metrics", "comparative_metrics"],
            "deal_considerations": ["financial_metrics", "comparative_metrics"],
            "competitive_landscape": ["comparative_metrics"],
            "product": ["operational_metrics"],
            "executive_summary": ["financial_metrics", "market_metrics"]
        }
        
        # Determine which stats to include based on the section
        section_key = None
        for key in stats_mapping:
            if key in str(categories).lower():
                section_key = key
                break
        
        if section_key and section_key in stats_mapping:
            relevant_stats_categories = stats_mapping[section_key]
        else:
            # Default to financial and operational metrics
            relevant_stats_categories = ["financial_metrics", "operational_metrics"]
        
        for stats_category in relevant_stats_categories:
            if stats_category in perplexity_data["stats_categories"]:
                stats_data = perplexity_data["stats_categories"][stats_category]
                if stats_data.get("search_successful") and stats_data.get("content"):
                    title = stats_category.replace('_', ' ').title()
                    content = stats_data["content"]
                    if len(content) > 1500:
                        content = content[:1500] + "... [truncated]"
                    stats_sections.append(f"--- {title} ---\n{content}")
        
        if stats_sections:
            relevant_sections.append(f"\n=== QUANTITATIVE METRICS & STATISTICS ===\n" + "\n\n".join(stats_sections))
    
    return "\n\n".join(relevant_sections) if relevant_sections else "Limited market research and metrics data available."

def format_affinity_data(affinity_data: Dict[str, Any]) -> str:
    """Format Affinity CRM data for prompts"""
    
    if not affinity_data:
        return "No CRM data available."
    
    formatted_sections = []
    
    # Extract key Affinity fields
    key_fields = [
        'name', 'stage', 'industry', 'description', 'website',
        'funding_stage', 'last_funding_amount', 'total_funding',
        'valuation', 'employees', 'headquarters', 'founded_date'
    ]
    
    for field in key_fields:
        if field in affinity_data and affinity_data[field]:
            formatted_sections.append(f"{field.replace('_', ' ').title()}: {affinity_data[field]}")
    
    # Add any other fields
    for key, value in affinity_data.items():
        if key not in key_fields and value:
            formatted_sections.append(f"{key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted_sections) if formatted_sections else "Limited CRM data available."

def generate_memo_section(
    section_key: str,
    prompt: str,
    company_data: Dict[str, Any],
    db: Session,
    memo_request_id: int
) -> Dict[str, Any]:
    """Generate a single memo section using GPT with enhanced data including stats"""
    
    try:
        print(f"Generating section: {section_key}")
        
        # Get relevant Perplexity data for this section (now includes stats)
        relevant_categories = SECTION_DATA_MAPPING.get(section_key, [])
        perplexity_section = extract_relevant_perplexity_data(
            company_data.get("perplexity_data", {}), 
            relevant_categories
        )
        
        # Format Affinity data
        affinity_section = format_affinity_data(company_data.get("affinity_data", {}))
        
        # Create enhanced data context with stats emphasis
        data_context = f"""
COMPANY: {company_data.get('company_name', 'Unknown')}

=== CRM DATA ===
{affinity_section}

=== MARKET RESEARCH & QUANTITATIVE ANALYSIS ===
{perplexity_section}
"""
        
        # Enhanced prompt with stats emphasis
        enhanced_prompt = f"""
{prompt}

Use the following comprehensive data about the company, including quantitative metrics and statistics:

{data_context}

IMPORTANT INSTRUCTIONS:
1. Base your response ONLY on the data provided above
2. Prioritize quantitative data, specific metrics, and statistics where available
3. Include specific numbers, percentages, growth rates, and financial figures when mentioned in the data
4. If specific information is not available, clearly state that rather than making assumptions
5. When providing assessments or ratings, justify them with specific data points from the research
6. Highlight key statistics that support your analysis
"""
        
        # Generate content using GPT
        system_message = f"""
You are an expert venture capital analyst writing detailed investment memos. 
Your analysis should be highly data-driven, using specific metrics and statistics.
Focus on quantitative evidence and be transparent about data limitations.
For section '{section_key}', emphasize relevant financial and operational metrics.
"""
        
        content = generate_text(
            enhanced_prompt,
            system_message,
            model="gpt-4-turbo-preview",
            max_tokens=2000,  # Increased for stats-rich content
            temperature=0.2   # Lower temperature for more factual output
        )
        
        # Store the section in database with enhanced metadata
        memo_section = MemoSection(
            memo_request_id=memo_request_id,
            section_name=section_key,
            content=content,
            data_sources=relevant_categories + ["quantitative_metrics"],
            status="completed"
        )
        
        db.add(memo_section)
        db.commit()
        db.refresh(memo_section)
        
        print(f"✅ Section '{section_key}' generated successfully with enhanced stats")
        
        return {
            "section_name": section_key,
            "status": "success",
            "content_length": len(content),
            "data_sources_used": relevant_categories + ["quantitative_metrics"],
            "section_id": memo_section.id,
            "stats_included": True
        }
        
    except Exception as e:
        print(f"❌ Failed to generate section '{section_key}': {str(e)}")
        
        # Store failed section
        memo_section = MemoSection(
            memo_request_id=memo_request_id,
            section_name=section_key,
            content="",
            data_sources=relevant_categories,
            status="failed",
            error_log=str(e)
        )
        
        db.add(memo_section)
        db.commit()
        
        return {
            "section_name": section_key,
            "status": "failed",
            "error": str(e),
            "data_sources_attempted": relevant_categories
        }

def generate_comprehensive_memo(
    company_data: Dict[str, Any],
    db: Session,
    memo_request_id: int
) -> Dict[str, Any]:
    """Generate all memo sections systematically"""
    
    print(f"Starting comprehensive memo generation for memo request {memo_request_id}")
    
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
    
    # Generate assessment sections (with ratings)
    assessment_sections = [
        ("assessment_people", "people"),
        ("assessment_market_opportunity", "market_opportunity"),
        ("assessment_product", "product"),
        ("assessment_financials", "financials"),
        ("assessment_traction_validation", "traction_validation"),
        ("assessment_deal_considerations", "deal_considerations")
    ]
    
    # Process main sections
    for section in main_sections:
        if section in prompts:
            result = generate_memo_section(
                section,
                prompts[section],
                company_data,
                db,
                memo_request_id
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
            result = generate_memo_section(
                assessment_key,
                prompts["assessment_summary"][prompt_key],
                company_data,
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
    
    if len(results["sections_failed"]) == 0:
        results["status"] = "completed"
    elif len(results["sections_completed"]) > 0:
        results["status"] = "partial_success"
    else:
        results["status"] = "failed"
    
    # Generate summary
    results["generation_summary"] = {
        "completed_sections": len(results["sections_completed"]),
        "failed_sections": len(results["sections_failed"]),
        "success_rate": f"{results['success_rate']:.1%}",
        "company_name": company_data.get("company_name", "Unknown")
    }
    
    print(f"Memo generation completed: {results['success_rate']:.1%} success rate")
    
    return results

def compile_final_memo(db: Session, memo_request_id: int) -> str:
    """Compile all memo sections into a final document"""
    
    sections = db.query(MemoSection).filter(
        MemoSection.memo_request_id == memo_request_id,
        MemoSection.status == "completed"
    ).order_by(MemoSection.created_at).all()
    
    if not sections:
        return "No completed sections found for this memo."
    
    memo_parts = []
    memo_parts.append("# INVESTMENT COMMITTEE MEMO\n")
    
    # Section order for final compilation
    section_order = [
        ("executive_summary", "Executive Summary"),
        ("company_snapshot", "Company Snapshot"),
        ("people", "Team & Leadership"),
        ("market_opportunity", "Market Opportunity"),
        ("competitive_landscape", "Competitive Landscape"),
        ("product", "Product & Technology"),
        ("financial", "Financial Analysis"),
        ("traction_validation", "Traction & Validation"),
        ("deal_considerations", "Deal Considerations"),
        ("assessment_people", "Assessment: Team Rating"),
        ("assessment_market_opportunity", "Assessment: Market Rating"),
        ("assessment_product", "Assessment: Product Rating"),
        ("assessment_financials", "Assessment: Financial Rating"),
        ("assessment_traction_validation", "Assessment: Traction Rating"),
        ("assessment_deal_considerations", "Assessment: Deal Rating")
    ]
    
    # Create a lookup for sections
    sections_dict = {section.section_name: section for section in sections}
    
    # Add sections in order
    for section_key, section_title in section_order:
        if section_key in sections_dict:
            memo_parts.append(f"\n## {section_title}\n")
            memo_parts.append(sections_dict[section_key].content)
            memo_parts.append("\n---\n")
    
    return "\n".join(memo_parts)