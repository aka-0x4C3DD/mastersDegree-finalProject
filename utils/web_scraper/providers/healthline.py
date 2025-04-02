"""
Healthline search provider using Selenium
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

def search_healthline(query):
    """Search Healthline for medical information using Selenium"""
    settings = get_search_settings()
    search_url = f"https://www.healthline.com/search?q1={quote_plus(query)}"
    base_url = "https://www.healthline.com"
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for Healthline search.")
            return []
            
        logger.info(f"Navigating to Healthline search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container (adjust XPath if needed)
        results_container_xpath = "//div[contains(@class, 'css-1t10xxp')]" # Example, might change
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.XPATH, results_container_xpath)))
        logger.debug("Healthline search results container located.")

        # Find result elements (adjust XPath if needed)
        result_items_xpath = f"{results_container_xpath}//a[contains(@class, 'css-1qhn6m6')]" # Example, might change
        search_results_elements = driver.find_elements(By.XPATH, result_items_xpath)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on Healthline.")

        for item in search_results_elements:
            try:
                # Healthline links contain the title directly
                title = item.text.strip()
                link = item.get_attribute('href')

                # Ensure link is absolute
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue
                
                # Get detailed content only if enabled
                if settings['enable_detailed_content']:
                    detailed_content = get_detailed_content_selenium(link, driver)
                    if detailed_content:
                        results.append({
                            "source": link,
                            "title": title,
                            "content": detailed_content
                        })
                        logger.debug(f"Extracted Healthline result (detailed): {title[:50]}...")
                    else:
                        # Fallback to title if detailed content fails
                        results.append({"source": link, "title": title, "content": title})
                        logger.debug(f"Extracted Healthline result (title only): {title[:50]}...")
                else:
                    # Use just the title as we don't have a snippet directly
                    results.append({
                        "source": link,
                        "title": title,
                        "content": title # Fallback content
                    })
                    logger.debug(f"Extracted Healthline result (title only): {title[:50]}...")

            except NoSuchElementException:
                logger.warning("Could not find expected elements within a Healthline result item.")
            except Exception as e:
                logger.error(f"Error extracting single Healthline result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"Healthline Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"Healthline search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during Healthline Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for Healthline search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during Healthline search cleanup: {str(e)}")
                 
    return results
