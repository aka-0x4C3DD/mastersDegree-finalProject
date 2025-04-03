import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import provider functions dynamically
from .providers import SEARCH_PROVIDERS
# Import the missing function
from .config import get_search_settings

logger = logging.getLogger(__name__)

# Define a reasonable limit for parallel browser instances
MAX_PARALLEL_BROWSERS = 4

def search_medical_sites(query, max_results=3):
    """Search for information from trusted medical sites using Selenium in parallel.

    Args:
        query: The search query
        max_results: Maximum number of results to return per site (overall limit applied later)

    Returns:
        A list of dictionaries containing source URLs and content snippets
    """
    logger.info(f"Searching medical sites in parallel for: {query}")
    all_results = []

    # Limit the number of concurrent workers to avoid resource exhaustion
    num_workers = min(len(SEARCH_PROVIDERS), MAX_PARALLEL_BROWSERS)
    logger.info(f"Using up to {num_workers} parallel workers for web scraping.")

    start_time = time.time()
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all search tasks
        future_to_search = {
            executor.submit(search_func, query): search_func.__name__
            for search_func in SEARCH_PROVIDERS
        }

        # Process results as they complete
        for future in as_completed(future_to_search):
            search_name = future_to_search[future]
            try:
                # Get the result from the future (which is the list from the provider)
                provider_results = future.result()
                if provider_results:
                    logger.info(f"Provider '{search_name}' completed successfully, returned {len(provider_results)} results.")
                    all_results.extend(provider_results)
                else:
                    logger.info(f"Provider '{search_name}' completed successfully, returned no results.")
            except Exception as e:
                # Log exceptions raised within the provider function
                logger.error(f"Error executing provider '{search_name}': {str(e)}", exc_info=True)

    total_duration = time.time() - start_time
    logger.info(f"Completed all providers in {total_duration:.2f}s. Found {len(all_results)} total results before deduplication.")

    # Sort results by content length (prioritize detailed information)
    all_results.sort(key=lambda x: len(x.get('content', '')), reverse=True)

    # Deduplicate results based on content similarity (simple approach)
    unique_results = []
    seen_content_prefix = set()

    for result in all_results:
        content_sample = result.get('content', '')[:150].lower().strip() # Use a slightly longer prefix
        if content_sample and content_sample not in seen_content_prefix:
            seen_content_prefix.add(content_sample)
            unique_results.append(result)
        elif not content_sample:
             logger.debug("Skipping result with empty content during deduplication.")

    logger.info(f"Total unique results found after deduplication: {len(unique_results)}")

    # Apply the final max_results limit AFTER deduplication
    final_max_results = get_search_settings().get('max_results', 3) # Get limit from config
    logger.info(f"Returning top {final_max_results} unique results.")
    return unique_results[:final_max_results]
