"""
NIH search provider using Selenium
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

def search_nih(query):
    """Search NIH website for information using Selenium"""
    settings = get_search_settings()
    # NIH uses a specific search affiliate parameter
    search_url = f"https://search.nih.gov/search?utf8=%E2%9C%93&affiliate=nih&query={quote_plus(query)}"
    base_url = "https://www.nih.gov" # Needed for relative links if any
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver() # Get a new driver instance
        if not driver:
            logger.error("Selenium driver not available for NIH search.")
            return []
        
        # --- Core search logic using driver ---
        logger.info(f"Navigating to NIH search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container (adjust XPath if needed)
        results_container_xpath = "//div[@id='results-list']" 
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.XPATH, results_container_xpath)))
        logger.debug("NIH search results container located.")

        # Find result elements (adjust XPath if needed)
        result_items_xpath = f"{results_container_xpath}//div[contains(@class, 'result')]"
        search_results_elements = driver.find_elements(By.XPATH, result_items_xpath)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on NIH.")

        for item in search_results_elements:
            try:
                # Use relative XPath
                title_elem_xpath = ".//h3/a"
                snippet_elem_xpath = ".//div[contains(@class, 'search-results-excerpt')]"

                title_elem = item.find_element(By.XPATH, title_elem_xpath)
                snippet_elem = item.find_element(By.XPATH, snippet_elem_xpath)

                title = title_elem.text.strip()
                link = title_elem.get_attribute('href')

                # Ensure link is absolute (NIH links should be absolute)
                # if link and not link.startswith('http'):
                #     link = urljoin(base_url, link) # Usually not needed for NIH

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue

                snippet = clean_text(snippet_elem.text)
                content = snippet # No detailed content fetching

                if title and content:
                    results.append({
                        "source": link,
                        "title": title,
                        "content": content
                    })
                    logger.debug(f"Extracted NIH result: {title[:50]}...")
                else:
                     logger.warning("Found NIH result item but couldn't extract title/content.")

            except NoSuchElementException:
                logger.warning("Could not find expected elements (title/snippet) within an NIH result item.")
            except Exception as e:
                logger.error(f"Error extracting single NIH result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"NIH Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"NIH search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during NIH Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for NIH search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during NIH search cleanup: {str(e)}")
                 
    return results # Return results collected in the try block
