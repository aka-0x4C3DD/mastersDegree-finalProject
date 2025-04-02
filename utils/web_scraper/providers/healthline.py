"""
Healthline search provider
"""
import logging
import requests
from bs4 import BeautifulSoup

from ..utils import get_common_headers
from ..config import get_search_settings
from ..content_extractor import get_detailed_content

logger = logging.getLogger(__name__)

def search_healthline(query):
    """Search Healthline for medical information"""
    settings = get_search_settings()
    
    try:
        url = f"https://www.healthline.com/search?q1={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=settings['timeout_seconds'])
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('a.css-1qhn6m6')[:5]:
                try:
                    title = result.text.strip()
                    link = result['href']
                    if not link.startswith('http'):
                        link = f"https://www.healthline.com{link}"
                    
                    # Get detailed content only if enabled
                    if settings['enable_detailed_content']:
                        detailed_content = get_detailed_content(link)
                        if detailed_content:
                            results.append({
                                "source": link,
                                "title": title,
                                "content": detailed_content
                            })
                    else:
                        # Use just the title as we don't have a snippet directly
                        results.append({
                            "source": link,
                            "title": title,
                            "content": title
                        })
                except Exception as e:
                    logger.error(f"Error extracting Healthline result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during Healthline search: {str(e)}")
    
    return []
