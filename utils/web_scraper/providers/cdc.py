"""
CDC search provider using Selenium
"""
import logging
from urllib.parse import urljoin, quote_plus # Keep urljoin for potential relative links
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils import get_selenium_driver, clean_text
from ..config import get_search_settings, is_trusted_domain

logger = logging.getLogger(__name__)

def search_cdc(query):
    """Search CDC website for information using Selenium"""
    settings = get_search_settings()
    # Use the standard search URL structure
    search_url = f"https://search.cdc.gov/search/?query={quote_plus(query)}"
    base_url = "https://www.cdc.gov" # Base URL for resolving relative links if needed
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for CDC search.")
            return []
            
        logger.info(f"Navigating to CDC search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container using CSS Selector (adjust if needed)
        # Example: Look for a ul with class 'searchResultsList'
        results_container_selector = "ul.searchResultsList" # Placeholder - VERIFY THIS SELECTOR
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, results_container_selector)))
        logger.debug("CDC search results container located.")

        # Find result elements using CSS Selector (adjust if needed)
        # Example: Find list items within the container
        result_items_selector = f"{results_container_selector} > li" # Placeholder - VERIFY THIS SELECTOR
        search_results_elements = driver.find_elements(By.CSS_SELECTOR, result_items_selector)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on CDC.")

        for item in search_results_elements:
            try:
                # Use relative CSS Selectors (adjust if needed)
                # Example: Find the first link within an h3 tag
                title_elem_selector = "h3 > a" # Placeholder - VERIFY THIS SELECTOR
                # Example: Find a div with class 'searchResultDescription'
                snippet_elem_selector = "div.searchResultDescription" # Placeholder - VERIFY THIS SELECTOR

                title_elem = item.find_element(By.CSS_SELECTOR, title_elem_selector)
                snippet_elem = item.find_element(By.CSS_SELECTOR, snippet_elem_selector)

                title = title_elem.text.strip()
                link = title_elem.get_attribute('href')

                # Ensure link is absolute (CDC links might be relative)
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue

                snippet = clean_text(snippet_elem.text)
                content = snippet # No detailed content fetching for CDC currently

                if title and content:
                    results.append({
                        "source": link,
                        "title": title,
                        "content": content
                    })
                    logger.debug(f"Extracted CDC result: {title[:50]}...")
                else:
                     logger.warning("Found CDC result item but couldn't extract title/content.")

            except NoSuchElementException:
                logger.warning("Could not find expected elements (title/snippet) within a CDC result item using CSS selectors.")
            except Exception as e:
                logger.error(f"Error extracting single CDC result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"CDC Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"CDC search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during CDC Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for CDC search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during CDC search cleanup: {str(e)}")
                 
    return results
