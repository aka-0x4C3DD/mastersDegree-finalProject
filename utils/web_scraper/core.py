import logging
import asyncio
import time

from .providers import SEARCH_PROVIDERS
from .config import get_search_settings

logger = logging.getLogger(__name__)

async def search_medical_sites(query, max_results=3):
    """Search for information from trusted medical sites using Playwright in parallel.

    Args:
        query: The search query
        max_results: Maximum number of results to return per site (overall limit applied later)

    Returns:
        A list of dictionaries containing source URLs and content snippets
    """
    logger.info(f"Searching medical sites in parallel for: {query}")
    all_results = []
    settings = get_search_settings()
    settings['max_results'] = max_results

    start_time = time.time()
    # Run all provider functions in parallel using asyncio.gather
    tasks = [provider(query, max_results=max_results) for provider in SEARCH_PROVIDERS]
    provider_results_list = await asyncio.gather(*tasks, return_exceptions=True)

    for provider_func, provider_results in zip(SEARCH_PROVIDERS, provider_results_list):
        provider_name = provider_func.__name__
        if isinstance(provider_results, Exception):
            logger.error(f"Error executing provider '{provider_name}': {provider_results}")
            continue
        if provider_results:
            logger.info(f"Provider '{provider_name}' completed successfully, returned {len(provider_results)} results.")
            all_results.extend(provider_results)
        else:
            logger.info(f"Provider '{provider_name}' completed successfully, returned no results.")

    total_duration = time.time() - start_time
    logger.info(f"Completed all providers in {total_duration:.2f}s. Found {len(all_results)} total results before deduplication.")

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
