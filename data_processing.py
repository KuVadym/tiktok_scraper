import asyncio
import json
from urllib.parse import quote
from utils import get_video_duration, check_captcha, should_execute_event
from utils import like_video, leave_comment, get_video_links, save_posts_to_csv
from tik_tok_selectors import *
import logging
from config import *
from scraping import scrap_necessary_data
from parsel import Selector


log = logging.getLogger(__name__)



async def watch_videos(page, video_links):
    for idx, href in enumerate(video_links):
        log.info(f"Відкриваємо відео #{idx + 1}: {href}")
        await page.goto(href, wait_until="domcontentloaded", timeout=60000)
        
        watch_time = await get_video_duration(page)

        await asyncio.sleep(4)
        await check_captcha(page)
        await asyncio.sleep(4)

        html = await page.content()
        selector = Selector(text=html)
        data = selector.xpath(VIDEO_SCRIPT_JSON_XPATH).get()
        data_for_parse = json.loads(data)["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
        data_to_save = await scrap_necessary_data(data_for_parse, href)
        await save_posts_to_csv([data_to_save])


        if should_execute_event(like_percent):  
                await like_video(page)

        if should_execute_event(comment_percent):  
                await leave_comment(page, "Хм. Цікаво...")

        if should_execute_event(skip_percent):
            await asyncio.sleep(4)
            await page.go_back()
            await page.wait_for_selector(SEARCH_TOP_LIST, timeout=10000)
        else:
            await asyncio.sleep(watch_time)


            # Повернутися назад на сторінку пошуку
            await page.go_back()
            await page.wait_for_selector('div[data-e2e="search_top-item-list"]', timeout=10000)

async def search_links(page, keyword: str, max_results: int = 20):
    search_url = f"https://www.tiktok.com/search?q={quote(keyword)}"
    log.info(f"Відкриваємо сторінку пошуку: {search_url}")


    await page.goto(search_url, wait_until="load")


    video_links = []
    while len(video_links) < max_results:
        new_links = await get_video_links(page)
        # Додаємо тільки унікальні посилання
        for link in new_links:
            if link not in video_links:
                video_links.append(link)
                if len(video_links) >= max_results:
                    break
        if len(video_links) < max_results:
            log.info("Прокручуємо сторінку для завантаження нових відео...")
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(3)

    return video_links[:max_results]
