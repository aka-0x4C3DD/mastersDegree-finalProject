"""
Mayo Clinic search provider
"""
import logging
import requests
from bs4 import BeautifulSoup

from ..utils import get_common_headers, clean_text
from ..config import get_search_settings
from ..content_extractor import get_detailed_content

logger = logging.getLogger(__name__)

def search_mayo_clinic(query):
    """Search Mayo Clinic website for information"""
    settings = get_search_settings()
    
    try:
        url = f"https://www.mayoclinic.org/search/search-results?q={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=settings['timeout_seconds'])
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.result')[:5]:
                try:
                    title_elem = result.select_one('h3 a')
                    snippet_elem = result.select_one('.result-description')
                    
                    if title_elem and snippet_elem:
                        title = title_elem.text.strip()
                        link = title_elem['href']
                        if not link.startswith('http'):
                            link = f"https://www.mayoclinic.org{link}"
                        snippet = clean_text(snippet_elem.text)
                        
                        # Try to get more comprehensive content by visiting the actual page
                        if settings['enable_detailed_content']:
                            detailed_content = get_detailed_content(link)
                            content = detailed_content if detailed_content else snippet
                        else:
                            content = snippet
                        
                        results.append({
                            "source": link,
                            "title": title,
                            "content": content
                        })
                except Exception as e:
                    logger.error(f"Error extracting Mayo Clinic result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during Mayo Clinic search: {str(e)}")
    
    return []
