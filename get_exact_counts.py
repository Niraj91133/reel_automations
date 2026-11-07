import sys
import time
import re
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies

sys.stdout.reconfigure(encoding='utf-8')

codes = ["DfT7L8BBlaN", "DbnfPsNNOUz", "Db90Bo_P8gD", "DasTHW6vLke", "DfTnI4kP-Ug"]
cookies = get_channel_cookies('startup_road')

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-dev-shm-usage', '--no-sandbox', '--blink-settings=imagesEnabled=false']
    )
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    for code in codes:
        url = f"https://www.instagram.com/reel/{code}/"
        page.goto(url, timeout=20000, wait_until='domcontentloaded')
        time.sleep(3)
        html = page.content()
        
        # Regex search in raw HTML
        # In Instagram HTML, counts often appear in JSON blocks like "comment_count": 1234 or "edge_media_to_comment":{"count":1234}
        comments = []
        for m in re.finditer(r'(?:comment_count|edge_media_to_comment[\'"]?\s*:\s*\{[\'"]?count[\'"]?)\s*:\s*(\d+)', html):
            comments.append(int(m.group(1)))
            
        likes = []
        for m in re.finditer(r'(?:like_count|edge_media_preview_like[\'"]?\s*:\s*\{[\'"]?count[\'"]?)\s*:\s*(\d+)', html):
            likes.append(int(m.group(1)))

        print(f"Code {code}:", flush=True)
        print(f"  Likes matches: {likes[:3]}", flush=True)
        print(f"  Comments matches: {comments[:3]}", flush=True)

    browser.close()

