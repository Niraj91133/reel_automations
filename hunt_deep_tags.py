import os
import sys
import re
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.niche_hunter import get_channel_cookies

cookies = get_channel_cookies("startup_road")

TAGS = [
    "smallbusinessindia",
    "businessideas",
    "lowinvestmentbusiness",
    "manufacturingbusiness"
]

reels = []
seen = set()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    def block_heavy(route):
        if route.request.resource_type in ["image", "media", "font"]:
            route.abort()
        else:
            route.continue_()
    page.route("**/*", block_heavy)

    for tag in TAGS:
        if len(reels) >= 15:
            break
        url = f"https://www.instagram.com/explore/tags/{tag}/"
        try:
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(3)
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(2)

            links = page.query_selector_all('a[href*="/reel/"], a[href*="/p/"]')
            for a in links:
                if len(reels) >= 15:
                    break
                href = a.get_attribute("href") or ""
                m = re.search(r'/(?:reel|p)/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1).strip()
                if code in seen:
                    continue
                seen.add(code)
                card_text = a.inner_text().strip().replace('\n', ' ')
                reels.append({
                    "code": code,
                    "url": f"https://www.instagram.com/reel/{code}/",
                    "tag": f"#{tag}",
                    "text": card_text
                })
        except Exception as e:
            pass

    browser.close()

print(f"Total Found: {len(reels)}")
for r in reels[:12]:
    print(r['url'], r['tag'], r['text'])
