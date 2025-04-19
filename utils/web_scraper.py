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
    search_reuters_health
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
    'sanitize_query',
    'search_nih',
    'search_cdc',
    'search_mayo_clinic',
    'search_webmd',
    'search_healthline',
    'search_medical_news_today',
    'search_pubmed',
    'search_who',
    'search_reuters_health',
    'TRUSTED_DOMAINS'
]