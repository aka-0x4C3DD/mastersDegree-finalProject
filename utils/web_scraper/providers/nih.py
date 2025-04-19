"""
NIH search provider (to be re-implemented with Playwright)
"""
import logging
from urllib.parse import urljoin, quote_plus
import asyncio
from ..playwright_utils import PlaywrightManager

logger = logging.getLogger(__name__)

async def search_nih(query, max_results=5, timeout=8000):
    """Search NIH website for information using Playwright"""
    from ..config import is_trusted_domain
    results = []
    search_url = f"https://search.nih.gov/search?utf8=%E2%9C%93&affiliate=nih&query={quote_plus(query)}"
    base_url = "https://www.nih.gov"
    results_container_selector = "#results-list"
    result_items_selector = "#results-list .result"
    title_selector = "h3 a"
    snippet_selector = ".search-results-excerpt"

    async with PlaywrightManager() as pw:
        page, context = await pw.new_page()
        try:
            await page.goto(search_url, timeout=timeout)
            await page.wait_for_selector(results_container_selector, timeout=timeout)
            items = await page.query_selector_all(result_items_selector)
            for item in items[:max_results]:
                title_elem = await item.query_selector(title_selector)
                snippet_elem = await item.query_selector(snippet_selector)
                title = await title_elem.text_content() if title_elem else None
                link = await title_elem.get_attribute('href') if title_elem else None
                snippet = await snippet_elem.text_content() if snippet_elem else title
                if link and not link.startswith('http'):
                    link = urljoin(base_url, link)
                if not is_trusted_domain(link):
                    continue
                results.append({
                    "source": link,
                    "title": title.strip() if title else None,
                    "content": snippet.strip() if snippet else None
                })
        except Exception as e:
            logger.error(f"NIH Playwright scraping error: {e}")
        finally:
            await context.close()
    return results
