import os
import requests
import re
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
        """Search for companies in Affinity by name."""
        try:
            url = f"{self.base_url}/organizations"
            params = {"term": query, "page_size": 10}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
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
        """Get detailed company information from Affinity."""
        try:
            url = f"{self.base_url}/organizations/{company_id}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            company_data = {
                "id": str(data.get("id")),
                "name": data.get("name"),
                "domain": data.get("domain"),
                "type": data.get("type"),
                "person_ids": data.get("person_ids", []),
                "list_entries": data.get("list_entries", [])
            }
            
            if "fields" in data:
                company_data["fields"] = data["fields"]
            
            return company_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting company data from Affinity: {e}")
            raise


def get_company_details(company_id: str):
    """Get details for a single company by ID."""
    url = f"{BASE_URL}/organizations/{company_id}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()

def get_list_entries(list_id: int) -> List[Dict[str, Any]]:
    """
    Get all list entries from a specific Affinity list.
    Returns list of organizations with their data.
    """
    try:
        url = f"{BASE_URL}/lists/{list_id}/list-entries"
        all_entries = []
        page = 1
        page_size = 500
        
        while True:
            params = {"page": page, "page_size": page_size}
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            entries = data.get("list_entries", [])
            
            if not entries:
                break
            
            all_entries.extend(entries)
            
            # Check if there are more pages
            if len(entries) < page_size:
                break
            
            page += 1
        
        return all_entries
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting list entries from Affinity: {e}")
        raise

def find_company_by_url(list_id: int, company_url: str) -> Optional[Dict[str, Any]]:
    """
    Find a company in a specific Affinity list by matching URL.
    Returns company data if found, None otherwise.
    """
    try:
        # Normalize the URL for comparison (remove protocol, www, trailing slashes)
        def normalize_url(url: str) -> str:
            if not url:
                return ""
            url = url.lower().strip()
            # Remove protocol
            url = re.sub(r'^https?://', '', url)
            # Remove www.
            url = re.sub(r'^www\.', '', url)
            # Remove trailing slash
            url = url.rstrip('/')
            return url
        
        normalized_search_url = normalize_url(company_url)
        
        if not normalized_search_url:
            return None
        
        # Get all entries from the list
        entries = get_list_entries(list_id)
        
        # Search through entries to find matching organization
        for entry in entries:
            organization_id = entry.get("entity_id")
            if not organization_id:
                continue
            
            # Get full organization data
            try:
                org_url = f"{BASE_URL}/organizations/{organization_id}"
                org_response = requests.get(org_url, headers=HEADERS, timeout=30)
                org_response.raise_for_status()
                org_data = org_response.json()
                
                # Check if the organization's domain matches
                domain = org_data.get("domain", "").lower().strip()
                if domain:
                    normalized_domain = normalize_url(domain)
                    if normalized_domain == normalized_search_url:
                        return org_data
                
                # Also check if URL is in fields
                fields = org_data.get("fields", [])
                for field in fields:
                    field_value = str(field.get("value", "")).lower().strip()
                    if field_value:
                        normalized_field = normalize_url(field_value)
                        if normalized_field == normalized_search_url:
                            return org_data
                            
            except requests.exceptions.RequestException:
                continue  # Skip this entry if we can't fetch org data
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding company by URL: {e}")
        return None
