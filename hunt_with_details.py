import os
import sys
import json
import time
import re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.niche_hunter import get_channel_cookies

cookies = get_channel_cookies("startup_road")

QUERIES = [
    "small manufacturing machine business comment",
    "chhoti machine se dhandha comment supplier",
    "low investment business ideas hindi comment",
    "scrap recycling business model hindi comment"
]

results = []
seen = set()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    # Block images/media to speed up
    def block_heavy(route):
        if route.request.resource_type in ["image", "media", "font"]:
            route.abort()
        else:
            route.continue_()
    page.route("**/*", block_heavy)

    for q in QUERIES:
        if len(results) >= 10:
            break
        print(f"🔍 Searching: '{q}'...")
        encoded = q.replace(" ", "%20")
        url = f"https://www.instagram.com/explore/search/keyword/?q={encoded}"
        try:
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(3)
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(2)

            links = page.query_selector_all('a[href*="/reel/"]')
            for a in links:
                if len(results) >= 10:
                    break
                href = a.get_attribute("href") or ""
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1).strip()
                if code in seen:
                    continue
                seen.add(code)

                # Click or read card text
                card_text = a.inner_text().strip().replace('\n', ' ')
                results.append({
                    "shortcode": code,
                    "url": f"https://www.instagram.com/reel/{code}/",
                    "query": q,
                    "preview": card_text or "Trending Video"
                })
        except Exception as e:
            print(f"Search note on '{q}': {e}")

    # Now let's visit each of the top candidates to grab exact caption & creator
    print(f"\n📖 Inspecting captions for {len(results)} discovered reels...")
    detailed = []
    for item in results:
        code = item["shortcode"]
        reel_url = item["url"]
        try:
            page.goto(reel_url, timeout=25000, wait_until='domcontentloaded')
            time.sleep(2)
            
            # Find creator
            creator_el = page.query_selector('header a[role="link"], h2 a, a[href^="/"][role="link"]')
            creator = creator_el.inner_text().strip() if creator_el else "creator"

            # Find caption
            caption_el = page.query_selector('h1, div[role="main"] span, article span')
            caption = ""
            if caption_el:
                caption = caption_el.inner_text().strip().replace('\n', ' ')
            
            detailed.append({
                "shortcode": code,
                "url": reel_url,
                "creator": creator,
                "query": item["query"],
                "caption": caption[:180] if caption else "Practical Business Reel"
            })
        except Exception as e:
            detailed.append({
                "shortcode": code,
                "url": reel_url,
                "creator": "creator",
                "query": item["query"],
                "caption": "High-Value Ground Business Reel"
            })

    browser.close()

print("\n🎯 === 10 HUNTED GROUND-LEVEL BUSINESS REELS ===")
for i, d in enumerate(detailed[:10], 1):
    print(f"#{i} | {d['url']}")
    print(f"   👤 Creator: @{d['creator']}")
    print(f"   🔍 Query: '{d['query']}'")
    print(f"   📝 Hook/Caption: {d['caption']}...")
    print("----------------------------------------------------------------")
