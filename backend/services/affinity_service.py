import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables for local dev
load_dotenv()

AFFINITY_API_KEY = os.getenv("AFFINITY_API_KEY")
BASE_URL = "https://api.affinity.co/v2"
HEADERS = {"Authorization": f"Bearer {AFFINITY_API_KEY}"}


class AffinityService:
    """Service class for Affinity CRM operations"""
    
    def __init__(self):
        self.api_key = AFFINITY_API_KEY
        self.base_url = BASE_URL
        self.headers = HEADERS
        
        if not self.api_key:
            raise ValueError("AFFINITY_API_KEY not found in environment variables")
    
    def search_companies(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for companies in Affinity by name.
        """
        try:
            # Use the organizations endpoint with search
            url = f"{self.base_url}/organizations"
            params = {
                "term": query,
                "page_size": 10
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response
            companies = []
            if "organizations" in data:
                for org in data["organizations"]:
                    companies.append({
                        "id": str(org.get("id")),
                        "name": org.get("name"),
                        "domain": org.get("domain"),
                        "type": org.get("type")
                    })
            
            return companies
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching companies in Affinity: {e}")
            return []
    
    def get_company_data(self, company_id: str) -> Dict[str, Any]:
        """
        Get detailed company information from Affinity.
        """
        logger.info(f"Fetching company data for ID: {company_id}")
        try:
            url = f"{self.base_url}/organizations/{company_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Company data fetched: {data}")
            
            # Format the company data
            company_data = {
                "id": str(data.get("id")),
                "name": data.get("name"),
                "domain": data.get("domain"),
                "type": data.get("type"),
                "person_ids": data.get("person_ids", []),
                "list_entries": data.get("list_entries", [])
            }
            
            # Get additional fields if available
            if "fields" in data:
                company_data["fields"] = data["fields"]
            
            return company_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting company data from Affinity: {e}")
            raise


# Keep the original functions for backward compatibility
def get_companies(page_url: str | None = None):
    """
    Get a list of companies from Affinity.
    Returns companies and next_page_url if more pages are available.
    """
    url = page_url if page_url else f"{BASE_URL}/organizations"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        data = response.json()
        
        companies = data.get("organizations", [])
        next_page = data.get("next_page_token")
        
        return {
            "companies": companies,
            "next_page_token": next_page,
            "success": True
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching companies: {e}")
        return {
            "companies": [],
            "next_page_token": None,
            "success": False,
            "error": str(e)
        }


def get_company_details(company_id: str):
    """
    Get details for a single company by ID.
    """
    url = f"{BASE_URL}/organizations/{company_id}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        company_data = response.json()
        
        return {
            "success": True,
            "data": company_data
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching company details: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }