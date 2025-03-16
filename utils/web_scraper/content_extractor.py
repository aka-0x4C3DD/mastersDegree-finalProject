"""
Module for extracting detailed content from medical web pages
"""
import logging
import time
import random
import requests
from bs4 import BeautifulSoup

from .utils import get_common_headers, clean_text

logger = logging.getLogger(__name__)

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

def get_pubmed_abstract(article_id):
    """Fetch the abstract for a PubMed article"""
    try:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
        headers = get_common_headers()
        
        # Add a small delay to avoid overloading PubMed servers
        time.sleep(random.uniform(0.2, 0.7))
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for abstract section
            abstract_elem = soup.select_one('.abstract-content')
            if abstract_elem:
                # Remove "labels" that might be in the abstract (like "BACKGROUND:", "METHODS:", etc.)
                for label in abstract_elem.select('.abstract-label'):
                    label.extract()
                    
                abstract_text = abstract_elem.get_text(strip=True)
                return clean_text(abstract_text)
    
    except Exception as e:
        logger.error(f"Error fetching PubMed abstract for ID {article_id}: {str(e)}")
    
    return None
