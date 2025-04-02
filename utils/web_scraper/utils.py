"""
Common utility functions for web scraping
"""
import re
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager # Using webdriver-manager
from selenium.common.exceptions import WebDriverException
import shutil # Keep for potential future use like checking paths

logger = logging.getLogger(__name__)

# --- Existing functions ---
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

# --- Modified WebDriver Utility ---
def get_selenium_driver():
    """Initializes and returns a NEW Selenium WebDriver instance (Chrome)."""
    logger.info("Initializing new Selenium WebDriver (Chrome)...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run headless (no GUI)
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--log-level=3') # Suppress console logs from Chrome/ChromeDriver
    options.add_experimental_option('excludeSwitches', ['enable-logging']) # Suppress DevTools listening message
    # Set a common user agent
    options.add_argument(f'user-agent={get_common_headers()["User-Agent"]}') 

    try:
        # Use webdriver-manager to automatically handle driver download/update
        # Suppress webdriver-manager logs which can be verbose
        logging.getLogger('WDM').setLevel(logging.WARNING) 
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Selenium WebDriver initialized successfully for this thread/task.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Selenium WebDriver: {str(e)}")
        logger.error("Ensure Chrome is installed and accessible.")
        logger.error("Consider installing webdriver-manager: pip install webdriver-manager")
        return None
