import asyncio
import random
import json
import csv
import os
from playwright.async_api import Page
from loguru import logger as log
from typing import List, Dict
from urllib.parse import quote
from crate_browser_session import create_browser_with_session
import logging
from config import *
from scraper import scrap_necessary_data


log = logging.getLogger(__name__)


async def get_video_duration(page: Page) -> float:
    try:
        await page.wait_for_selector('video', timeout=10000)
        duration = await page.evaluate("document.querySelector('video')?.duration")
        duration += 2
        return duration or 0.0
    except Exception as e:
        log.warning(f"Не вдалося визначити тривалість відео: {e}")
        return 0.0
    

def should_execute_event(probability_percent: int) -> bool:
    return random.randint(1, 100) <= probability_percent


async def like_video(page: Page):
    try:
        await page.click('[data-e2e="like-icon"]')
        log.info("Поставлено лайк.")
        await asyncio.sleep(10)
    except Exception as e:
        log.warning(f"Не вдалося поставити лайк: {e}")


async def leave_comment(page: Page, comment_text: str):
    try:
        await page.click('[data-e2e="comment-icon"]')
        await page.fill('[data-e2e="comment-input"]', comment_text)
        await page.press('[data-e2e="comment-input"]', "Enter")
        log.info("Коментар залишено.")
    except Exception as e:
        log.warning(f"Не вдалося залишити коментар: {e}")
    

async def get_video_links(page) -> List[str]:
    await page.wait_for_selector('div[data-e2e="search_top-item-list"]', timeout=15000)
    videos = await page.query_selector_all('[data-e2e="search_top-item-list"] [data-e2e="search_top-item"]')
    links = []
    for video in videos:
        link_handle = await video.query_selector('a.css-1mdo0pl-AVideoContainer')
        href = await link_handle.get_attribute('href') if link_handle else None
        if href:
            links.append(href)
    log.info(f"Знайдено відео: {len(links)}")
    return links

async def watch_videos(page, video_links: List[str]):
    for idx, href in enumerate(video_links):
        log.info(f"Відкриваємо відео #{idx + 1}: {href}")
        await page.goto(href, wait_until="domcontentloaded", timeout=60000)
        watch_time = await get_video_duration(page)

        

        if should_execute_event(skip_percent):
            await asyncio.sleep(4)
            await page.go_back()
            await page.wait_for_selector('div[data-e2e="search_top-item-list"]', timeout=10000)
        else:
            await asyncio.sleep(watch_time)

            
            # if should_execute_event(like_percent):  
            #     await like_video(page)

            # if should_execute_event(comment_percent):  
            #     await leave_comment(page, "Nice video! 🔥")
            # Повернутися назад на сторінку пошуку
            await page.go_back()
            await page.wait_for_selector('div[data-e2e="search_top-item-list"]', timeout=10000)

async def scrape_search(context, keyword: str, max_results: int = 20) -> List[str]:
    page = await context.new_page()
    
    search_url = f"https://www.tiktok.com/search?q={quote(keyword)}"
    log.info(f"Відкриваємо сторінку пошуку: {search_url}")

    await page.goto(search_url, wait_until="networkidle")

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

    await watch_videos(page, video_links[:max_results])

    return video_links[:max_results]

async def main():
    import sys
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    playwright, browser, context = await create_browser_with_session()

    keyword = "мем"
    max_videos = 5
    
    # Запускаємо пошук, перегляд відео і отримуємо список посилань
    try:
        video_links = await scrape_search(context, keyword, max_results=max_videos)
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

    print("Знайдені відео:")
    for link in video_links:
        print(link)

asyncio.run(main())