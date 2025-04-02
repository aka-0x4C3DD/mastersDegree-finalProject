"""
Mayo Clinic search provider using Selenium
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

def search_mayo_clinic(query):
    """Search Mayo Clinic website for information using Selenium"""
    settings = get_search_settings()
    search_url = f"https://www.mayoclinic.org/search/search-results?q={quote_plus(query)}"
    base_url = "https://www.mayoclinic.org"
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for Mayo Clinic search.")
            return []
            
        logger.info(f"Navigating to Mayo Clinic search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container (adjust XPath if needed)
        results_container_xpath = "//div[@id='main-content']//ol[contains(@class, 'search-results')]"
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.XPATH, results_container_xpath)))
        logger.debug("Mayo Clinic search results container located.")

        # Find result elements (adjust XPath if needed)
        result_items_xpath = f"{results_container_xpath}/li[contains(@class, 'result')]"
        search_results_elements = driver.find_elements(By.XPATH, result_items_xpath)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on Mayo Clinic.")

        for item in search_results_elements:
            try:
                # Use relative XPath
                title_elem_xpath = ".//h3/a"
                snippet_elem_xpath = ".//div[contains(@class, 'result-description')]"

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
                
                # Try to get more comprehensive content by visiting the actual page if enabled
                if settings['enable_detailed_content']:
                    # Pass the existing driver to avoid creating a new one
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
                    logger.debug(f"Extracted Mayo Clinic result: {title[:50]}...")
                else:
                     logger.warning("Found Mayo Clinic result item but couldn't extract title/content.")

            except NoSuchElementException:
                logger.warning("Could not find expected elements (title/snippet) within a Mayo Clinic result item.")
            except Exception as e:
                logger.error(f"Error extracting single Mayo Clinic result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"Mayo Clinic Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"Mayo Clinic search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during Mayo Clinic Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for Mayo Clinic search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during Mayo Clinic search cleanup: {str(e)}")
                 
    return results
