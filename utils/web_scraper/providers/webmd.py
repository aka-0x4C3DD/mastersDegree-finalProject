"""
WebMD search provider
"""
import logging
import requests
from bs4 import BeautifulSoup

from ..utils import get_common_headers, clean_text
from ..config import get_search_settings

logger = logging.getLogger(__name__)

def search_webmd(query):
    """Search WebMD for medical information"""
    settings = get_search_settings()
    
    try:
        url = f"https://www.webmd.com/search/search_results/default.aspx?query={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=settings['timeout_seconds'])
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.search-results-doc-container')[:5]:
                try:
                    title_elem = result.select_one('a')
                    snippet_elem = result.select_one('.search-results-doc-description')
                    
                    if title_elem and snippet_elem:
                        title = title_elem.text.strip()
                        link = title_elem['href']
                        if not link.startswith('http'):
                            link = f"https://www.webmd.com{link}"
                        snippet = clean_text(snippet_elem.text)
                        
                        results.append({
                            "source": link,
                            "title": title,
                            "content": snippet
                        })
                except Exception as e:
                    logger.error(f"Error extracting WebMD result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during WebMD search: {str(e)}")
    
    return []
