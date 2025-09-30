import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from perplexity import Perplexity
    PERPLEXITY_AVAILABLE = True
except ImportError:
    PERPLEXITY_AVAILABLE = False
    print("Perplexity client not installed. Run: pip install perplexity-ai")

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

def perplexity_search(
    query: str,
    max_results: int = 5,
    max_tokens_per_page: int = 1024
) -> Dict[str, Any]:
    """
    Simple Perplexity search using the official client.
    """
    if not PERPLEXITY_AVAILABLE:
        return {
            "error": "Perplexity client not installed",
            "search_successful": False
        }
    
    if not PERPLEXITY_API_KEY:
        return {
            "error": "Perplexity API key not configured",
            "search_successful": False
        }
    
    try:
        client = Perplexity(api_key=PERPLEXITY_API_KEY)
        
        search = client.search.create(
            query=query,
            max_results=max_results,
            max_tokens_per_page=max_tokens_per_page
        )
        
        # Combine all search results into a single content string
        content_parts = []
        for result in search.results:
            content_parts.append(f"**{result.title}**")
            content_parts.append(f"Source: {result.url}")
            if hasattr(result, 'content') and result.content:
                content_parts.append(result.content)
            elif hasattr(result, 'snippet') and result.snippet:
                content_parts.append(result.snippet)
            content_parts.append("---")
        
        return {
            "content": "\n".join(content_parts),
            "search_successful": True,
            "results_count": len(search.results)
        }
        
    except Exception as e:
        return {
            "error": f"Perplexity search failed: {str(e)}",
            "search_successful": False
        }

def search_company_by_category(company_name: str, category: str) -> Dict[str, Any]:
    """
    Search for company information using predefined category prompts.
    """
    RESEARCH_PROMPTS = {
        "company_overview": f"What is {company_name} company? Provide company background, business model, products, and services",
        "market_analysis": f"Market analysis for {company_name}: market size, growth trends, opportunities, and market dynamics",
        "competitive_landscape": f"Who are {company_name} competitors? Competitive landscape and market positioning analysis",
        "financial_analysis": f"{company_name} funding rounds, valuation, revenue, financial metrics, and investor information",
        "team_and_investors": f"{company_name} founders, management team, key employees, investors, and company leadership",
        "technology_and_product": f"{company_name} technology stack, product features, technical capabilities, and innovation",
        "traction_and_metrics": f"{company_name} customer growth, business metrics, user adoption, and key performance indicators",
        "risks_and_challenges": f"{company_name} business risks, market challenges, competitive threats, and potential problems"
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

def search_company_comprehensive(company_name: str) -> Dict[str, Any]:
    """
    Perform comprehensive research on a company using all categories.
    """
    results = {
        "company_name": company_name,
        "categories": {},
        "overall_success": True,
        "errors": []
    }
    
    categories = [
        "company_overview", "market_analysis", "competitive_landscape", 
        "financial_analysis", "team_and_investors", "technology_and_product",
        "traction_and_metrics", "risks_and_challenges"
    ]
    
    for category in categories:
        print(f"Researching {category} for {company_name}...")
        category_result = search_company_by_category(company_name, category)
        
        results["categories"][category] = category_result
        
        if not category_result.get("search_successful"):
            results["overall_success"] = False
            results["errors"].append(f"{category}: {category_result.get('error', 'Unknown error')}")
    
    return results

def search_company_stats_and_metrics(company_name: str) -> Dict[str, Any]:
    """
    Search for specific stats, metrics, and quantitative data about a company and its market.
    """
    stats_queries = {
        "financial_metrics": f"""
        Find specific financial data and metrics for {company_name}:
        - Revenue figures (ARR, MRR, total revenue)
        - Growth rates (YoY, QoQ revenue growth)
        - Funding amounts and valuations
        - Employee count and growth
        - Customer count and acquisition metrics
        - Market share data
        - Burn rate and runway information
        """,
        
        "market_metrics": f"""
        Find market size and industry metrics related to {company_name}'s market:
        - Total Addressable Market (TAM) size
        - Serviceable Addressable Market (SAM) size
        - Market growth rates and projections
        - Industry benchmarks and averages
        - Competitive market share data
        - Market penetration rates
        - Industry revenue multiples and valuations
        """,
        
        "operational_metrics": f"""
        Find operational and business metrics for {company_name}:
        - Customer acquisition cost (CAC)
        - Lifetime value (LTV) and LTV/CAC ratios
        - Churn rates and retention metrics
        - Gross margins and unit economics
        - Sales efficiency metrics
        - Product usage and engagement stats
        - Geographic presence and expansion data
        """,
        
        "comparative_metrics": f"""
        Find comparative data and benchmarks for {company_name}:
        - Competitor revenue and valuation comparisons
        - Industry average growth rates
        - Benchmark metrics for similar companies
        - Market leader performance comparisons
        - Funding round comparisons in the sector
        - Valuation multiples for similar companies
        - Performance relative to industry standards
        """
    }
    
    results = {
        "company_name": company_name,
        "stats_categories": {},
        "search_success": True,
        "errors": []
    }
    
    for category, query in stats_queries.items():
        try:
            print(f"Searching {category} for {company_name}...")
            result = perplexity_search(query, max_results=7, max_tokens_per_page=1500)
            
            if result.get("search_successful"):
                results["stats_categories"][category] = {
                    "content": result["content"],
                    "search_successful": True,
                    "category": category
                }
            else:
                results["stats_categories"][category] = {
                    "error": result.get("error", "Unknown error"),
                    "search_successful": False,
                    "category": category
                }
                results["errors"].append(f"{category}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            results["stats_categories"][category] = {
                "error": str(e),
                "search_successful": False,
                "category": category
            }
            results["errors"].append(f"{category}: {str(e)}")
    
    # Check if any searches were successful
    successful_searches = sum(1 for cat in results["stats_categories"].values() if cat.get("search_successful"))
    results["search_success"] = successful_searches > 0
    results["successful_categories"] = successful_searches
    results["total_categories"] = len(stats_queries)
    
    return results

def search_company_comprehensive_with_stats(company_name: str) -> Dict[str, Any]:
    """
    Enhanced comprehensive search that includes both regular research and stats/metrics.
    """
    print(f"Starting comprehensive research with stats for {company_name}...")
    
    # Run regular comprehensive search
    regular_research = search_company_comprehensive(company_name)
    
    # Run stats and metrics search
    stats_research = search_company_stats_and_metrics(company_name)
    
    # Combine results
    enhanced_results = {
        "company_name": company_name,
        "categories": regular_research.get("categories", {}),
        "stats_categories": stats_research.get("stats_categories", {}),
        "overall_success": regular_research.get("overall_success", False),
        "stats_success": stats_research.get("search_success", False),
        "errors": regular_research.get("errors", []) + stats_research.get("errors", []),
        "research_summary": {
            "regular_categories_successful": len([c for c in regular_research.get("categories", {}).values() if c.get("search_successful")]),
            "stats_categories_successful": stats_research.get("successful_categories", 0),
            "total_regular_categories": len(regular_research.get("categories", {})),
            "total_stats_categories": stats_research.get("total_categories", 0)
        }
    }
    
    return enhanced_results

# Backward compatibility
def search_company_info(company_name: str) -> Dict[str, Any]:
    """
    Enhanced comprehensive company search with stats for backward compatibility.
    """
    try:
        # Use the enhanced comprehensive search
        enhanced_data = search_company_comprehensive_with_stats(company_name)
        
        # Format for backward compatibility
        research_parts = []
        
        # Add regular research content
        if enhanced_data.get("categories"):
            for category, data in enhanced_data["categories"].items():
                if data.get("search_successful") and data.get("content"):
                    title = category.replace('_', ' ').title()
                    research_parts.append(f"=== {title} ===\n{data['content']}")
        
        # Add stats content
        if enhanced_data.get("stats_categories"):
            research_parts.append("\n=== QUANTITATIVE METRICS & STATISTICS ===")
            for category, data in enhanced_data["stats_categories"].items():
                if data.get("search_successful") and data.get("content"):
                    title = category.replace('_', ' ').title()
                    research_parts.append(f"\n--- {title} ---\n{data['content']}")
        
        combined_content = "\n\n".join(research_parts)
        
        return {
            "company_name": company_name,
            "research_data": combined_content,
            "enhanced_data": enhanced_data,
            "search_successful": len(research_parts) > 0
        }
        
    except Exception as e:
        return {
            "company_name": company_name,
            "error": str(e),
            "search_successful": False
        }