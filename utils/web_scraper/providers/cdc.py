"""
CDC (Centers for Disease Control and Prevention) search provider
"""
import logging
import requests
from bs4 import BeautifulSoup

from ..utils import get_common_headers, clean_text
from ..config import is_trusted_domain, get_search_settings

logger = logging.getLogger(__name__)

def search_cdc(query):
    """Search CDC website for information"""
    settings = get_search_settings()
    
    try:
        url = f"https://search.cdc.gov/search/?query={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=settings['timeout_seconds'])
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.searchResultsList li')[:5]:
                try:
                    title_elem = result.select_one('h3 a')
                    snippet_elem = result.select_one('.searchResultDescription')
                    
                    if title_elem and snippet_elem:
                        title = title_elem.text.strip()
                        link = title_elem['href']
                        snippet = clean_text(snippet_elem.text)
                        
                        if is_trusted_domain(link):
                            results.append({
                                "source": link,
                                "title": title,
                                "content": snippet
                            })
                except Exception as e:
                    logger.error(f"Error extracting CDC result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during CDC search: {str(e)}")
    
    return []
