from playwright.async_api import async_playwright

STORAGE_STATE = "tiktok_session.json"

async def save_tiktok_session():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # видимий браузер
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login")

        print("🔑 Увійди вручну, потім натисни Enter тут в терміналі...")
        input()

        await context.storage_state(path=STORAGE_STATE)
        print(f"✅ Сесію збережено у файл {STORAGE_STATE}")

        await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(save_tiktok_session())