"""
Core functionality for searching medical sites
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from .config import get_search_settings
from .providers import SEARCH_PROVIDERS
from .utils import sanitize_query

logger = logging.getLogger(__name__)

def search_medical_sites(query, max_results=None):
    """Search for information from trusted medical sites with parallel requests
    
    Args:
        query: The search query
        max_results: Maximum number of results to return (overrides config)
        
    Returns:
        A list of dictionaries containing source URLs and content snippets
    """
    # Sanitize the query
    sanitized_query = sanitize_query(query)
    logger.info(f"Searching medical sites for: {sanitized_query}")
    
    # Get settings from config (or use override if provided)
    settings = get_search_settings()
    if max_results is not None:
        settings['max_results'] = max_results
    
    all_results = []
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=len(SEARCH_PROVIDERS)) as executor:
        # Submit all search tasks
        future_to_search = {
            executor.submit(search_func, sanitized_query): search_func.__name__ 
            for search_func in SEARCH_PROVIDERS
        }
        
        # Process results as they complete
        for future in future_to_search:
            search_name = future_to_search[future]
            try:
                results = future.result()
                if results:
                    logger.info(f"{search_name} returned {len(results)} results")
                    all_results.extend(results)
            except Exception as e:
                logger.error(f"Error in {search_name}: {str(e)}")
    
    # Sort results by content length (prioritize detailed information)
    all_results.sort(key=lambda x: len(x.get('content', '')), reverse=True)
    
    # Deduplicate results based on content similarity
    unique_results = []
    seen_content = set()
    
    for result in all_results:
        content_sample = result.get('content', '')[:100].lower()  # Take first 100 chars for comparison
        if content_sample and content_sample not in seen_content:
            seen_content.add(content_sample)
            unique_results.append(result)
    
    logger.info(f"Total unique results found: {len(unique_results)}")
    return unique_results[:settings['max_results']]
