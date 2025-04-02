"""
Legacy web scraper module that now imports from the modular package structure.
This module is kept for backward compatibility.
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log a deprecation warning when this module is imported
logger.warning(
    "The monolithic web_scraper.py is deprecated and will be removed in a future version. "
    "Please update your imports to use the new modular structure: "
    "from utils.web_scraper import search_medical_sites, load_trusted_domains_from_config, is_trusted_domain"
)

# Import all required functions from the modular structure
from utils.web_scraper.core import search_medical_sites
from utils.web_scraper.config import load_trusted_domains_from_config, is_trusted_domain, get_search_settings
from utils.web_scraper.utils import get_common_headers, clean_text, sanitize_query
from utils.web_scraper.content_extractor import get_detailed_content, get_pubmed_abstract

# Import provider functions for backward compatibility
from utils.web_scraper.providers import (
    search_nih,
    search_cdc,
    search_mayo_clinic,
    search_webmd,
    search_healthline,
    search_medical_news_today,
    search_pubmed,
    search_who,
    search_reuters_health # Import the new Reuters provider
)

# Get trusted domains for backward compatibility
TRUSTED_DOMAINS = load_trusted_domains_from_config()

# Re-export all the functions for backward compatibility
__all__ = [
    'search_medical_sites',
    'load_trusted_domains_from_config',
    'is_trusted_domain',
    'get_common_headers',
    'clean_text',
    'get_detailed_content',
    'get_pubmed_abstract',
    'search_nih',
    'search_cdc',
    'search_mayo_clinic',
    'search_webmd',
    'search_healthline',
    'search_medical_news_today',
    'search_pubmed',
    'search_who',
    'search_reuters_health', # Add Reuters to exports
    'TRUSTED_DOMAINS'
]

if __name__ == "__main__":
    # Simple test
    query = "latest treatments for type 2 diabetes"
    print(f"Searching for: {query}")
    results = search_medical_sites(query, max_results=3)
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Source: {result['source']}")
        if 'title' in result:
            print(f"Title: {result['title']}")
        print(f"Content: {result.get('content', '')[:100]}...")