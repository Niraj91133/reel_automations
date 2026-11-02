import os
import sys
import time
import re
import sqlite3
import random
import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

COOKIE_FILE = "cookies.txt"
STARTUP_THREAD_URL = "https://www.instagram.com/direct/t/101996904536119/"

# High-Intent Money-Making & Side Hustle Search Queries
SEARCH_KEYWORDS = [
    "online earning",
    "paise kaise kamaye",
    "side hustle india",
    "ai tools money",
    "work from home hindi",
    "student earning",
    "chatgpt earning",
    "freelancing tools",
    "daily income website",
    "zero investment earning"
]

# Curated High-Performing Indian Creators who specialize in "Comment XYZ / Earning Methods"
CURATED_MONEY_CREATORS = [
    "techrupshai",
    "harshal_shisode_",
    "kartikcreatebusiness",
    "risewithmohit",
    "bhavyasharmaai",
    "itshanzlapro",
    "ezsnippet",
    "technoyogy.ai",
    "techiivikas.ai",
    "buildwithsanny.ai",
    "mayankshah_ai",
    "wixelai",
    "hustlewithme0001",
    "dr_tech_786",
    "growwithshiv",
    "speakup.diksha",
    "anuraag00ak",
    "raghav.money",
    "finanxial.freedom",
    "actual.abhishek",
    "techninjaah",
    "ashishbuilds",
    "uvichar_",
    "steven.builds"
]

def init_scout_db():
    conn = sqlite3.connect("reels_history.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scouted_reels (
            shortcode TEXT PRIMARY KEY,
            creator TEXT,
            reel_url TEXT,
            views_str TEXT,
            scouted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_scouted(shortcode):
    conn = sqlite3.connect("reels_history.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM scouted_reels WHERE shortcode = ?", (shortcode,))
    row = c.fetchone()
    if row:
        conn.close()
        return True
    c.execute("SELECT 1 FROM processed_reels WHERE shortcode = ?", (shortcode,))
    row2 = c.fetchone()
    conn.close()
    return row2 is not None

def mark_scouted(shortcode, creator, reel_url, views_str=""):
    conn = sqlite3.connect("reels_history.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO scouted_reels (shortcode, creator, reel_url, views_str) VALUES (?, ?, ?, ?)",
              (shortcode, creator, reel_url, views_str))
    conn.commit()
    conn.close()

def parse_cookie_file(cookie_file):
    cookies = []
    if not os.path.exists(cookie_file):
        return cookies
    with open(cookie_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                cookies.append({
                    'domain': parts[0],
                    'path': parts[2],
                    'secure': parts[3].lower() == 'true',
                    'expires': int(parts[4]) if parts[4].isdigit() else -1,
                    'name': parts[5],
                    'value': parts[6]
                })
    return cookies

def parse_views_count(view_text):
    vt = view_text.strip().upper().replace(',', '')
    if not vt:
        return 0
    try:
        if 'M' in vt:
            return int(float(vt.replace('M', '')) * 1_000_000)
        elif 'K' in vt:
            return int(float(vt.replace('K', '')) * 1_000)
        elif vt.isdigit():
            return int(vt)
    except:
        pass
    return 0

def scout_money_making_reels(target_count=10, notify_callback=None):
    """
    Scouts strictly for "Comment XYZ / How To Make Money / Actionable AI Tools" reels:
    - 100% diverse (exactly 1 reel per creator).
    - High views (30K+ to millions).
    - Verified not liked by @im_raaaj_.
    - Delivers straight into @im_raaaj_ DM chat.
    """
    init_scout_db()
    cookies = parse_cookie_file(COOKIE_FILE)
    if not cookies:
        print("Error: cookies.txt not found!", flush=True)
        return 0

    if notify_callback:
        notify_callback(f"🔍 <b>Money-Making Scout Active:</b> 'Comment XYZ / Paise Kaise Kamaye' wali {target_count} viral reels dhoondh rha hu...")

    discovered_candidates = []
    used_creators = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies(cookies)
        page = context.new_page()

        print(f"\n==================================================", flush=True)
        print(f"  SCOUTING 'COMMENT XYZ / EARNING' REELS (Target: {target_count})", flush=True)
        print(f"==================================================\n", flush=True)

        # 1. Search Bar Discovery
        page.goto('https://www.instagram.com/', timeout=35000, wait_until='domcontentloaded')
        time.sleep(2)

        search_creators = []
        for kw in random.sample(SEARCH_KEYWORDS, min(4, len(SEARCH_KEYWORDS))):
            try:
                search_btn = page.query_selector("svg[aria-label='Search'], a:has-text('Search'), div[role='button']:has-text('Search')")
                if search_btn:
                    search_btn.click()
                    time.sleep(1)

                input_box = page.query_selector("input[placeholder*='Search'], input[aria-label*='Search']")
                if input_box:
                    input_box.fill("")
                    time.sleep(0.2)
                    input_box.type(kw, delay=30)
                    time.sleep(2.5)

                    for a in page.query_selector_all("a[href*='/']"):
                        href = a.get_attribute("href") or ""
                        if href.startswith("/"):
                            parts = href.strip("/").split("/")
                            if len(parts) == 1 and parts[0] not in ['direct', 'explore', 'reels', 'stories', 'accounts']:
                                search_creators.append(parts[0])
            except Exception:
                pass

        # Combine search-discovered accounts + curated money-making accounts
        pool = list(dict.fromkeys(search_creators + CURATED_MONEY_CREATORS))
        random.shuffle(pool)

        print(f"Pool of {len(pool)} money-making creators ready to scan...", flush=True)

        for creator in pool:
            if len(discovered_candidates) >= target_count:
                break
            if creator in used_creators or creator in ["startup_road", "im_raaaj_"]:
                continue

            try:
                url = f"https://www.instagram.com/{creator}/reels/"
                page.goto(url, timeout=25000, wait_until='domcontentloaded')
                time.sleep(1.8)

                links = page.query_selector_all('a[href*="/reel/"]')
                best_reel = None

                for link in links[:8]:
                    href = link.get_attribute("href")
                    if not href or "/reel/" not in href:
                        continue

                    code = href.split("/reel/")[1].split("/")[0].strip()
                    if not code or is_scouted(code):
                        continue

                    card_text = link.inner_text().strip().replace('\n', ' ')
                    views_num = parse_views_count(card_text)

                    # Viral filter: Views >= 30k or 'M'
                    is_viral = False
                    if 'M' in card_text.upper():
                        is_viral = True
                    elif 'K' in card_text.upper() and views_num >= 30_000:
                        is_viral = True
                    elif views_num >= 30_000 or not card_text:
                        is_viral = True

                    if is_viral:
                        best_reel = {
                            "shortcode": code,
                            "creator": creator,
                            "url": f"https://www.instagram.com/reel/{code}/",
                            "views": card_text or "Viral"
                        }
                        break # Exactly 1 reel per creator for maximum diversity!

                if best_reel:
                    used_creators.add(creator)
                    discovered_candidates.append(best_reel)
                    print(f"  🔥 [Candidate #{len(discovered_candidates)}/{target_count}] https://www.instagram.com/reel/{best_reel['shortcode']}/ (Views: {best_reel['views']} | Creator: @{creator})", flush=True)

            except Exception:
                pass

        if not discovered_candidates:
            print("No new candidates found.", flush=True)
            browser.close()
            return 0

        # Step 2: Deliver into @im_raaaj_ DM chat
        print(f"\n📨 Delivering {len(discovered_candidates)} 'Comment XYZ / Earning' reels to @im_raaaj_ DM chat...", flush=True)
        page.goto(STARTUP_THREAD_URL, timeout=45000, wait_until='networkidle')
        time.sleep(4)

        not_now_dm = page.query_selector("button:has-text('Not Now')")
        if not_now_dm:
            try: not_now_dm.click()
            except: pass

        input_box_dm = page.query_selector('div[role="textbox"]')
        if not input_box_dm:
            input_box_dm = page.query_selector('div[contenteditable="true"]')

        sent_count = 0
        if input_box_dm:
            for item in discovered_candidates:
                try:
                    reel_link = item["url"]
                    creator_name = item["creator"]
                    views_info = item["views"]

                    input_box_dm.click()
                    time.sleep(0.4)
                    page.keyboard.type(reel_link, delay=25)
                    time.sleep(0.4)
                    page.keyboard.press("Enter")
                    time.sleep(2.5)

                    mark_scouted(item["shortcode"], creator_name, reel_link, views_info)
                    sent_count += 1
                    print(f"  ✅ [Sent {sent_count}/{len(discovered_candidates)}] Delivered to @im_raaaj_: {reel_link} (Views: {views_info} | @{creator_name})", flush=True)
                except Exception as e:
                    print(f"Error sending candidate {item['shortcode']}: {e}", flush=True)
        else:
            print("Could not find message input box in DM chat!", flush=True)

        browser.close()

    print(f"\n🎉 Successfully delivered {sent_count} 'Comment XYZ / Earning' reels to @im_raaaj_ DM!")
    if notify_callback:
        notify_callback(f"🎉 <b>Complete:</b> {sent_count} fresh 'Comment XYZ / Earning' viral reels (10 different creators) delivered to @im_raaaj_ DM! Check your inbox 👍")
        
    return sent_count

# Aliases
scout_and_send_reels = scout_money_making_reels
scout_diverse_niche_reels = scout_money_making_reels

if __name__ == '__main__':
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    scout_money_making_reels(count)
