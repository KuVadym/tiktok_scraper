from playwright.async_api import async_playwright
import json
import jmespath
from typing import List, Dict
from parsel import Selector
from loguru import logger as log

async def fetch_page_html(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale='en-US',
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        )
        page = await context.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("script#__UNIVERSAL_DATA_FOR_REHYDRATION__", state="attached", timeout=10000)
        html = await page.content()
        await browser.close()
        return html
    

def parse_post(html: str) -> Dict:
    selector = Selector(text=html)
    data = selector.xpath("//script[@id='__UNIVERSAL_DATA_FOR_REHYDRATION__']/text()").get()
    post_data = json.loads(data)["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
    parsed_post_data = jmespath.search(
        """{
        id: id,
        desc: desc,
        createTime: createTime,
        video: video.{duration: duration, ratio: ratio, cover: cover, playAddr: playAddr, downloadAddr: downloadAddr, bitrate: bitrate},
        author: author.{id: id, uniqueId: uniqueId, nickname: nickname, avatarLarger: avatarLarger, signature: signature, verified: verified},
        stats: stats,
        locationCreated: locationCreated,
        diversificationLabels: diversificationLabels,
        suggestedWords: suggestedWords,
        contents: contents[].{textExtra: textExtra[].{hashtagName: hashtagName}}
        }""",
        post_data
    )
    return parsed_post_data

async def scrape_posts(urls: List[str]) -> List[Dict]:
    data = []
    for url in urls:
        html = await fetch_page_html(url)
        post_data = parse_post(html)
        data.append(post_data)
    log.success(f"Scraped {len(data)} posts")
    return data


async def scrap_necessary_data(data):
    parsed_post_data = jmespath.search(
    """{
        video_url: video.playAddr,
        views: stats.playCount,
        likes: stats.diggCount,
        comments: stats.commentCount
    }""",
    data
)
    return parsed_post_data

# Run the scraper
async def run():
    post_data = await scrape_posts([
        "https://www.tiktok.com/@oddanimalspecimens/video/7198206283571285294"
    ])
    with open("post_data.json", "w", encoding="utf-8") as f:
        json.dump(post_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
