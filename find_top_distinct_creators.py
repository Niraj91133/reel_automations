import sys
import time
import re
import json
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies, parse_views_count

sys.stdout.reconfigure(encoding='utf-8')

creators = [
    "biharstory",
    "actual.abhishek",
    "speedgyaan",
    "ecom.deep",
    "kartikcreatebusiness",
    "ideas_logix",
    "businessidea_841",
    "theunpluggedmoney",
    "vyapar_jagat",
    "businessbaate",
    "franchisecanvas"
]

cookies = get_channel_cookies('startup_road')
hits = {}

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

    for handle in creators:
        url = f"https://www.instagram.com/{handle}/reels/"
        try:
            page.goto(url, timeout=20000, wait_until='domcontentloaded')
            time.sleep(2.5)

            if "login" in page.url.lower():
                print(f"Skipping @{handle}: login redirect", flush=True)
                continue

            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(1.5)

            links = page.query_selector_all('a[href*="/reel/"]')
            print(f"@{handle}: found {len(links)} reels", flush=True)

            creator_hits = []
            for link in links:
                href = link.get_attribute("href") or ""
                text = link.inner_text().strip().replace('\n', ' ')
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1)
                views = parse_views_count(text)
                if 'M' in text.upper() or views >= 200000:
                    creator_hits.append({
                        "code": code,
                        "views_text": text,
                        "parsed_views": views,
                        "url": f"https://www.instagram.com/reel/{code}/"
                    })

            if creator_hits:
                hits[handle] = creator_hits
                print(f"  -> Hits for @{handle}: {[(h['code'], h['views_text']) for h in creator_hits[:4]]}", flush=True)

        except Exception as e:
            print(f"Error on @{handle}: {e}", flush=True)

    browser.close()

with open("distinct_creators_hits.json", "w", encoding="utf-8") as f:
    json.dump(hits, f, indent=2)

print(f"\nCompleted! Creators with 200k+ reels: {list(hits.keys())}", flush=True)

