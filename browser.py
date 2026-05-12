"""Playwright-based web automation for research and browsing."""
import asyncio
from typing import Optional


async def fetch_page_text(url: str, timeout: int = 15000) -> str:
    """Fetch visible text content from a URL using Playwright."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            text = await page.inner_text("body")
            await browser.close()
            return text[:5000]
    except Exception as e:
        return f"Could not fetch page: {e}"


async def search_web(query: str) -> str:
    """Search Google and return the first page of text results."""
    import urllib.parse
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    return await fetch_page_text(url)


async def get_page_summary(url: str) -> str:
    """Get a brief summary of a page's content."""
    text = await fetch_page_text(url)
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 40]
    return "\n".join(lines[:20])
