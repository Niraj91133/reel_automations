import os
import sys
import time
import re
import json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.niche_hunter import get_channel_cookies, parse_views_count
import sqlite3
conn = sqlite3.connect("database/startup_road.db")
c = conn.cursor()
posted_shortcodes = set(row[0] for row in c.execute("SELECT shortcode FROM processed_reels"))
conn.close()

print(f"Total already posted reels in startup_road DB: {len(posted_shortcodes)}")

cookies = get_channel_cookies("startup_road")

target_creators = [
    "kartikcreatebusiness",
    "businessidea_841",
    "ideas_logix",
    "speedgyaan",
    "ecom.deep",
    "actual.abhishek",
    "theexportdiary",
    "business_factory_",
    "vyapari_baba",
    "laghu_udyog_bharat"
]

verified_reels = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    for username in target_creators:
        url = f"https://www.instagram.com/{username}/reels/"
        print(f"\n==========================================")
        print(f"Checking @{username}/reels/ ...")
        try:
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(3)
            
            # Check if page loaded
            if "login" in page.url.lower():
                print(f"Redirected to login on @{username}")
                continue

            # Scroll down to load more reels
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(1.5)

            # Find all reel items on grid
            # Reel grid items usually have a link href containing /reel/
            reel_elements = page.query_selector_all('a[href*="/reel/"]')
            print(f"Found {len(reel_elements)} reel elements on @{username}")

            for elem in reel_elements:
                href = elem.get_attribute("href") or ""
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1).strip()
                
                # Check duplicate
                if code in posted_shortcodes:
                    continue
                
                # Extract view count from the element text
                text_content = elem.inner_text().strip()
                lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                
                view_str = ""
                for line in lines:
                    if any(c in line for c in ['K', 'M', 'k', 'm']) or re.search(r'\d+', line):
                        view_str = line
                        break
                
                views = parse_views_count(view_str)
                print(f"  Reel: {code} | Text: {text_content!r} | Parsed Views: {views}")

                # If views >= 200k (or even 150k as candidate)
                if views >= 180000 or (not views and len(verified_reels) < 15):
                    verified_reels.append({
                        "creator": username,
                        "code": code,
                        "url": f"https://www.instagram.com/reel/{code}/",
                        "raw_view_str": view_str,
                        "views": views
                    })
        except Exception as e:
            print(f"Error checking @{username}: {e}")

    browser.close()

print(f"\nTotal potential viral reels gathered: {len(verified_reels)}")
with open("candidate_viral_reels.json", "w", encoding="utf-8") as f:
    json.dump(verified_reels, f, indent=2)
