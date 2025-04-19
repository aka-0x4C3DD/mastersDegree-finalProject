"""
Playwright utility functions for browser automation and scraping.
"""
import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class PlaywrightManager:
    def __init__(self, headless=True, timeout=None):
        self.headless = headless
        self.browser = None
        self.playwright = None

        # Get timeout from config if not provided
        if timeout is None:
            from .config import get_search_settings
            settings = get_search_settings()
            self.timeout = settings.get('timeout_seconds', 15) * 1000  # Convert to ms
        else:
            self.timeout = timeout

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def new_page(self, **kwargs):
        context = await self.browser.new_context()
        page = await context.new_page()
        return page, context

async def get_text_content(page, selector, timeout=None):
    # Get timeout from config if not provided
    if timeout is None:
        from .config import get_search_settings
        settings = get_search_settings()
        timeout = settings.get('timeout_seconds', 15) * 1000  # Convert to ms
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        element = await page.query_selector(selector)
        if element:
            return await element.text_content()
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout waiting for selector: {selector}")
    return None

async def get_attribute(page, selector, attribute, timeout=None):
    # Get timeout from config if not provided
    if timeout is None:
        from .config import get_search_settings
        settings = get_search_settings()
        timeout = settings.get('timeout_seconds', 15) * 1000  # Convert to ms
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        element = await page.query_selector(selector)
        if element:
            return await element.get_attribute(attribute)
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout waiting for selector: {selector}")
    return None

async def get_elements(page, selector, timeout=None):
    # Get timeout from config if not provided
    if timeout is None:
        from .config import get_search_settings
        settings = get_search_settings()
        timeout = settings.get('timeout_seconds', 15) * 1000  # Convert to ms
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return await page.query_selector_all(selector)
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout waiting for selector: {selector}")
    return []

# Example usage:
# async with PlaywrightManager() as pw:
#     page, context = await pw.new_page()
#     await page.goto('https://example.com')
#     ...
