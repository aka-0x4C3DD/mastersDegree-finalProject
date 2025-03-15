import requests
from bs4 import BeautifulSoup
import validators
import os
from urllib.parse import urlparse, urlencode
import logging
import configparser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load trusted domains from config.ini
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
TRUSTED_MEDICAL_DOMAINS = config['web_scraper']['trusted_domains'].split(', ')

def is_trusted_domain(url):
    """Check if a URL belongs to a trusted medical domain"""
    if not url or not validators.url(url):
        return False
    
    domain = urlparse(url).netloc.lower()
    
    # Check if the domain or its parent domain is in the trusted list
    return any(domain.endswith(trusted_domain) for trusted_domain in TRUSTED_MEDICAL_DOMAINS)

def search_medical_sites(query, max_results=3):
    """Search for information from trusted medical sites
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        A list of dictionaries containing source URLs and content snippets
    """
    results = []
    
    try:
        for domain in TRUSTED_MEDICAL_DOMAINS:
            base_url = f"https://{domain}/search"
            params = {'q': query}
            search_url = f"{base_url}?{urlencode(params)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Use domain-specific selectors if available
                domain_selectors = {
                    'cdc.gov': ('.searchResult-item', '.result-description'),
                    'mayoclinic.org': ('.search-result', '.result-description'),
                    'webmd.com': ('.search-result', '.result-snippet')
                }
                domain_key = domain.split('.')[0]
                selectors = domain_selectors.get(domain_key, ('.result-item', '.snippet'))
                
                results_section = soup.select(selectors[0])[:max_results]
                for result in results_section:
                    title_elem = result.select_one('h3 a')
                    snippet_elem = result.select_one(selectors[1])
                    
                    if title_elem and snippet_elem:
                        title = title_elem.text.strip()
                        link = title_elem['href']
                        snippet = snippet_elem.text.strip()
                        
                        if is_trusted_domain(link):
                            results.append({
                                "source": link,
                                "title": title,
                                "content": snippet
                            })
                            if len(results) >= max_results:
                                break
            if len(results) >= max_results:
                break
    except Exception as e:
        logger.error(f"Error during medical site search: {str(e)}")
        results.append({
            "source": "Error",
            "content": f"An error occurred while searching medical sites: {str(e)}"
        })
    finally:
        return results[:max_results]

if __name__ == "__main__":
    # Simple test
    query = "diabetes type 2 treatment"
    print(f"Searching for: {query}")
    results = search_medical_sites(query)
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Source: {result['source']}")
        if 'title' in result:
            print(f"Title: {result['title']}")
        print(f"Content: {result['content']}")
