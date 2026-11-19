import os
import sys
import time
import re
import sqlite3
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.niche_hunter import get_channel_cookies

NICHE_CREATORS = {
    "trading_road24": [
        ("boomingbulls", "Trading Setups"),
        ("ghanshyamtech", "Price Action"),
        ("tradewithmayank", "BankNifty Levels"),
        ("pushkarrajthakur_official", "Stock Market Wealth")
    ],
    "marketing_road24": [
        ("actual.abhishek", "Meta Ads & Growth"),
        ("adovionlabs", "Marketing Strategy"),
        ("ecom.deep", "Ecom & Funnels"),
        ("himanshhh.ai", "AI Marketing Hacks")
    ],
    "theloan_road": [
        ("casahiljain", "Mudra & Business Loans"),
        ("financesathi", "Banking & CIBIL Rules"),
        ("thetaxbuddy", "Govt Schemes & Subsidies"),
        ("labourlawadvisor", "Business Schemes")
    ]
}

def replenish_channel_reels(channel_id, target_total=15):
    creators = NICHE_CREATORS.get(channel_id, [])
    if not creators:
        return 0

    db_path = os.path.join(BASE_DIR, f"databases/{channel_id}_history.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT shortcode FROM processed_reels")
    processed = {r[0] for r in c.fetchall()}
    c.execute("SELECT shortcode FROM hunted_reels")
    existing_hunted = {r[0] for r in c.fetchall()}

    cookies = get_channel_cookies(channel_id)
    added_count = 0

    print(f"\n🚀 Scanning Top Indian Creators for [{channel_id}]...")
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

        for creator, niche in creators:
            if added_count >= target_total:
                break
            url = f"https://www.instagram.com/{creator}/reels/"
            print(f"🔍 Checking @{creator} ({niche})...")
            try:
                page.goto(url, timeout=25000, wait_until='domcontentloaded')
                time.sleep(3)
                links = page.query_selector_all('a[href*="/reel/"]')
                for a in links[:8]:
                    if added_count >= target_total:
                        break
                    href = a.get_attribute("href") or ""
                    m = re.search(r'/reel/([^/?]+)', href)
                    if m:
                        code = m.group(1).strip()
                        if code in processed or code in existing_hunted:
                            continue
                        card_text = a.inner_text().strip().replace('\n', ' ')
                        c.execute(
                            "INSERT OR IGNORE INTO hunted_reels (shortcode, source_query, views_text, has_comment_cta, sent_to_raj, creator) VALUES (?, ?, ?, ?, ?, ?)",
                            (code, f"@{creator}", card_text or "Trending", 1, 0, f"@{creator}")
                        )
                        conn.commit()
                        existing_hunted.add(code)
                        added_count += 1
                        print(f"   + Added {code} from @{creator} ({card_text})")
            except Exception as e:
                print(f"Note on @{creator}: {e}")

        browser.close()
    conn.close()
    print(f"🎯 Total {added_count} fresh reels added to {channel_id} pool!")
    return added_count

if __name__ == '__main__':
    ch = sys.argv[1] if len(sys.argv) > 1 else "trading_road24"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    replenish_channel_reels(ch, target_total=count)
