"""
ClinicalGPT Medical Assistant - Web Scraping Package
This package handles searching and extracting information from trusted medical websites.
"""
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import main functions for easy access
from .core import search_medical_sites
from .config import load_trusted_domains_from_config, is_trusted_domain

# Export everything needed at package level
__all__ = ['search_medical_sites', 'load_trusted_domains_from_config', 'is_trusted_domain']
