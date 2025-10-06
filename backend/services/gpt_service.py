import os
from openai import OpenAI
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_text(
    prompt: str,
    system_message: str = None,
    model: str = "gpt-4-turbo-preview",
    max_tokens: int = 3000,
    temperature: float = 0.7
) -> str:
    """
    Generate text using GPT API.
    """
    messages = []
    
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        raise Exception(f"GPT API error: {str(e)}")

def format_comprehensive_perplexity_data(perplexity_data: Dict[str, Any]) -> str:
    """
    Format comprehensive Perplexity data for prompt inclusion.
    """
    if not perplexity_data or not perplexity_data.get("categories"):
        return ""
    
    formatted_sections = []
    
    category_mapping = {
        "company_overview": "Company Background & Business Model",
        "market_analysis": "Market Analysis & Opportunity",
        "competitive_landscape": "Competitive Landscape",
        "financial_analysis": "Financial Information & Funding",
        "team_and_investors": "Team & Investors",
        "technology_and_product": "Technology & Product",
        "traction_and_metrics": "Traction & Key Metrics",
        "risks_and_challenges": "Risks & Challenges"
    }
    
    for category, data in perplexity_data["categories"].items():
        if data.get("search_successful") and data.get("content"):
            section_title = category_mapping.get(category, category.replace('_', ' ').title())
            formatted_sections.append(f"\n=== {section_title.upper()} ===")
            
            # Truncate content to avoid token limits
            content = data["content"]
            if len(content) > 2500:
                content = content[:2500] + "... [truncated]"
            formatted_sections.append(content)
    
    return "\n".join(formatted_sections)

def format_company_data_for_prompt(company_data: Dict[str, Any]) -> str:
    """
    Format company data into a readable format for the prompt.
    """
    formatted_sections = []
    
    # Company name
    formatted_sections.append(f"COMPANY: {company_data.get('company_name', 'Unknown')}")
    
    # Affinity CRM data
    if company_data.get("affinity_data"):
        formatted_sections.append("\n=== AFFINITY CRM DATA ===")
        affinity_data = company_data["affinity_data"]
        
        # Extract key fields from Affinity data
        if isinstance(affinity_data, dict):
            for key, value in affinity_data.items():
                if value:  # Only include non-empty values
                    formatted_sections.append(f"{key}: {value}")
        else:
            formatted_sections.append(str(affinity_data))
    
    # Google Drive files
    if company_data.get("drive_data") and company_data["drive_data"].get("files"):
        formatted_sections.append("\n=== GOOGLE DRIVE DOCUMENTS ===")
        files = company_data["drive_data"]["files"]
        
        for i, file in enumerate(files, 1):
            formatted_sections.append(f"\nDocument {i}: {file.get('name', 'Unknown')}")
            if file.get("content"):
                # Truncate content more aggressively to avoid token limits
                content = file["content"][:1500]
                if len(file["content"]) > 1500:
                    content += "... [truncated]"
                formatted_sections.append(f"Content: {content}")
            elif file.get("content_error"):
                formatted_sections.append(f"Content Error: {file['content_error']}")
    
    # Comprehensive Perplexity research data
    if company_data.get("perplexity_data"):
        perplexity_section = format_comprehensive_perplexity_data(company_data["perplexity_data"])
        if perplexity_section:
            formatted_sections.append("\n=== COMPREHENSIVE MARKET RESEARCH ===")
            formatted_sections.append(perplexity_section)
    
    return "\n".join(formatted_sections)

def generate_ic_memo_from_data(company_data: Dict[str, Any]) -> str:
    """
    Generate a VC IC memo based on provided company data using comprehensive research.
    """
    system_message = """
    You are an expert venture capital investment analyst. You write detailed Investment Committee (IC) memos 
    that help partners make informed investment decisions. Your memos should be comprehensive, analytical, 
    and include both opportunities and risks. Use the comprehensive research data provided to create a 
    well-structured, data-driven analysis.
    """
    
    # Format the data for the prompt
    formatted_data = format_company_data_for_prompt(company_data)
    
    prompt = f"""
    Generate a comprehensive VC Investment Committee Memo based on the following company information and research:

    {formatted_data}

    Structure the memo with the following sections, using the detailed research provided:

    1. **Executive Summary** 
       - Clear problem statement and solution
       - Key investment thesis with 2-3 main reasons to invest
       - Deal terms summary (if available)
       - Investment recommendation with key risks

    2. **Company Overview** 
       - Business model and value proposition
       - Stage of development and key milestones
       - Products/services and target customers

    3. **Market Opportunity** 
       - Market size (TAM/SAM/SOM) with specific data
       - Growth dynamics and market trends
       - Positioning within the market

    4. **Team Assessment** 
       - Founder backgrounds and relevant experience
       - Key team members and advisors
       - Previous achievements and track record

    5. **Product/Technology Analysis** 
       - Core technology and differentiation
       - Competitive advantages and IP
       - Product roadmap and scalability

    6. **Traction & Metrics** 
       - Customer acquisition and growth metrics
       - Revenue metrics and unit economics
       - Key partnerships and validation

    7. **Competitive Landscape** 
       - Direct and indirect competitors
       - Competitive positioning and advantages
       - Market share and differentiation

    8. **Financial Analysis** 
       - Current financial position
       - Funding history and valuation trends
       - Revenue model and path to profitability
       - Key financial metrics (LTV/CAC, burn rate, etc.)

    9. **Investment Highlights** 
       - Top 3-5 reasons this is an attractive investment
       - Unique value drivers and growth catalysts
       - Strategic advantages

    10. **Key Risks & Concerns** 
        - Market and competitive risks
        - Execution and team risks
        - Financial and operational risks
        - Mitigation strategies

    11. **Deal Considerations** 
        - Valuation analysis and comparables
        - Deal terms and structure
        - Exit opportunities and timeline
        - Expected returns (IRR/MOIC projections)

    12. **Recommendation** 
        - Clear invest/pass recommendation
        - Investment size and terms
        - Key milestones to monitor

    Make sure to:
    - Use specific data points from the research provided
    - Be analytical and balanced in your assessment
    - Highlight both opportunities and risks clearly
    - Support conclusions with evidence from the data
    - Use professional VC memo language and structure
    """
    
    return generate_text(prompt, system_message, model="gpt-4-turbo-preview", max_tokens=4000)