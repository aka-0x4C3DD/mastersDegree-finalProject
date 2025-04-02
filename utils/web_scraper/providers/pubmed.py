"""
PubMed search provider for medical research
"""
import logging
import requests
from bs4 import BeautifulSoup

from ..utils import get_common_headers, clean_text
from ..config import get_search_settings
from ..content_extractor import get_pubmed_abstract

logger = logging.getLogger(__name__)

def search_pubmed(query):
    """Search PubMed for medical research papers and information"""
    settings = get_search_settings()
    
    try:
        url = f"https://pubmed.ncbi.nlm.nih.gov/?term={query.replace(' ', '+')}"
        headers = get_common_headers()
        
        response = requests.get(url, headers=headers, timeout=15)  # Longer timeout for PubMed
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.select('.docsum-content')[:5]:
                try:
                    title_elem = result.select_one('.docsum-title')
                    article_id = result.get('data-article-id')
                    
                    if title_elem and article_id:
                        title = title_elem.text.strip()
                        link = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
                        
                        # Try to extract authors and journal info if available
                        authors = result.select_one('.docsum-authors')
                        journal = result.select_one('.docsum-journal-citation')
                        snippet = ""
                        
                        if authors:
                            snippet += authors.text.strip() + ". "
                        if journal:
                            snippet += journal.text.strip()
                        
                        # If we have article ID and detailed content is enabled, try to get abstract
                        if settings['enable_detailed_content']:
                            detailed_content = get_pubmed_abstract(article_id)
                            content = detailed_content if detailed_content else snippet
                        else:
                            content = snippet
                        
                        results.append({
                            "source": link,
                            "title": title,
                            "content": content
                        })
                except Exception as e:
                    logger.error(f"Error extracting PubMed result: {str(e)}")
            
            return results
    except Exception as e:
        logger.error(f"Error during PubMed search: {str(e)}")
    
    return []
