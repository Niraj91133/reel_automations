import os
import sys
import time
import re
import sqlite3
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.niche_hunter import get_channel_cookies

TRADING_CREATORS = [
    "boomingbulls",
    "poweroftocks",
    "ghanshyamtech",
    "tradewithmayank",
    "neerajjoshi",
    "pushkarrajthakur"
]

cookies = get_channel_cookies("trading_road24")
db_path = BASE_DIR / "databases" / "trading_road24_history.db"

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT shortcode FROM processed_reels")
processed = set(r[0] for r in c.fetchall())

c.execute("SELECT shortcode FROM hunted_reels")
existing_hunted = set(r[0] for r in c.fetchall())

print(f"Current trading DB state: {len(processed)} processed, {len(existing_hunted)} hunted.")

discovered = []

chromium_args = [
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--renderer-process-limit=2",
    "--blink-settings=imagesEnabled=false",
    "--mute-audio"
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=chromium_args)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    if cookies:
        ctx.add_cookies(cookies)
    page = ctx.new_page()

    for creator in TRADING_CREATORS:
        if len(discovered) >= 30:
            break
        url = f"https://www.instagram.com/{creator}/reels/"
        print(f"Scouting @{creator} reels: {url} ...")
        try:
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(2000)

            links = page.query_selector_all('a[href*="/reel/"]')
            print(f"  Found {len(links)} reel elements on @{creator}")
            for l in links[:15]:
                href = l.get_attribute("href") or ""
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                sc = m.group(1).strip()
                if sc in processed or sc in existing_hunted or any(d[0] == sc for d in discovered):
                    continue

                card_text = l.inner_text().strip().replace('\n', ' ')
                views_str = card_text if card_text else "50K+"

                discovered.append((sc, f"@{creator}", "creator_scout", views_str, 1, 1))
                print(f"    + Discovered trading reel [{sc}] by @{creator} ({views_str})")
                if len(discovered) >= 30:
                    break
        except Exception as e:
            print(f"  Error checking @{creator}: {e}")

    browser.close()

print(f"\nTotal new trading reels discovered: {len(discovered)}")

if discovered:
    c.executemany("""
        INSERT OR IGNORE INTO hunted_reels 
        (shortcode, creator, source_query, views_text, has_comment_cta, sent_to_raj)
        VALUES (?, ?, ?, ?, ?, ?)
    """, discovered)
    conn.commit()
    print(f"✅ Successfully saved {len(discovered)} trading reels to {db_path} hunted_reels!")

conn.close()
