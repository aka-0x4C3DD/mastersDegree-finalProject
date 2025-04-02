"""
PubMed search provider using Selenium
"""
import logging
from urllib.parse import quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils import get_selenium_driver, clean_text
from ..config import get_search_settings, is_trusted_domain
from ..content_extractor import get_pubmed_abstract_selenium # Use Selenium version

logger = logging.getLogger(__name__)

def search_pubmed(query):
    """Search PubMed for medical research papers and information using Selenium"""
    settings = get_search_settings()
    search_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(query)}"
    base_url = "https://pubmed.ncbi.nlm.nih.gov"
    results = []
    driver = None # Initialize driver variable
    try:
        driver = get_selenium_driver()
        if not driver:
            logger.error("Selenium driver not available for PubMed search.")
            return []
            
        logger.info(f"Navigating to PubMed search URL: {search_url}")
        driver.get(search_url)

        # Wait for search results container (adjust XPath if needed)
        results_container_xpath = "//div[@class='search-results-chunks']"
        wait = WebDriverWait(driver, settings['timeout_seconds'] + 5) # Slightly longer wait for PubMed
        wait.until(EC.presence_of_element_located((By.XPATH, results_container_xpath)))
        logger.debug("PubMed search results container located.")

        # Find result elements (adjust XPath if needed)
        result_items_xpath = f"{results_container_xpath}//article[contains(@class, 'full-docsum')]"
        search_results_elements = driver.find_elements(By.XPATH, result_items_xpath)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on PubMed.")

        for item in search_results_elements:
            try:
                # Use relative XPath
                title_elem_xpath = ".//a[contains(@class, 'docsum-title')]"
                article_id_xpath = ".//span[contains(@class, 'docsum-pmid')]" # Get PMID for link

                title_elem = item.find_element(By.XPATH, title_elem_xpath)
                pmid_elem = item.find_element(By.XPATH, article_id_xpath)
                
                title = title_elem.text.strip()
                article_id = pmid_elem.text.strip()
                link = f"{base_url}/{article_id}/"

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue
                
                # Try to extract authors and journal info if available
                authors_xpath = ".//span[contains(@class, 'docsum-authors')]"
                journal_xpath = ".//span[contains(@class, 'docsum-journal-citation')]"
                snippet = ""
                try:
                    authors = item.find_element(By.XPATH, authors_xpath).text.strip()
                    snippet += authors + ". "
                except NoSuchElementException: pass
                try:
                    journal = item.find_element(By.XPATH, journal_xpath).text.strip()
                    snippet += journal
                except NoSuchElementException: pass
                
                # If we have article ID and detailed content is enabled, try to get abstract
                if settings['enable_detailed_content']:
                    detailed_content = get_pubmed_abstract_selenium(link, driver) # Pass driver
                    content = detailed_content if detailed_content else snippet
                else:
                    content = snippet
                
                if title and content:
                    results.append({
                        "source": link,
                        "title": title,
                        "content": content
                    })
                    logger.debug(f"Extracted PubMed result: {title[:50]}...")
                else:
                     logger.warning("Found PubMed result item but couldn't extract title/content.")

            except NoSuchElementException:
                logger.warning("Could not find expected elements (title/pmid) within a PubMed result item.")
            except Exception as e:
                logger.error(f"Error extracting single PubMed result via Selenium: {str(e)}", exc_info=True)

        logger.info(f"PubMed Selenium search extracted {len(results)} results.")

    except TimeoutException:
        logger.warning(f"PubMed search timed out waiting for elements on {search_url}")
    except Exception as e:
        logger.error(f"Error during PubMed Selenium search: {str(e)}", exc_info=True)
    finally:
        # --- Ensure driver is quit ---
        if driver:
            try:
                logger.debug(f"Quitting Selenium driver for PubMed search.")
                driver.quit()
            except Exception as e:
                 logger.error(f"Error quitting driver during PubMed search cleanup: {str(e)}")
                 
    return results
