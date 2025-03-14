import requests
from bs4 import BeautifulSoup
import validators
import os
from urllib.parse import urlparse
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of trusted medical domains
# This list can be expanded or loaded from a configuration file
TRUSTED_MEDICAL_DOMAINS = [
    'nih.gov',
    'who.int',
    'mayoclinic.org',
    'medlineplus.gov',
    'cdc.gov',
    'health.harvard.edu',
    'hopkinsmedicine.org',
    'clevelandclinic.org',
    'webmd.com',
    'medicalnewstoday.com',
    'nejm.org',
    'bmj.com',
    'jamanetwork.com',
    'thelancet.com',
    'pubmed.ncbi.nlm.nih.gov',
    'healthline.com',
    'medscape.com',
]

# Path to save the trusted domains file
TRUSTED_DOMAINS_FILE = os.path.join(os.path.dirname(__file__), 'trusted_domains.json')

def is_trusted_domain(url):
    """Check if a URL belongs to a trusted medical domain"""
    if not url or not validators.url(url):
        return False
    
    domain = urlparse(url).netloc.lower()
    
    # Check if the domain or its parent domain is in the trusted list
    return any(domain.endswith(trusted_domain) for trusted_domain in TRUSTED_MEDICAL_DOMAINS)

def load_trusted_domains():
    """Load trusted domains from file if it exists"""
    global TRUSTED_MEDICAL_DOMAINS
    
    if os.path.exists(TRUSTED_DOMAINS_FILE):
        try:
            with open(TRUSTED_DOMAINS_FILE, 'r') as f:
                domains = json.load(f)
                if isinstance(domains, list) and all(isinstance(d, str) for d in domains):
                    TRUSTED_MEDICAL_DOMAINS = domains
                    logger.info(f"Loaded {len(domains)} trusted domains from file")
        except Exception as e:
            logger.error(f"Error loading trusted domains: {str(e)}")

def save_trusted_domains():
    """Save the current trusted domains list to file"""
    try:
        os.makedirs(os.path.dirname(TRUSTED_DOMAINS_FILE), exist_ok=True)
        with open(TRUSTED_DOMAINS_FILE, 'w') as f:
            json.dump(TRUSTED_MEDICAL_DOMAINS, f, indent=2)
        logger.info(f"Saved {len(TRUSTED_MEDICAL_DOMAINS)} trusted domains to file")
    except Exception as e:
        logger.error(f"Error saving trusted domains: {str(e)}")

def search_medical_sites(query, max_results=3):
    """Search for information from trusted medical sites
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        A list of dictionaries containing source URLs and content snippets
    """
    # Load trusted domains
    load_trusted_domains()
    
    results = []
    
    try:
        # Use a search API or perform a web search
        # For this example, we'll use a simplified approach by directly searching
        # some known medical websites
        
        # NIH search
        nih_results = search_nih(query)
        if nih_results:
            results.extend(nih_results[:max_results])
        
        # CDC search if we need more results
        if len(results) < max_results:
            cdc_results = search_cdc(query)
            if cdc_results:
                results.extend(cdc_results[:max_results - len(results)])
        
        # Mayo Clinic search if we still need more results
        if len(results) < max_results:
            mayo_results = search_mayo_clinic(query)
            if mayo_results:
                results.extend(mayo_results[:max_results - len(results)])
    
    except Exception as e:
        logger.error(f"Error during medical site search: {str(e)}")
        results.append({
            "source": "Error",
            "content": f"An error occurred while searching medical sites: {str(e)}"
        })
    
    return results

def search_nih(query):
    """Search NIH website for information"""
    try:
        url = f"https://search.nih.gov/search?utf8=%E2%9C%93&affiliate=nih&query={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.search-result')[:3]:
                title_elem = result.select_one('h3 a')
                snippet_elem = result.select_one('.search-result-snippet')
                
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
            
            return results
    except Exception as e:
        logger.error(f"Error during NIH search: {str(e)}")
    
    return []

def search_cdc(query):
    """Search CDC website for information"""
    try:
        url = f"https://search.cdc.gov/search/?query={query}&sitelimit=www.cdc.gov"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.searchResults .item')[:3]:
                title_elem = result.select_one('a')
                snippet_elem = result.select_one('.description')
                
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
            
            return results
    except Exception as e:
        logger.error(f"Error during CDC search: {str(e)}")
    
    return []

def search_mayo_clinic(query):
    """Search Mayo Clinic website for information"""
    try:
        url = f"https://www.mayoclinic.org/search/search-results?q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.result')[:3]:
                title_elem = result.select_one('h3 a')
                snippet_elem = result.select_one('.result-description')
                
                if title_elem and snippet_elem:
                    title = title_elem.text.strip()
                    link = title_elem['href']
                    if not link.startswith('http'):
                        link = f"https://www.mayoclinic.org{link}"
                    snippet = snippet_elem.text.strip()
                    
                    if is_trusted_domain(link):
                        results.append({
                            "source": link,
                            "title": title,
                            "content": snippet
                        })
            
            return results
    except Exception as e:
        logger.error(f"Error during Mayo Clinic search: {str(e)}")
    
    return []

def add_trusted_domain(domain):
    """Add a new trusted domain to the list"""
    if domain and domain not in TRUSTED_MEDICAL_DOMAINS:
        TRUSTED_MEDICAL_DOMAINS.append(domain)
        save_trusted_domains()
        return True
    return False

def remove_trusted_domain(domain):
    """Remove a domain from the trusted list"""
    if domain in TRUSTED_MEDICAL_DOMAINS:
        TRUSTED_MEDICAL_DOMAINS.remove(domain)
        save_trusted_domains()
        return True
    return False

# Initialize by loading trusted domains
load_trusted_domains()

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