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

TARGET_TAGS = [
    ("manufacturingbusiness", "Chhoti Machines & Manufacturing Setups"),
    ("lowinvestmentbusiness", "Kam Lagat Me Apna Dhandha"),
    ("businessideas", "High-Margin Offline Arbitrage"),
    ("franchisebusiness", "Franchise & Big Brand Partnership")
]

hunted_list = []
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

    for tag, pillar in TARGET_TAGS:
        if len(hunted_list) >= 10:
            break
        tag_url = f"https://www.instagram.com/explore/tags/{tag}/"
        print(f"🔍 Hunting #{tag} ({pillar})...")
        try:
            page.goto(tag_url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(3)
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(2)

            links = page.query_selector_all('a[href*="/reel/"]')
            for a in links:
                if len(hunted_list) >= 10:
                    break
                href = a.get_attribute("href") or ""
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1).strip()
                if code in seen:
                    continue
                seen.add(code)

                # Card text on grid
                card_text = a.inner_text().strip().replace('\n', ' ')
                hunted_list.append({
                    "shortcode": code,
                    "url": f"https://www.instagram.com/reel/{code}/",
                    "tag": f"#{tag}",
                    "pillar": pillar,
                    "views_text": card_text or "Viral Trending"
                })
        except Exception as e:
            print(f"Note on #{tag}: {e}")

    browser.close()

print(f"\n✅ Total Hunted: {len(hunted_list)} reels (Zero DM sent!)")
for i, item in enumerate(hunted_list[:10], 1):
    print(f"#{i} | {item['url']} | {item['tag']} | {item['pillar']}")
