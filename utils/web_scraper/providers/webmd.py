"""
WebMD search provider using Selenium
"""
import logging
from urllib.parse import urljoin, quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils import get_selenium_driver, clean_text
from ..config import get_search_settings, is_trusted_domain

logger = logging.getLogger(__name__)

def search_webmd(query):
    """Search WebMD for medical information using Selenium"""
    settings = get_search_settings()
    # Updated WebMD search URL structure
    search_url = f"https://www.webmd.com/search?query={quote_plus(query)}"
    base_url = "https://www.webmd.com"
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for WebMD search.")
            return []
            
        logger.info(f"Navigating to WebMD search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container using CSS Selector (adjust if needed)
        # Example: Look for a div with class 'search-results-container-wrapper'
        results_container_selector = "div.search-results-container-wrapper" # Placeholder - VERIFY THIS SELECTOR
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, results_container_selector)))
        logger.debug("WebMD search results container located.")

        # Find result elements using CSS Selector (adjust if needed)
        # Example: Find divs with class 'search-results-doc-container'
        result_items_selector = f"{results_container_selector} div.search-results-doc-container" # Placeholder - VERIFY THIS SELECTOR
        search_results_elements = driver.find_elements(By.CSS_SELECTOR, result_items_selector)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on WebMD.")

        for item in search_results_elements:
            try:
                # Use relative CSS Selectors (adjust if needed)
                # Example: Find link with class 'search-results-doc-title-link'
                title_elem_selector = "a.search-results-doc-title-link" # Placeholder - VERIFY THIS SELECTOR
                # Example: Find paragraph with class 'search-results-doc-description'
                snippet_elem_selector = "p.search-results-doc-description" # Placeholder - VERIFY THIS SELECTOR

                title_elem = item.find_element(By.CSS_SELECTOR, title_elem_selector)
                snippet_elem = item.find_element(By.CSS_SELECTOR, snippet_elem_selector)

                title = title_elem.text.strip()
                link = title_elem.get_attribute('href')

                # Ensure link is absolute
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue

                snippet = clean_text(snippet_elem.text)
                content = snippet # No detailed content fetching for WebMD currently

                if title and content:
                    results.append({
                        "source": link,
                        "title": title,
                        "content": content
                    })
                    logger.debug(f"Extracted WebMD result: {title[:50]}...")
                else:
                     logger.warning("Found WebMD result item but couldn't extract title/content.")

            except NoSuchElementException:
                logger.warning("Could not find expected elements (title/snippet) within a WebMD result item using CSS selectors.")
            except Exception as e:
                logger.error(f"Error extracting single WebMD result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"WebMD Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"WebMD search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during WebMD Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for WebMD search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during WebMD search cleanup: {str(e)}")
                 
    return results
