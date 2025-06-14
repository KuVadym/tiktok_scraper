import json
from playwright.async_api import async_playwright, BrowserContext

async def create_browser_with_session(cookie_path: str = "tiktok_session.json") -> BrowserContext:
    """Створює браузерний контекст з cookies і потрібними налаштуваннями"""
    with open(cookie_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    playwright = await async_playwright().start()

    browser = await playwright.chromium.launch(
        channel="chrome",
        headless=False,
        args=[
            "--autoplay-policy=no-user-gesture-required",
            "--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure",
            "--use-fake-ui-for-media-stream",
            "--no-sandbox",
            "--disable-web-security",
            "--enable-features=NetworkService,NetworkServiceInProcess"
        ]
    )

    context = await browser.new_context(
        permissions=["microphone", "camera"],
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )

    await context.add_cookies(cookies)
    return playwright, browser, context