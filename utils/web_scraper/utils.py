"""
Common utility functions for web scraping
"""
import re
import random
import logging

logger = logging.getLogger(__name__)

def get_common_headers():
    """Get common headers for HTTP requests to avoid being blocked"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'DNT': '1',  # Do Not Track
        'Upgrade-Insecure-Requests': '1',
    }

def clean_text(text):
    """Clean extracted text by removing extra spaces and newlines"""
    if not text:
        return ""
    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def sanitize_query(query):
    """Sanitize a search query to make it safe for URLs"""
    # Replace special characters with spaces
    sanitized = re.sub(r'[^\w\s]', ' ', query)
    # Replace multiple spaces with a single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    # Trim and encode the query
    return sanitized.strip()
