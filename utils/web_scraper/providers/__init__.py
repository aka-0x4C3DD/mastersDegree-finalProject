"""
Search providers for medical information
"""

from .nih import search_nih
from .cdc import search_cdc
from .mayo_clinic import search_mayo_clinic
from .webmd import search_webmd
from .healthline import search_healthline
from .medical_news_today import search_medical_news_today
from .pubmed import search_pubmed

# All search providers that will be used
SEARCH_PROVIDERS = [
    search_nih,
    search_cdc, 
    search_mayo_clinic,
    search_webmd,
    search_healthline,
    search_medical_news_today,
    search_pubmed
]

__all__ = [
    'search_nih',
    'search_cdc',
    'search_mayo_clinic',
    'search_webmd',
    'search_healthline',
    'search_medical_news_today',
    'search_pubmed',
    'SEARCH_PROVIDERS'
]
