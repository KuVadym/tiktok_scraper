import asyncio
import json
from loguru import logger as log
from typing import List, Dict
from urllib.parse import quote
from browser import create_browser_with_session

async def scrape_search(keyword: str, max_results: int = 20) -> List[Dict]:
    results = []

    context = await create_browser_with_session()
    page = await context.new_page()

    search_url = f"https://www.tiktok.com/search?q={quote(keyword)}"
    log.info(f"Opening search page: {search_url}")
    await page.goto(search_url)

    await page.goto(search_url, wait_until="networkidle")

    await page.wait_for_selector('div[data-e2e="search-video-feed-item"]', timeout=10000, state="attached")


    return results


async def run():
    keyword = "whales"
    search_data = await scrape_search(keyword=keyword, max_results=20)

    with open("search_data.json", "w", encoding="utf-8") as file:
        json.dump(search_data, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(run())
