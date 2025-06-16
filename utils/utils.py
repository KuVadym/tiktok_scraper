import csv
import aiofiles
import functools
import os
import asyncio
import random
import logging
from typing import List, Dict 
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeout
from config.config import LOG_DIR, IF_ERROR_DELAY, IF_ERROR_RETRIES
from config.tik_tok_selectors import *

def should_execute_event(probability_percent: int) -> bool:
    return random.randint(1, 100) <= probability_percent

#=============================== Налаштування логування ================================
log = logging.getLogger(__name__)


os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "error.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("tiktok_logger")


#=============================== Обробка помилок ================================
def retry_async(retries=3, delay=1, exceptions=(Exception,), log_fn=print):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    log_fn(f"[!] Спроба {attempt} для {func.__name__} не вдалася: {e}")
                    if attempt == retries:
                        raise
                    await asyncio.sleep(delay)
        return wrapper
    return decorator


#=============================== Функції для роботи з TikTok ================================
#================================ Перевірка капчі ================================
@retry_async(retries=IF_ERROR_RETRIES, delay=IF_ERROR_DELAY, exceptions=(PlaywrightTimeout,), log_fn=logger.warning)
async def check_captcha(page: Page):
    while True:
        captcha_present = await page.query_selector(CAPTCHA_MODAL)
        if captcha_present:
            log.info("Капча виявлена, очікуємо вручну...")
            await asyncio.sleep(5)
        else:
            log.info("Капча зникла, продовжуємо.")
            break


#================================ Отримання тривалості відео ================================
@retry_async(retries=IF_ERROR_RETRIES, delay=IF_ERROR_DELAY, exceptions=(PlaywrightTimeout,), log_fn=logger.warning)
async def get_video_duration(page: Page) -> float:
    try:
        await page.wait_for_selector(VIDEO_TAG, timeout=10000)
        duration = await page.evaluate("document.querySelector('video')?.duration") or 0.0
        return duration + 2
    except Exception as e:
        log.warning(f"Не вдалося визначити тривалість відео: {e}")
        return 0.0


#================================ Лайк відео ================================
@retry_async(retries=IF_ERROR_RETRIES, delay=IF_ERROR_DELAY, exceptions=(PlaywrightTimeout,), log_fn=logger.warning)
async def like_video(page: Page):
    print("🌟 Починаємо ставити лайк...")

    try:
        # Чекаємо кнопку лайку
        like_button = await page.wait_for_selector(LIKE_BUTTON, timeout=5000)

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


#================================ Залишення коментаря ================================
@retry_async(retries=IF_ERROR_RETRIES, delay=IF_ERROR_DELAY, exceptions=(PlaywrightTimeout,), log_fn=logger.warning)
async def leave_comment(page: Page, comment_text: str):
    try:
        await page.wait_for_timeout(random.randint(500, 1000))

        await page.click(COMMENT_ICON)
        await page.wait_for_selector('[data-e2e="comment-input"] [contenteditable="true"]', timeout=7000)

        comment_box = await page.query_selector(COMMENT_INPUT)
        if comment_box:
            await comment_box.scroll_into_view_if_needed()
            await page.wait_for_timeout(random.randint(500, 1000))

            await comment_box.click()
            await page.wait_for_timeout(random.randint(300, 600))

            for char in comment_text:
                await comment_box.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            await page.wait_for_timeout(random.randint(300, 800))

            # ПРОБУЄМО знайти кнопку "відправити коментар"
            send_button = await page.query_selector(COMMENT_SEND_BUTTON)
            if send_button:
                await send_button.click()
                log.info("✅ Коментар залишено.")
            else:
                log.warning("❌ Кнопка надсилання коментаря не знайдена.")
        else:
            log.warning("❌ Поле для вводу коментаря не знайдено.")
    except Exception as e:
        log.warning(f"❌ Не вдалося залишити коментар: {e}")


#================================ Отримання посилань на відео ================================
@retry_async(retries=IF_ERROR_RETRIES, delay=IF_ERROR_DELAY, exceptions=(PlaywrightTimeout,), log_fn=logger.warning)
async def get_video_links(page):
    await page.wait_for_selector(SEARCH_RESULT_CONTAINER, timeout=15000)
    videos = await page.query_selector_all(SEARCH_VIDEO_ITEM)
    links = []
    for video in videos:
        link_handle = await video.query_selector(VIDEO_LINK)
        href = await link_handle.get_attribute('href') if link_handle else None
        if href:
            links.append(href)
    log.info(f"Знайдено відео: {len(links)}")
    return links


#================================ Збереження постів у CSV ================================
@retry_async(retries=IF_ERROR_RETRIES, delay=IF_ERROR_DELAY, exceptions=(PlaywrightTimeout,), log_fn=logger.warning)
async def save_posts_to_csv(posts: List[Dict], filename: str = "tiktok_posts.csv") -> None:
    if not posts:
        print("No posts to save.")
        return

    keys = posts[0].keys()
    file_exists = os.path.isfile(filename)

    async with aiofiles.open(filename, mode="a", encoding="utf-8", newline="") as file:
        if not file_exists:
            await file.write(','.join(keys) + '\n')

        for row in posts:
            line = ','.join(str(row.get(k, "")) for k in keys)
            await file.write(line + '\n')

    print(f"Appended {len(posts)} posts to {filename}")




