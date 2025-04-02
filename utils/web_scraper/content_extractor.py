"""
Module for extracting detailed content from medical web pages
"""
import logging
import time
import random
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .utils import get_common_headers, clean_text

logger = logging.getLogger(__name__)

def get_detailed_content(url, max_length=1000):
    """Visit a specific page using Requests and extract more detailed content"""
    try:
        # Add a small delay to avoid overloading servers
        time.sleep(random.uniform(0.1, 0.5))
        
        headers = get_common_headers()
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return extract_content_from_soup(soup, max_length)
    
    except Exception as e:
        logger.error(f"Error getting detailed content from {url} using Requests: {str(e)}")
    
    return None

def get_detailed_content_selenium(url, driver, max_length=1000):
    """Visit a specific page using Selenium and extract more detailed content"""
    try:
        # Add a small delay to avoid overloading servers
        time.sleep(random.uniform(0.1, 0.5))
        
        logger.debug(f"Navigating to article page: {url}")
        driver.get(url)
        
        # Use driver's page source to create BeautifulSoup object
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return extract_content_from_soup(soup, max_length)
        
    except Exception as e:
        logger.error(f"Error getting detailed content from {url} using Selenium: {str(e)}")
    
    return None

def extract_content_from_soup(soup, max_length=1000):
    """Extracts main content from a BeautifulSoup object"""
    # Remove script, style elements
    for script in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        script.extract()
    
    # Look for article content in common containers
    content_selectors = [
        'article', '.article-body', '.content-body', '.article-content',
        '.entry-content', 'main', '.main-content', '.post-content', 
        '.story-content', '.body-content' # Added more common selectors
    ]
    
    content = ""
    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            paragraphs = content_elem.find_all('p', recursive=False) # Find direct children first
            if not paragraphs:
                 paragraphs = content_elem.find_all('p') # Fallback to all paragraphs

            text = ' '.join(p.text for p in paragraphs[:15])  # Take first 15 paragraphs
            content = clean_text(text)
            if len(content) > 200: # Check if we got substantial content
                break
    
    if not content or len(content) < 200:
        # Fallback: just take all paragraph content from the page body
        paragraphs = soup.find('body').find_all('p') if soup.find('body') else []
        text = ' '.join(p.text for p in paragraphs[:15])
        content = clean_text(text)
    
    # Limit content length
    if content and len(content) > max_length:
        content = content[:max_length] + "..."
    
    return content if content else None

def get_pubmed_abstract(article_id):
    """Fetch the abstract for a PubMed article using Requests"""
    try:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{article_id}/"
        headers = get_common_headers()
        
        # Add a small delay to avoid overloading PubMed servers
        time.sleep(random.uniform(0.2, 0.7))
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return extract_pubmed_abstract_from_soup(soup)
    
    except Exception as e:
        logger.error(f"Error fetching PubMed abstract for ID {article_id} using Requests: {str(e)}")
    
    return None

def get_pubmed_abstract_selenium(url, driver):
    """Fetch the abstract for a PubMed article using Selenium"""
    try:
        # Add a small delay
        time.sleep(random.uniform(0.2, 0.7))
        
        logger.debug(f"Navigating to PubMed article page: {url}")
        driver.get(url)
        
        # Use driver's page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return extract_pubmed_abstract_from_soup(soup)
        
    except Exception as e:
        logger.error(f"Error fetching PubMed abstract from {url} using Selenium: {str(e)}")
    
    return None

def extract_pubmed_abstract_from_soup(soup):
    """Extracts abstract from a PubMed BeautifulSoup object"""
    # Look for abstract section
    abstract_elem = soup.select_one('.abstract-content')
    if abstract_elem:
        # Remove "labels" that might be in the abstract (like "BACKGROUND:", "METHODS:", etc.)
        for label in abstract_elem.select('.abstract-label'):
            label.extract()
            
        abstract_text = abstract_elem.get_text(strip=True)
        return clean_text(abstract_text)
    return None
