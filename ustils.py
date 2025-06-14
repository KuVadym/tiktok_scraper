import csv
from typing import List, Dict

def save_posts_to_csv(posts: List[Dict], filename: str = "tiktok_posts.csv") -> None:
    if not posts:
        print("No posts to save.")
        return

    keys = posts[0].keys()

    with open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(posts)

    print(f"Saved {len(posts)} posts to {filename}")