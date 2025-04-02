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
    search_url = f"https://www.webmd.com/search/search_results/default.aspx?query={quote_plus(query)}"
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

        # Wait for search results container (adjust XPath if needed)
        results_container_xpath = "//div[contains(@class, 'search-results-container-wrapper')]"
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.XPATH, results_container_xpath)))
        logger.debug("WebMD search results container located.")

        # Find result elements (adjust XPath if needed)
        result_items_xpath = f"{results_container_xpath}//div[contains(@class, 'search-results-doc-container')]"
        search_results_elements = driver.find_elements(By.XPATH, result_items_xpath)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on WebMD.")

        for item in search_results_elements:
            try:
                # Use relative XPath
                title_elem_xpath = ".//a[contains(@class, 'search-results-doc-title-link')]"
                snippet_elem_xpath = ".//p[contains(@class, 'search-results-doc-description')]"

                title_elem = item.find_element(By.XPATH, title_elem_xpath)
                snippet_elem = item.find_element(By.XPATH, snippet_elem_xpath)

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
                logger.warning("Could not find expected elements (title/snippet) within a WebMD result item.")
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
