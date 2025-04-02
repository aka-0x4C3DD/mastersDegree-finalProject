"""
Medical News Today search provider
"""
import logging
import requests
from bs4 import BeautifulSoup

from ..utils import get_common_headers
from ..config import get_search_settings
from ..content_extractor import get_detailed_content

logger = logging.getLogger(__name__)

def search_medical_news_today(query):
    """Search Medical News Today for medical information"""
    settings = get_search_settings()
    
    try:
        url = f"https://www.medicalnewstoday.com/search?q={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=settings['timeout_seconds'])
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('a.css-ni2lnp')[:5]:
                try:
                    title_elem = result.select_one('span.css-u1w2sb')
                    
                    if title_elem:
                        title = title_elem.text.strip()
                        link = result['href']
                        if not link.startswith('http'):
                            link = f"https://www.medicalnewstoday.com{link}"
                        
                        # Get detailed content from the article page if enabled
                        if settings['enable_detailed_content']:
                            detailed_content = get_detailed_content(link)
                            if detailed_content:
                                results.append({
                                    "source": link,
                                    "title": title,
                                    "content": detailed_content
                                })
                        else:
                            # Use just the title if we're not getting detailed content
                            results.append({
                                "source": link,
                                "title": title,
                                "content": title
                            })
                except Exception as e:
                    logger.error(f"Error extracting Medical News Today result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during Medical News Today search: {str(e)}")
    
    return []
