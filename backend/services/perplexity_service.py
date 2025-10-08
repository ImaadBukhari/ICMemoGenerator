import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import re

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

def extract_citations_from_content(content: str) -> List[str]:
    """Extract URLs from markdown-style citations in content"""
    citation_pattern = r'\[(\d+)\]\s*(https?://[^\s\)]+)'
    citations = re.findall(citation_pattern, content)
    return [url for _, url in citations]

def perplexity_search(query: str) -> Dict[str, Any]:
    """Perform a Perplexity search and extract citations"""
    try:
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'sonar',
                'messages': [{'role': 'user', 'content': query}],
                'return_citations': True,
                'return_images': False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            api_citations = data.get('citations', [])
            content_citations = extract_citations_from_content(content)
            all_citations = list(set(api_citations + content_citations))
            
            return {
                "search_successful": True,
                "content": content,
                "citations": all_citations,
                "api_citations": api_citations,
                "extracted_citations": content_citations
            }
        else:
            return {
                "search_successful": False,
                "content": "",
                "citations": [],
                "error": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "search_successful": False,
            "content": "",
            "citations": [],
            "error": str(e)
        }

def search_company_by_category(company_name: str, category: str, description: str = "") -> Dict[str, Any]:
    """
    Search for company information using STARTUP-SPECIFIC category prompts.
    """
    # Build context string from description
    context = f" The company is described as: {description}." if description else ""
    
    # IMPROVED PROMPTS with optional description context
    RESEARCH_PROMPTS = {
        "company_overview": f"What is the startup/company called '{company_name}'?{context} Focus on: business model, what products/services they offer, when they were founded, their mission, and what problem they solve. Exclude unrelated results about people, diseases, or concepts with the same name.",
        
        "market_analysis": f"What market does the startup '{company_name}' operate in?{context} Include: total addressable market size (TAM), growth trends, target customer segments, and market dynamics. Only include information about the company '{company_name}', not other entities with similar names.",
        
        "competitive_landscape": f"Who are the direct competitors of the startup/company '{company_name}'?{context} Include competitive analysis, market positioning, and how '{company_name}' differentiates from competitors. Focus only on the startup, not other entities.",
        
        "financial_analysis": f"What is the funding and financial information for the startup '{company_name}'?{context} Include: funding rounds, valuation, revenue metrics, investors, and financial performance. Only include data about the company '{company_name}'.",
        
        "team_and_investors": f"Who founded the startup '{company_name}' and who are the key team members?{context} Include: founder backgrounds, management team, investors, board members. Focus on the startup, not unrelated people with the same name.",
        
        "technology_and_product": f"What technology does the startup '{company_name}' use?{context} Describe their product features, technical stack, innovation, and IP. Only information about the company '{company_name}'.",
        
        "traction_and_metrics": f"What traction and growth metrics does the startup '{company_name}' have?{context} Include: customer growth, revenue growth, user adoption, key performance indicators. Focus on the company only.",
        
        "risks_and_challenges": f"What are the business risks and challenges facing the startup '{company_name}'?{context} Include: market risks, competitive threats, execution challenges. Only about the company '{company_name}'."
    }
    
    if category not in RESEARCH_PROMPTS:
        return {
            "error": f"Invalid category. Available categories: {list(RESEARCH_PROMPTS.keys())}",
            "search_successful": False
        }
    
    query = RESEARCH_PROMPTS[category]
    result = perplexity_search(query)
    
    if result.get("search_successful"):
        result["company_name"] = company_name
        result["category"] = category
    
    return result

def search_company_stats_and_metrics(company_name: str, description: str = "") -> Dict[str, Any]:
    """
    Search for STARTUP-SPECIFIC quantitative stats and metrics.
    """
    context = f" The company is described as: {description}." if description else ""
    
    STATS_CATEGORIES = {
        "revenue_metrics": f"What are the revenue metrics for the startup '{company_name}'?{context} Include: ARR/MRR, revenue growth rate, revenue per customer, gross margin. Only data about the company '{company_name}', not other entities.",
        
        "growth_metrics": f"What are the growth and traction metrics for the startup '{company_name}'?{context} Include: customer growth rate, user growth, market share growth, expansion metrics. Focus on the startup only.",
        
        "financial_health": f"What is the financial health of the startup '{company_name}'?{context} Include: burn rate, runway, cash position, unit economics, LTV/CAC ratio. Only about the company '{company_name}'.",
        
        "funding_data": f"What is the funding history of the startup '{company_name}'?{context} Include: all funding rounds with amounts, dates, valuations, lead investors, total funding raised. Only information about the company '{company_name}'.",
        
        "market_stats": f"What are the market size and opportunity statistics for the startup '{company_name}'?{context} Include: TAM/SAM/SOM figures, market growth rate, addressable market. Focus on the market the company '{company_name}' operates in.",
        
        "operational_metrics": f"What are the operational metrics for the startup '{company_name}'?{context} Include: team size, number of customers, retention rate, churn rate, expansion revenue. Only data about the company '{company_name}'."
    }
    
    results = {
        "company_name": company_name,
        "stats_categories": {},
        "successful_categories": 0,
        "total_categories": len(STATS_CATEGORIES)
    }
    
    for category, query in STATS_CATEGORIES.items():
        print(f"Searching stats for {category}...")
        result = perplexity_search(query)
        
        results["stats_categories"][category] = result
        
        if result.get("search_successful"):
            results["successful_categories"] += 1
    
    return results

# ... rest of the functions stay the same but with updated calls ...

def search_company_comprehensive_with_stats(company_name: str, description: str = "") -> Dict[str, Any]:
    """
    Enhanced comprehensive search with STARTUP-SPECIFIC prompts and optional description.
    """
    print(f"Starting comprehensive search for startup: {company_name}")
    if description:
        print(f"  Using description: {description}")
    
    # Pass description to category searches
    categories = [
        "company_overview", "market_analysis", "competitive_landscape",
        "financial_analysis", "team_and_investors", "technology_and_product",
        "traction_and_metrics", "risks_and_challenges"
    ]
    
    regular_research = {
        "company_name": company_name,
        "categories": {},
        "successful_categories": 0
    }
    
    for category in categories:
        print(f"Searching category: {category}")
        result = search_company_by_category(company_name, category, description)  # Pass description
        regular_research["categories"][category] = result
        
        if result.get("search_successful"):
            regular_research["successful_categories"] += 1
    
    # Stats research with description
    print("\nSearching for quantitative metrics...")
    stats_research = search_company_stats_and_metrics(company_name, description)  # Pass description
    
    enhanced_results = {
        "company_name": company_name,
        "categories": regular_research["categories"],
        "stats_categories": stats_research["stats_categories"],
        "search_metadata": {
            "regular_categories_successful": regular_research["successful_categories"],
            "stats_categories_successful": stats_research.get("successful_categories", 0),
            "total_regular_categories": len(regular_research.get("categories", {})),
            "total_stats_categories": stats_research.get("total_categories", 0)
        }
    }
    
    return enhanced_results

def search_company_comprehensive(company_name: str, db, description: str = "") -> Dict[str, Any]:
    """
    Main entry point for comprehensive company search with optional description.
    """
    from backend.db.models import Source
    
    try:
        # Get enhanced search results with description
        enhanced_data = search_company_comprehensive_with_stats(company_name, description)
        
        # Store description in Source record
        source = Source(
            company_name=company_name,
            perplexity_data=enhanced_data,
            company_description=description  # Store description (need to add this column to DB)
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        
        
        print(f"\n✅ Saved company data to database (source_id: {source.id})")
        print(f"   Regular categories: {enhanced_data['search_metadata']['regular_categories_successful']}/{enhanced_data['search_metadata']['total_regular_categories']}")
        print(f"   Stats categories: {enhanced_data['search_metadata']['stats_categories_successful']}/{enhanced_data['search_metadata']['total_stats_categories']}")
        
        # Return format expected by memo generation
        return {
            "company_name": company_name,
            "source_id": source.id,
            "enhanced_data": enhanced_data,
            "search_successful": True
        }
        
    except Exception as e:
        print(f"\n❌ Error in search_company_comprehensive: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "company_name": company_name,
            "error": str(e),
            "search_successful": False
        }