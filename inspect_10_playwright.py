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

shortcodes = [
    'DWzFpCsilRP', 'Da1uZcdzVdP', 'DUFzBIMksDy', 'DXo2O-SkhRu',
    'DZP97Uxycpf', 'DYwxmjYvPgu', 'DdjgKMQB12M', 'DfPW7VzSnhx',
    'DYuMCAZzJX6', 'DYpCgIEtiqc'
]

print("🔍 Inspecting 10 Hunted Reels using Authenticated Playwright...")

detailed = []
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

    for i, code in enumerate(shortcodes, 1):
        url = f"https://www.instagram.com/reel/{code}/"
        try:
            page.goto(url, timeout=25000, wait_until='domcontentloaded')
            time.sleep(2)

            # Find creator
            creator_el = page.query_selector('header a[role="link"], h2 a, a[href^="/"][role="link"]')
            creator = creator_el.inner_text().strip() if creator_el else "creator"

            # Find caption
            caption_el = page.query_selector('h1, div[role="main"] span, article span')
            caption = caption_el.inner_text().strip().replace('\n', ' ') if caption_el else ""

            # Check for comment cta
            has_cta = any(k in caption.lower() for k in ['comment', 'dm', 'link', 'bhejo', 'supplier', 'details'])

            detailed.append({
                "shortcode": code,
                "url": url,
                "creator": creator,
                "caption": caption[:160] if caption else "Small Business Setup",
                "has_cta": has_cta
            })
            print(f"[{i}/10] Fetched: @{creator} | {url}")
        except Exception as e:
            print(f"[{i}/10] Error on {code}: {e}")

    browser.close()

print("\n========================================================")
print("  🎯 10 HUNTED REELS (FOR USER REVIEW - NOT SENT TO DM)")
print("========================================================\n")

for i, d in enumerate(detailed, 1):
    print(f"#{i} | {d['url']}")
    print(f"   👤 Creator: @{d['creator']}")
    print(f"   📝 Hook: {d['caption']}...")
    print(f"   💬 Comment CTA Detected: {'✅ YES' if d['has_cta'] else '❌ NO'}")
    print()
