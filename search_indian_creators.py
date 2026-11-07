import sys
import time
import re
import json
import urllib.parse
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies

sys.stdout.reconfigure(encoding='utf-8')

cookies = get_channel_cookies('startup_road')
searched_creators = set()

queries = ["machine business", "laghu udyog", "small manufacturing", "business ideas hindi"]

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-dev-shm-usage', '--no-sandbox', '--blink-settings=imagesEnabled=false']
    )
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    for q in queries:
        url = f"https://www.instagram.com/explore/search/keyword/?q={urllib.parse.quote(q)}"
        try:
            page.goto(url, timeout=20000, wait_until='domcontentloaded')
            time.sleep(3)
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(2)

            links = page.query_selector_all('a[href*="/reel/"]')
            print(f"Query '{q}': found {len(links)} reels", flush=True)

            for link in links[:15]:
                href = link.get_attribute("href") or ""
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1)
                searched_creators.add(code)
        except Exception as e:
            print(f"Error on query {q}: {e}", flush=True)

    browser.close()

print(f"Total discovered candidate reels from keyword search: {len(searched_creators)}")
with open("keyword_reels.json", "w", encoding="utf-8") as f:
    json.dump(list(searched_creators), f, indent=2)

