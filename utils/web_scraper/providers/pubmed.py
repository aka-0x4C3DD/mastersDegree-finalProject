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

        # Wait for search results container using CSS Selector (adjust if needed)
        # Example: Look for a div with class 'search-results-chunks'
        results_container_selector = "div.search-results-chunks" # Placeholder - VERIFY THIS SELECTOR
        wait = WebDriverWait(driver, settings['timeout_seconds'] + 5) # Slightly longer wait for PubMed
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, results_container_selector)))
        logger.debug("PubMed search results container located.")

        # Find result elements using CSS Selector (adjust if needed)
        # Example: Find articles with class 'full-docsum' within the container
        result_items_selector = f"{results_container_selector} article.full-docsum" # Placeholder - VERIFY THIS SELECTOR
        search_results_elements = driver.find_elements(By.CSS_SELECTOR, result_items_selector)[:settings['max_results']]
        logger.info(f"Found {len(search_results_elements)} potential result elements on PubMed.")

        for item in search_results_elements:
            try:
                # Use relative CSS Selectors (adjust if needed)
                # Example: Find link with class 'docsum-title'
                title_elem_selector = "a.docsum-title" # Placeholder - VERIFY THIS SELECTOR
                # Example: Find span with class 'docsum-pmid'
                article_id_selector = "span.docsum-pmid" # Placeholder - VERIFY THIS SELECTOR
                # Example: Find span with class 'docsum-authors'
                authors_selector = "span.docsum-authors" # Placeholder - VERIFY THIS SELECTOR
                # Example: Find span with class 'docsum-journal-citation'
                journal_selector = "span.docsum-journal-citation" # Placeholder - VERIFY THIS SELECTOR

                title_elem = item.find_element(By.CSS_SELECTOR, title_elem_selector)
                pmid_elem = item.find_element(By.CSS_SELECTOR, article_id_selector)
                
                title = title_elem.text.strip()
                article_id = pmid_elem.text.strip()
                link = f"{base_url}/{article_id}/"

                # Validate domain
                if not is_trusted_domain(link):
                    logger.debug(f"Skipping non-trusted domain: {link}")
                    continue
                
                # Try to extract authors and journal info if available
                snippet = ""
                try:
                    authors = item.find_element(By.CSS_SELECTOR, authors_selector).text.strip()
                    snippet += authors + ". "
                except NoSuchElementException: pass
                try:
                    journal = item.find_element(By.CSS_SELECTOR, journal_selector).text.strip()
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
                logger.warning("Could not find expected elements (title/pmid) within a PubMed result item using CSS selectors.")
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
