import json
from playwright.async_api import async_playwright, BrowserContext

async def create_browser_with_session(cookie_path: str = "tiktok_session.json"):
    """Створює persistent браузерний контекст з cookies і потрібними налаштуваннями."""

    with open(cookie_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    playwright = await async_playwright().start()

    context: BrowserContext = await playwright.chromium.launch_persistent_context(
        user_data_dir="./user_data",  # обовʼязково: persistent session
        channel="chrome",
        headless=False,
        args=[
        "--autoplay-policy=no-user-gesture-required",
        "--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure",
        "--use-fake-ui-for-media-stream",
        "--no-sandbox",
        "--disable-web-security",
        "--enable-features=NetworkService,NetworkServiceInProcess"
        ],
        viewport={"width": 1280, "height": 800},
        permissions=["microphone", "camera"],
        locale="en-US",
        timezone_id="Europe/Kiev",
        geolocation={"longitude": 30.5234, "latitude": 50.4501},  # Київ
        ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete navigator.__proto__.webdriver;
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        delete window.chrome.runtime;
        """)
    # Додаємо cookies до persistent контексту
    await context.add_cookies(cookies)

    return playwright, context


async def create_browser_with_new_context(cookie_path="tiktok_session.json"):
    # Завантажуємо cookies
    with open(cookie_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    playwright = await async_playwright().start()

    # Запускаємо браузер (Chrome)
    browser = await playwright.chromium.launch(
        # channel="chrome",
        headless=False,
        args=[
            "--autoplay-policy=no-user-gesture-required",
            "--disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure",
            "--use-fake-ui-for-media-stream",
            "--no-sandbox",
            "--disable-web-security",
            "--enable-features=NetworkService,NetworkServiceInProcess"
        ],
    )

    # Створюємо новий контекст
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        permissions=["microphone", "camera"],
        locale="en-US",
        timezone_id="Europe/Kiev",
        geolocation={"longitude": 30.5234, "latitude": 50.4501},
        ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    # Маскування (антибот)
    await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    delete navigator.__proto__.webdriver;
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    delete window.chrome?.runtime;
    """)

    # Додаємо cookies
    await context.add_cookies(cookies)

    return playwright, browser, context