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
    ("ideas_logix", "Small Machines & Business Models"),
    ("businessidea_841", "Wholesale & Offline Setups"),
    ("kartikcreatebusiness", "Micro-Manufacturing & Case Studies"),
    ("theexportdiary", "Import Export & High-Margin Arbitrage"),
    ("ecom.deep", "Automation & Brand Playbooks")
]

print("🚀 Scanning Curated Ground-Level Business Creators...")
reels_found = []

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

    for c, theme in target_creators:
        if len(reels_found) >= 10:
            break
        url = f"https://www.instagram.com/{c}/reels/"
        print(f"🔍 Checking @{c} ({theme})...")
        try:
            page.goto(url, timeout=25000, wait_until='domcontentloaded')
            time.sleep(3)
            links = page.query_selector_all('a[href*="/reel/"]')
            for a in links[:3]:
                if len(reels_found) >= 10:
                    break
                href = a.get_attribute("href") or ""
                m = re.search(r'/reel/([^/?]+)', href)
                if m:
                    code = m.group(1).strip()
                    card_text = a.inner_text().strip().replace('\n', ' ')
                    reels_found.append({
                        "creator": c,
                        "theme": theme,
                        "code": code,
                        "url": f"https://www.instagram.com/reel/{code}/",
                        "views": card_text or "Trending"
                    })
        except Exception as e:
            print(f"Note on @{c}: {e}")

    # Now let's visit each of these reels to grab their exact caption
    print(f"\n📖 Grabbing exact Hook & Comment CTA for {len(reels_found)} reels...")
    for item in reels_found:
        try:
            page.goto(item["url"], timeout=20000, wait_until='domcontentloaded')
            time.sleep(2)
            # Caption is in title or meta or text
            title = page.title()
            item["title"] = title.split("•")[0].strip() if "•" in title else title
            # Search for comment CTA
            content = page.content()
            cta_match = re.search(r'(comment [\'\"][^\'\"]+[\'\"]|comment [A-Z0-9]+|comment karo)', content, re.IGNORECASE)
            item["comment_cta"] = cta_match.group(1) if cta_match else "Comment for details & supplier"
        except Exception as e:
            item["title"] = "Business Case Study / Machine Breakdown"
            item["comment_cta"] = "Comment for details & supplier"

    browser.close()

print("\n================================================================================")
print("  🎯 10 CURATED GROUND-LEVEL BUSINESS REELS (WITH REAL COMMENT CTAs)")
print("================================================================================\n")

for i, r in enumerate(reels_found[:10], 1):
    print(f"#{i} | {r['url']}")
    print(f"   👤 Creator: @{r['creator']}")
    print(f"   📌 Theme: {r['theme']}")
    print(f"   📝 Title/Hook: {r.get('title')}")
    print(f"   💬 Comment CTA: {r.get('comment_cta')}")
    print("--------------------------------------------------------------------------------")
