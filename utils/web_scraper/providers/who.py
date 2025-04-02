"""
WHO (World Health Organization) search provider
"""
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..utils import get_common_headers, clean_text
from ..config import get_search_settings, is_trusted_domain

logger = logging.getLogger(__name__)

def search_who(query):
    """Search WHO website for global health news and information"""
    settings = get_search_settings()
    base_url = "https://www.who.int"
    
    try:
        # WHO uses a specific search endpoint
        search_url = f"{base_url}/search?query={query}"
        headers = get_common_headers()
        
        response = requests.get(search_url, headers=headers, timeout=settings['timeout_seconds'])
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results (Selector might need adjustment based on WHO website structure)
            # Inspecting the WHO search results page, results seem to be within '.sf-search-results__item'
            for result in soup.select('.sf-search-results__item')[:5]: 
                try:
                    title_elem = result.select_one('.sf-search-results__title a')
                    snippet_elem = result.select_one('.sf-search-results__description')
                    
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.get('href')
                        # Ensure the link is absolute
                        if link and not link.startswith('http'):
                            link = urljoin(base_url, link)
                        
                        snippet = clean_text(snippet_elem.text) if snippet_elem else title # Fallback to title if no snippet
                        
                        # Validate domain just in case
                        if is_trusted_domain(link):
                            results.append({
                                "source": link,
                                "title": title,
                                "content": snippet
                            })
                except Exception as e:
                    logger.error(f"Error extracting WHO result: {str(e)}")
            
            logger.info(f"WHO search returned {len(results)} results.")
            return results
        else:
            logger.warning(f"WHO search failed with status code: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error during WHO search: {str(e)}")
    
    return []
