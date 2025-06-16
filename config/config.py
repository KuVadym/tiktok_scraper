skip_percent = 12
like_percent = 100
comment_percent = 100
max_results = 5

IF_ERROR_RETRIES = 3
IF_ERROR_DELAY = 2

import os

BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, "logs")
COOKIE_PATH = os.path.join(BASE_DIR, "config", "tiktok_session.json")
