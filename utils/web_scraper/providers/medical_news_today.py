"""
Medical News Today search provider using Selenium
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

def search_medical_news_today(query):
    """Search Medical News Today for medical information using Selenium"""
    settings = get_search_settings()
    search_url = f"https://www.medicalnewstoday.com/search?q={quote_plus(query)}"
    base_url = "https://www.medicalnewstoday.com"
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for Medical News Today search.")
            return []
            
        logger.info(f"Navigating to Medical News Today search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container (adjust XPath if needed)
        results_container_xpath = "//div[contains(@class, 'css-1k8qqf1')]" # Example, might change
        wait = WebDriverWait(driver, settings['timeout_seconds'])
        wait.until(EC.presence_of_element_located((By.XPATH, results_container_xpath)))
        logger.debug("Medical News Today search results container located.")

        # Find result elements (adjust XPath if needed)
        result_items_xpath = f"{results_container_xpath}//a[contains(@class, 'css-ni2lnp')]" # Example, might change
        search_results_elements = driver.find_elements(By.XPATH, result_items_xpath)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on Medical News Today.")

        for item in search_results_elements:
            try:
                # Use relative XPath
                title_elem_xpath = ".//span[contains(@class, 'css-u1w2sb')]" # Example, might change

                title_elem = item.find_element(By.XPATH, title_elem_xpath)
                title = title_elem.text.strip()
                link = item.get_attribute('href')

                # Ensure link is absolute
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue
                
                # Get detailed content from the article page if enabled
                if settings['enable_detailed_content']:
                    detailed_content = get_detailed_content_selenium(link, driver)
                    if detailed_content:
                        results.append({
                            "source": link,
                            "title": title,
                            "content": detailed_content
                        })
                        logger.debug(f"Extracted MNT result (detailed): {title[:50]}...")
                    else:
                        # Fallback to title if detailed content fails
                        results.append({"source": link, "title": title, "content": title})
                        logger.debug(f"Extracted MNT result (title only): {title[:50]}...")
                else:
                    # Use just the title if we're not getting detailed content
                    results.append({
                        "source": link,
                        "title": title,
                        "content": title # Fallback content
                    })
                    logger.debug(f"Extracted MNT result (title only): {title[:50]}...")

            except NoSuchElementException:
                logger.warning("Could not find expected elements within a Medical News Today result item.")
            except Exception as e:
                logger.error(f"Error extracting single Medical News Today result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"Medical News Today Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"Medical News Today search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during Medical News Today Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for Medical News Today search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during Medical News Today search cleanup: {str(e)}")
                 
    return results
