import requests
from bs4 import BeautifulSoup
import validators
import os
from urllib.parse import urlparse
import json
import logging
import configparser
import time
import random
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Read trusted domains from config.ini
def load_trusted_domains_from_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
    
    if os.path.exists(config_path):
        try:
            config.read(config_path)
            if 'web_scraper' in config and 'trusted_domains' in config['web_scraper']:
                # Split by comma and strip whitespace
                domains = [domain.strip() for domain in config['web_scraper']['trusted_domains'].split(',')]
                logger.info(f"Loaded {len(domains)} trusted domains from config.ini")
                return domains
            else:
                logger.warning("Missing web_scraper section or trusted_domains key in config.ini")
        except Exception as e:
            logger.error(f"Error loading config.ini: {str(e)}")
    else:
        logger.warning(f"Config file not found at {config_path}")
    
    # Return a minimal fallback list if config loading fails
    logger.warning("Using minimal fallback list of trusted domains")
    return [
        'https://www.nih.gov',
        'https://www.cdc.gov',
        'https://www.mayoclinic.org',
    ]

# Load trusted domains
TRUSTED_DOMAINS = load_trusted_domains_from_config()

def is_trusted_domain(url):
    """Check if a URL belongs to a trusted medical domain"""
    if not url or not validators.url(url):
        return False
    
    # Convert URL to string if it's not already
    url_str = str(url)
    
    # Check if any trusted domain is in the URL
    return any(trusted_domain in url_str for trusted_domain in TRUSTED_DOMAINS)

def search_medical_sites(query, max_results=3):
    """Search for information from trusted medical sites with parallel requests
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        A list of dictionaries containing source URLs and content snippets
    """
    logger.info(f"Searching medical sites for: {query}")
    all_results = []
    
    # Define search functions to try
    search_functions = [
        search_nih, 
        search_cdc, 
        search_mayo_clinic, 
        search_webmd, 
        search_healthline,
        search_medical_news_today
    ]
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=len(search_functions)) as executor:
        # Submit all search tasks
        future_to_search = {
            executor.submit(search_func, query): search_func.__name__ 
            for search_func in search_functions
        }
        
        # Process results as they complete
        for future in future_to_search:
            search_name = future_to_search[future]
            try:
                results = future.result()
                if results:
                    logger.info(f"{search_name} returned {len(results)} results")
                    all_results.extend(results)
            except Exception as e:
                logger.error(f"Error in {search_name}: {str(e)}")
    
    # Sort results by content length (prioritize detailed information)
    all_results.sort(key=lambda x: len(x.get('content', '')), reverse=True)
    
    # Deduplicate results based on content similarity
    unique_results = []
    seen_content = set()
    
    for result in all_results:
        content_sample = result.get('content', '')[:100].lower()  # Take first 100 chars for comparison
        if content_sample not in seen_content:
            seen_content.add(content_sample)
            unique_results.append(result)
    
    logger.info(f"Total unique results found: {len(unique_results)}")
    return unique_results[:max_results]

def get_common_headers():
    """Get common headers for HTTP requests to avoid being blocked"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def clean_text(text):
    """Clean extracted text by removing extra spaces and newlines"""
    if not text:
        return ""
    # Replace multiple whitespace characters with a single space
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def search_nih(query):
    """Search NIH website for information"""
    try:
        url = f"https://search.nih.gov/search?utf8=%E2%9C%93&affiliate=nih&query={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.result')[:5]:
                try:
                    title_elem = result.select_one('h3 a')
                    snippet_elem = result.select_one('.search-results-excerpt')
                    
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
                    logger.error(f"Error extracting NIH result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during NIH search: {str(e)}")
    
    return []

def search_cdc(query):
    """Search CDC website for information"""
    try:
        url = f"https://search.cdc.gov/search/?query={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=10)
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

def search_mayo_clinic(query):
    """Search Mayo Clinic website for information"""
    try:
        url = f"https://www.mayoclinic.org/search/search-results?q={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=10)
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
                        detailed_content = get_detailed_content(link)
                        content = detailed_content if detailed_content else snippet
                        
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

def search_webmd(query):
    """Search WebMD for medical information"""
    try:
        url = f"https://www.webmd.com/search/search_results/default.aspx?query={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=10)
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

def search_healthline(query):
    """Search Healthline for medical information"""
    try:
        url = f"https://www.healthline.com/search?q1={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=10)
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
                    
                    # Get detailed content from the article page
                    detailed_content = get_detailed_content(link)
                    
                    if detailed_content:
                        results.append({
                            "source": link,
                            "title": title,
                            "content": detailed_content
                        })
                except Exception as e:
                    logger.error(f"Error extracting Healthline result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during Healthline search: {str(e)}")
    
    return []

def search_medical_news_today(query):
    """Search Medical News Today for medical information"""
    try:
        url = f"https://www.medicalnewstoday.com/search?q={query}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=10)
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
                        
                        # Get detailed content from the article page
                        detailed_content = get_detailed_content(link)
                        
                        if detailed_content:
                            results.append({
                                "source": link,
                                "title": title,
                                "content": detailed_content
                            })
                except Exception as e:
                    logger.error(f"Error extracting Medical News Today result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during Medical News Today search: {str(e)}")
    
    return []

def get_detailed_content(url, max_length=1000):
    """Visit a specific page and extract more detailed content"""
    try:
        # Add a small delay to avoid overloading servers
        time.sleep(random.uniform(0.1, 0.5))
        
        headers = get_common_headers()
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.extract()
            
            # Look for article content in common containers
            content_selectors = [
                'article', '.article-body', '.content-body', '.article-content',
                '.entry-content', 'main', '.main-content', '.post-content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    paragraphs = content_elem.find_all('p')
                    text = ' '.join(p.text for p in paragraphs[:10])  # Take first 10 paragraphs
                    content = clean_text(text)
                    break
            
            if not content:
                # Fallback: just take all paragraph content from the page
                paragraphs = soup.find_all('p')
                text = ' '.join(p.text for p in paragraphs[:10])
                content = clean_text(text)
            
            # Limit content length
            if content and len(content) > max_length:
                content = content[:max_length] + "..."
            
            return content
    
    except Exception as e:
        logger.error(f"Error getting detailed content from {url}: {str(e)}")
    
    return None

if __name__ == "__main__":
    # Simple test
    query = "latest treatments for type 2 diabetes"
    print(f"Searching for: {query}")
    results = search_medical_sites(query, max_results=3)
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Source: {result['source']}")
        if 'title' in result:
            print(f"Title: {result['title']}")
        print(f"Content: {result.get('content', '')[:100]}...")