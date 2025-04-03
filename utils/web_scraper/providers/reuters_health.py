"""
Reuters Health News search provider using Selenium
"""
import logging
from urllib.parse import urljoin, quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils import get_selenium_driver, clean_text
from ..config import get_search_settings, is_trusted_domain
from ..content_extractor import get_detailed_content_selenium # Use Selenium version

logger = logging.getLogger(__name__)

def search_reuters_health(query):
    """Search Reuters Health for medical news using Selenium"""
    settings = get_search_settings()
    # Updated Reuters search URL structure
    search_url = f"https://www.reuters.com/site-search/?query={quote_plus(query)}"
    base_url = "https://www.reuters.com"
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for Reuters Health search.")
            return []
            
        logger.info(f"Navigating to Reuters Health search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container using CSS Selector (adjust if needed)
        # Example: Look for a div with a class containing 'search-results'
        results_container_selector = "div[class*='search-results']" # Placeholder - VERIFY THIS SELECTOR
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, results_container_selector)))
        logger.debug("Reuters Health search results container located.")

        # Find result elements using CSS Selector (adjust if needed)
        # Example: Find divs with a class containing 'search-result'
        result_items_selector = f"{results_container_selector} div[class*='search-result']" # Placeholder - VERIFY THIS SELECTOR
        search_results_elements = driver.find_elements(By.CSS_SELECTOR, result_items_selector)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on Reuters Health.")

        for item in search_results_elements:
            try:
                # Use relative CSS Selectors (adjust if needed)
                # Example: Find the first link within an h3 tag
                title_elem_selector = "h3 > a" # Placeholder - VERIFY THIS SELECTOR
                # Example: Find the first paragraph for the snippet
                snippet_elem_selector = "p" # Placeholder - VERIFY THIS SELECTOR (might be too generic)

                title_elem = item.find_element(By.CSS_SELECTOR, title_elem_selector)
                
                title = title_elem.text.strip()
                link = title_elem.get_attribute('href')

                # Ensure link is absolute
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue
                
                # Try to get snippet
                try:
                    snippet_elem = item.find_element(By.CSS_SELECTOR, snippet_elem_selector)
                    snippet = clean_text(snippet_elem.text)
                except NoSuchElementException:
                    snippet = title # Fallback if no snippet found

                # Get detailed content only if enabled
                if settings['enable_detailed_content']:
                    detailed_content = get_detailed_content_selenium(link, driver)
                    content = detailed_content if detailed_content else snippet
                else:
                    content = snippet
                
                if title and content:
                    results.append({
                        "source": link,
                        "title": title,
                        "content": content
                    })
                    logger.debug(f"Extracted Reuters Health result: {title[:50]}...")
                else:
                     logger.warning("Found Reuters Health result item but couldn't extract title/content.")

            except NoSuchElementException:
                logger.warning("Could not find expected elements (title/snippet) within a Reuters Health result item using CSS selectors.")
            except Exception as e:
                logger.error(f"Error extracting single Reuters Health result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"Reuters Health Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"Reuters Health search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during Reuters Health Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for Reuters Health search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during Reuters Health search cleanup: {str(e)}")
                 
    return results