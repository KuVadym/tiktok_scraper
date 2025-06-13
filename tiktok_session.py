import json
from playwright.async_api import async_playwright
from time import sleep

async def main():
    with open("tiktok_session.json", "r") as f:
        cookies = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
        "--autoplay-policy=no-user-gesture-required",
        "--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure",
        "--use-fake-ui-for-media-stream",
        "--no-sandbox",
        "--disable-web-security",
        "--enable-features=NetworkService,NetworkServiceInProcess"
    ])
        # context = await browser.new_context()
        context = await browser.new_context(
    permissions=["microphone", "camera"],
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    viewport={"width": 1280, "height": 800}
)
        await context.add_cookies(cookies)
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/")
        sleep(50)
        await page.screenshot(path="check_login.png")
        await browser.close()

import asyncio
asyncio.run(main())