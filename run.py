import asyncio
from core.browser import create_browser_with_session, apply_stealth
from core.data_processing import search_links, watch_videos
from config.config import max_results



async def main():
    playwright, context = await create_browser_with_session()
    page = await context.new_page()
    # await apply_stealth(page)
    keyword = "вода"
    max_videos = 3
    try:
        video_links = await search_links(page, keyword, max_results=max_videos)
        
        await watch_videos(page, video_links[:max_results])
    finally:
        await context.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
