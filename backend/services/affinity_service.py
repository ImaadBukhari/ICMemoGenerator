# backend/services/affinity_service.py

import os
import requests
from dotenv import load_dotenv

# Load environment variables for local dev
load_dotenv()

AFFINITY_API_KEY = os.getenv("AFFINITY_API_KEY")
BASE_URL = "https://api.affinity.co/v2"
HEADERS = {"Authorization": f"Bearer {AFFINITY_API_KEY}"}


def get_companies(page_url: str | None = None):
    """
    Get the firm's entire 'rolodex' of companies.
    (Does not include list-specific fields — for that, use get_list_entries)
    """
    url = page_url or f"{BASE_URL}/companies"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_company_details(company_id: str):
    """
    Get details for a single company by ID.
    """
    url = f"{BASE_URL}/companies/{company_id}/list-entries"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()



