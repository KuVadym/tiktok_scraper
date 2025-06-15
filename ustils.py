import csv
import aiofiles
import os
from typing import List, Dict

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