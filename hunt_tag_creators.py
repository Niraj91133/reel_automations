import sys
import time
import re
import json
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies, parse_views_count

sys.stdout.reconfigure(encoding='utf-8')

cookies = get_channel_cookies('startup_road')
discovered_creators_reels = []

tags = ["laghuudyog", "manufacturingbusiness", "businessideashindi", "smallbusinessindia", "franchisebusiness"]

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

    for tag in tags:
        tag_url = f"https://www.instagram.com/explore/tags/{tag}/"
        try:
            print(f"Checking #{tag}...", flush=True)
            page.goto(tag_url, timeout=20000, wait_until='domcontentloaded')
            time.sleep(3)
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(2)

            links = page.query_selector_all('a[href*="/reel/"], a[href*="/p/"]')
            print(f"#{tag}: found {len(links)} links", flush=True)

            for link in links[:15]:
                href = link.get_attribute("href") or ""
                text = link.inner_text().strip().replace('\n', ' ')
                m = re.search(r'/(?:reel|p)/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1)
                views = parse_views_count(text)
                discovered_creators_reels.append({
                    "tag": tag,
                    "code": code,
                    "views_text": text,
                    "parsed_views": views,
                    "url": f"https://www.instagram.com/reel/{code}/"
                })
        except Exception as e:
            print(f"Error on #{tag}: {e}", flush=True)

    browser.close()

with open("tag_hunted_reels.json", "w", encoding="utf-8") as f:
    json.dump(discovered_creators_reels, f, indent=2)

print(f"Total hunted from tags: {len(discovered_creators_reels)}", flush=True)

