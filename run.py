import asyncio
import json
from scraper import scrape_posts

async def run():
    post_data = await scrape_posts(
        urls=[
            "https://www.tiktok.com/@oddanimalspecimens/video/7198206283571285294"
        ]
    )
    # save the result to a JSON file
    with open("post_data.json", "w", encoding="utf-8") as file:
        json.dump(post_data, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(run())