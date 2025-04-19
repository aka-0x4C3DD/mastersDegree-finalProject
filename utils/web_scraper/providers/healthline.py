"""
Healthline search provider (to be re-implemented with Playwright)
"""
import logging
from urllib.parse import urljoin, quote_plus
import asyncio
from ..playwright_utils import PlaywrightManager

logger = logging.getLogger(__name__)

async def search_healthline(query, max_results=5, timeout=None):
    # Get timeout from config if not provided
    if timeout is None:
        from ..config import get_search_settings
        settings = get_search_settings()
        timeout = settings.get('timeout_seconds', 20) * 1000  # Convert to ms
    """Search Healthline for medical information using Playwright"""
    from ..config import is_trusted_domain
    results = []
    search_url = f"https://www.healthline.com/search-results?q={quote_plus(query)}"
    base_url = "https://www.healthline.com"
    results_container_selector = "div.search-results-container"
    result_items_selector = "div.search-results-item"

    async with PlaywrightManager() as pw:
        page, context = await pw.new_page()
        try:
            await page.goto(search_url, timeout=timeout)
            await page.wait_for_selector(results_container_selector, timeout=timeout)
            items = await page.query_selector_all(result_items_selector)
            for item in items[:max_results]:
                title_elem = await item.query_selector('h2.search-results-item-title')
                link_elem = await item.query_selector('a.search-results-item-link')
                snippet_elem = await item.query_selector('p.search-results-item-description')

                title = await title_elem.text_content() if title_elem else None
                link = await link_elem.get_attribute('href') if link_elem else None
                snippet = await snippet_elem.text_content() if snippet_elem else title
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)
                if not is_trusted_domain(link):
                    continue
                results.append({
                    "source": link,
                    "title": title.strip() if title else None,
                    "content": snippet.strip() if snippet else title
                })
        except Exception as e:
            logger.error(f"Healthline Playwright scraping error: {e}")
        finally:
            await context.close()
    return results
