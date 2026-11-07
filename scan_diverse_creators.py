import sys
import time
import re
import json
import sqlite3
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

from core.niche_hunter import get_channel_cookies, parse_views_count

conn = sqlite3.connect("database/startup_road.db")
c = conn.cursor()
posted_shortcodes = set(row[0] for row in c.execute("SELECT shortcode FROM processed_reels"))
conn.close()

# List of distinct candidate Hindi business & machinery creators
candidate_creators = [
    "actual.abhishek",
    "speedgyaan",
    "kartikcreatebusiness",
    "theexportdiary",
    "ecom.deep",
    "franchise_batao",
    "business_factory_",
    "vyapari_baba",
    "laghu_udyog_bharat",
    "business_mantras",
    "startup_pedia",
    "startup_gyaan",
    "entrepreneur_hindi",
    "bhupendrakumar_official",
    "ideas_logix",
    "businessidea_841"
]

cookies = get_channel_cookies('startup_road')
creator_reels = {}

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

    for handle in candidate_creators:
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

            found_reels = []
            for link in links:
                href = link.get_attribute("href") or ""
                text = link.inner_text().strip().replace('\n', ' ')
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1)
                if code in posted_shortcodes:
                    continue
                
                # Check views
                views = parse_views_count(text)
                if 'M' in text.upper() or 'K' in text.upper() or views > 100000:
                    found_reels.append({"code": code, "views_text": text, "parsed_views": views})

            if found_reels:
                creator_reels[handle] = found_reels
                print(f"  -> Top hits on @{handle}: {[(r['code'], r['views_text']) for r in found_reels[:3]]}", flush=True)

        except Exception as e:
            print(f"Error on @{handle}: {e}", flush=True)

    browser.close()

with open("diverse_creators_found.json", "w", encoding="utf-8") as f:
    json.dump(creator_reels, f, indent=2)

print("\nScan completed! Found creators:", list(creator_reels.keys()), flush=True)

