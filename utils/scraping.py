import jmespath



async def scrap_necessary_data(data, href = None):
    parsed_post_data = jmespath.search(
    """{
        video_url: video.playAddr,
        views: stats.playCount,
        likes: stats.diggCount,
        comments: stats.commentCount
    }""",
    data
)
    if href:
        parsed_post_data["video_url"] = href
    return parsed_post_data
