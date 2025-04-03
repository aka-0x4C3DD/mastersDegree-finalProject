"""
WHO (World Health Organization) search provider using Selenium
"""
import logging
from urllib.parse import urljoin, quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import necessary functions from sibling modules
from ..utils import get_selenium_driver, clean_text
from ..config import get_search_settings, is_trusted_domain
# Import content extractor if needed for detailed content (currently not used for WHO)
# from ..content_extractor import get_detailed_content_selenium 

logger = logging.getLogger(__name__)

def search_who(query):
    """Search WHO website for global health news and information using Selenium"""
    settings = get_search_settings()
    base_url = "https://www.who.int"
    # Updated search URL structure
    search_url = f"{base_url}/home/search-results?indexCatalogue=genericsearchindex1&searchQuery={quote_plus(query)}&wordsMode=AnyWord"
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for WHO search.")
            return []
            
        logger.info(f"Navigating to WHO search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container using CSS Selector (adjust if needed)
        # Example: Look for a div that likely contains the results list
        results_container_selector = "div.results-list" # Placeholder - VERIFY THIS SELECTOR
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, results_container_selector)))
        logger.debug("WHO search results container located.")

        # Find result elements using CSS Selector (adjust if needed)
        # Example: Find list items or divs representing individual results within the container
        result_items_selector = f"{results_container_selector} div.result-item" # Placeholder - VERIFY THIS SELECTOR
        search_results_elements = driver.find_elements(By.CSS_SELECTOR, result_items_selector)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on WHO.")

        for item in search_results_elements:
            try:
                # Use relative CSS Selectors (adjust if needed)
                # Example: Find the first link within the item for the title
                title_elem_selector = "a.result-title" # Placeholder - VERIFY THIS SELECTOR
                # Example: Find a paragraph or div with a description class
                snippet_elem_selector = "p.result-description" # Placeholder - VERIFY THIS SELECTOR

                title_elem = item.find_element(By.CSS_SELECTOR, title_elem_selector)
                
                # Try to find snippet, fallback to title if not found
                try:
                    snippet_elem = item.find_element(By.CSS_SELECTOR, snippet_elem_selector)
                    snippet = clean_text(snippet_elem.text)
                except NoSuchElementException:
                    snippet = title_elem.text.strip() # Fallback

                title = title_elem.text.strip()
                link = title_elem.get_attribute('href')

                # Ensure link is absolute
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue

                content = snippet # No detailed content fetching for WHO currently

                if title and content:
                    results.append({
                        "source": link,
                        "title": title,
                        "content": content
                    })
                    logger.debug(f"Extracted WHO result: {title[:50]}...")
                else:
                     logger.warning("Found WHO result item but couldn't extract title/content.")

            except NoSuchElementException:
                logger.warning("Could not find expected elements (title/snippet) within a WHO result item using CSS selectors.")
            except Exception as e:
                logger.error(f"Error extracting single WHO result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"WHO Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"WHO search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during WHO Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for WHO search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during WHO search cleanup: {str(e)}")
                 
    return results
