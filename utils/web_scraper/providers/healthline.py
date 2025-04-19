"""
Healthline search provider (to be re-implemented with Playwright)
"""
import logging
from urllib.parse import urljoin, quote_plus
import asyncio
from ..playwright_utils import PlaywrightManager

logger = logging.getLogger(__name__)

async def search_healthline(query, max_results=5, timeout=8000):
    """Search Healthline for medical information using Playwright"""
    from ..config import is_trusted_domain
    results = []
    search_url = f"https://www.healthline.com/search?q1={quote_plus(query)}"
    base_url = "https://www.healthline.com"
    results_container_selector = "div.css-1t10xxp"
    result_items_selector = "a.css-1qhn6m6"

    async with PlaywrightManager() as pw:
        page, context = await pw.new_page()
        try:
            await page.goto(search_url, timeout=timeout)
            await page.wait_for_selector(results_container_selector, timeout=timeout)
            items = await page.query_selector_all(result_items_selector)
            for item in items[:max_results]:
                title = await item.text_content()
                link = await item.get_attribute('href')
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)
                if not is_trusted_domain(link):
                    continue
                results.append({
                    "source": link,
                    "title": title.strip() if title else None,
                    "content": title.strip() if title else None
                })
        except Exception as e:
            logger.error(f"Healthline Playwright scraping error: {e}")
        finally:
            await context.close()
    return results
