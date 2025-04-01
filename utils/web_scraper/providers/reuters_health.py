"""
Reuters Health News search provider
"""
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus

from ..utils import get_common_headers, clean_text
from ..config import get_search_settings, is_trusted_domain
from ..content_extractor import get_detailed_content

logger = logging.getLogger(__name__)

def search_reuters_health(query):
    """Search Reuters Health News for information"""
    settings = get_search_settings()
    base_url = "https://www.reuters.com"
    # Using the general search and hoping health news appears prominently
    search_url = f"{base_url}/search/news?blob={quote_plus(query)}&sortBy=date&dateRange=all" 
    
    try:
        headers = get_common_headers()
        response = requests.get(search_url, headers=headers, timeout=settings['timeout_seconds'])
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results (Selectors based on inspecting Reuters search results page)
            # Results seem to be within 'div.search-result-indiv'
            for result in soup.select('div.search-result-indiv')[:5]: 
                try:
                    title_elem = result.select_one('h3.search-result-title a')
                    snippet_elem = result.select_one('p.search-result-excerpt')
                    
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.get('href')
                        
                        # Ensure the link is absolute
                        if link and not link.startswith('http'):
                            link = urljoin(base_url, link)
                        
                        # Validate domain
                        if not is_trusted_domain(link):
                            continue

                        # Get snippet or fallback to title
                        snippet = clean_text(snippet_elem.text) if snippet_elem else title
                        
                        # Try to get more detailed content if enabled
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
                    logger.error(f"Error extracting Reuters result: {str(e)}")
            
            logger.info(f"Reuters Health search returned {len(results)} results.")
            return results
        else:
            logger.warning(f"Reuters Health search failed with status code: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error during Reuters Health search: {str(e)}")
    
    return []