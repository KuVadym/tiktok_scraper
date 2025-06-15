import asyncio
import random
import json
from playwright.async_api import Page
from loguru import logger as log

from urllib.parse import quote
from browser import create_browser_with_session, create_browser_with_new_context
from ustils import save_posts_to_csv
import logging
from config import *
from scraping import scrap_necessary_data
from parsel import Selector


log = logging.getLogger(__name__)


async def check_captcha(page):
    """ Перевіряє, чи є капча, і чекає її проходження """
    while True:
        captcha_present = await page.query_selector('iframe[src*="captcha"]')  # Змінюй селектор відповідно до сайту
        if captcha_present:
            print("Капча виявлена! Очікуємо її проходження вручну...")
            await asyncio.sleep(5)  # Чекаємо кілька секунд перед повторною перевіркою
        else:
            print("Капча зникла! Продовжуємо виконання скрипту.")
            break


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
    print("🌟 Починаємо ставити лайк...")

    try:
        # Чекаємо кнопку лайку
        like_button = await page.wait_for_selector('[data-e2e="like-icon"]', timeout=5000)

        # Перевіряємо початковий стан
        initial_state = await like_button.get_attribute("aria-pressed")
        print(f"🔍 Початковий стан aria-pressed: {initial_state}")

        if initial_state == "true":
            print("✅ Відео вже лайкнуто.")
            return

        # Отримуємо координати для імітації людського кліку
        box = await like_button.bounding_box()
        if box:
            await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await asyncio.sleep(0.2)
            await page.mouse.down()
            await asyncio.sleep(0.2)
            await page.mouse.up()
            print("🖱️ Виконано імітацію людського кліку.")
        else:
            log.warning("⚠️ Не вдалося отримати координати кнопки лайку.")
            return

        # Зачекаємо, поки зміниться атрибут
        await asyncio.sleep(2)
        after_state = await like_button.get_attribute("aria-pressed")
        print(f"🔄 Після кліку: aria-pressed = {after_state}")

        if after_state == "true":
            print("✅ Лайк поставлено успішно.")
        else:
            print("⚠️ Лайк не зафіксовано (клас не змінився).")

    except Exception as e:
        log.warning(f"❌ Виникла помилка при лайканні: {e}")

async def leave_comment(page: Page, comment_text: str):
    try:
        await page.wait_for_timeout(random.randint(500, 1000))

        await page.click('[data-e2e="comment-icon"]')
        await page.wait_for_selector('[data-e2e="comment-input"] [contenteditable="true"]', timeout=7000)

        comment_box = await page.query_selector('[data-e2e="comment-input"] [contenteditable="true"]')
        if comment_box:
            await comment_box.scroll_into_view_if_needed()
            await page.wait_for_timeout(random.randint(500, 1000))

            await comment_box.click()
            await page.wait_for_timeout(random.randint(300, 600))

            for char in comment_text:
                await comment_box.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            await asyncio.sleep(60)
            await page.wait_for_timeout(random.randint(300, 800))

            # ПРОБУЄМО знайти кнопку "відправити коментар"
            # send_button = await page.query_selector('[data-e2e="post-comment"]')
            send_button = await page.query_selector('[data-e2e="comment-post"]')
            if send_button:
                await send_button.click()
                log.info("✅ Коментар залишено.")
            else:
                log.warning("❌ Кнопка надсилання коментаря не знайдена.")
        else:
            log.warning("❌ Поле для вводу коментаря не знайдено.")
    except Exception as e:
        log.warning(f"❌ Не вдалося залишити коментар: {e}")


async def get_video_links(page):
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

async def watch_videos(page, video_links):
    for idx, href in enumerate(video_links):
        
        log.info(f"Відкриваємо відео #{idx + 1}: {href}")
        await page.goto(href, wait_until="domcontentloaded", timeout=60000)
        
        watch_time = await get_video_duration(page)
        await asyncio.sleep(4)
        await check_captcha(page)

        html = await page.content()
        selector = Selector(text=html)
        data = selector.xpath("//script[@id='__UNIVERSAL_DATA_FOR_REHYDRATION__']/text()").get()
        data_for_parse = json.loads(data)["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
        data_to_save = await scrap_necessary_data(data_for_parse)
        print(data_to_save)
        await save_posts_to_csv([data_to_save])


        if should_execute_event(like_percent):  
                await like_video(page)

        if should_execute_event(comment_percent):  
                await leave_comment(page, "Хм. Цікаво...")

        if should_execute_event(skip_percent):
            await asyncio.sleep(4)
            await page.go_back()
            await page.wait_for_selector('div[data-e2e="search_top-item-list"]', timeout=10000)
        else:
            await asyncio.sleep(watch_time)


            # Повернутися назад на сторінку пошуку
            await page.go_back()
            await page.wait_for_selector('div[data-e2e="search_top-item-list"]', timeout=10000)

async def scrape_search(context, keyword: str, max_results: int = 20):
    page = await context.new_page()
    
    search_url = f"https://www.tiktok.com/search?q={quote(keyword)}"
    log.info(f"Відкриваємо сторінку пошуку: {search_url}")

    # await page.goto(search_url, wait_until="networkidle")
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

    await watch_videos(page, video_links[:max_results])

    return video_links[:max_results]

async def main():
    import sys
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    playwright, context = await create_browser_with_session()

    keyword = "вода"
    max_videos = 3
    
    # Запускаємо пошук, перегляд відео і отримуємо список посилань
    try:
        video_links = await scrape_search(context, keyword, max_results=max_videos)
    finally:
        await context.close()
        # await browser.close()
        await playwright.stop()

    print("Знайдені відео:")
    for link in video_links:
        print(link)

asyncio.run(main())