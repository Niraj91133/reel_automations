import os
import sys
import time
import re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.niche_hunter import get_channel_cookies

cookies = get_channel_cookies("startup_road")

target_creators = [
    "kartikcreatebusiness",
    "businessidea_841",
    "ideas_logix",
    "speedgyaan",
    "ecom.deep",
    "actual.abhishek",
    "theexportdiary"
]

print("🔍 Visiting Top Hindi Business Creators to Hunt 200k+ Views & 2k+ Comment Reels...")

reels_found = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    # Block heavy media
    def block_heavy(route):
        if route.request.resource_type in ["image", "media", "font"]:
            route.abort()
        else:
            route.continue_()
    page.route("**/*", block_heavy)

    for username in target_creators:
        profile_url = f"https://www.instagram.com/{username}/"
        print(f"\nScanning @{username}...")
        try:
            page.goto(profile_url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(3)
            
            # Scroll to load reels
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(2)

            links = page.query_selector_all('a[href*="/reel/"], a[href*="/p/"]')
            print(f"Found {len(links)} links on @{username}")
            for link in links[:5]:
                href = link.get_attribute("href") or ""
                m = re.search(r'/(?:reel|p)/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1).strip()
                reels_found.append({
                    "creator": username,
                    "code": code,
                    "url": f"https://www.instagram.com/reel/{code}/"
                })
        except Exception as e:
            print(f"Error on @{username}: {e}")

    browser.close()

print(f"\nTotal Discovered Candidates: {len(reels_found)}")
for r in reels_found:
    print(r["creator"], r["url"])

