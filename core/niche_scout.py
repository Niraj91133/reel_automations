import os
import sys
import time
import random
import sqlite3
import gc
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

COOKIE_FILE = "cookies.txt"
STARTUP_THREAD_URL = "https://www.instagram.com/direct/t/101996904536119/"

NICHE_DISCOVERY_PROFILES = {
    "startup_road": {
        "display_name": "Startup Road",
        "keywords": [
            "startup lessons hindi",
            "business podcast hindi",
            "founder advice india",
            "startup revenue secrets",
            "business case study hindi"
        ],
        "creators": [
            "rajshamani",
            "warikoo",
            "theranveerallahbadia",
            "financewithsharan",
            "growthx_club",
            "learnwithjaspal",
            "thethinkschool",
            "anuragsinghinvestor"
        ]
    },
    "healthy_diet": {
        "display_name": "Gudtree (Diet & Snacks)",
        "keywords": [
            "healthy snacks india",
            "food label truth hindi",
            "palm oil in food reality",
            "clean eating snacks",
            "diet knowledge hindi",
            "protein snacks review"
        ],
        "creators": [
            "foodpharmer",
            "dr.pal.manickam",
            "lukecoutinho",
            "nutritionbylovneet",
            "gunjanoutspeaks",
            "dietician_shreya",
            "thewholetruthfoods",
            "simrun.chopra"
        ]
    },
    "trading_pulse": {
        "display_name": "Trading Road",
        "keywords": [
            "price action hindi",
            "candlestick pattern trading",
            "trading psychology rules",
            "risk management trading",
            "support resistance trading"
        ],
        "creators": [
            "boomingbulls",
            "poweroftocks",
            "ghanshyamtech",
            "artofoptionlearning",
            "pushkarrajthakur",
            "tradewithmayank",
            "neerajjoshi"
        ]
    },
    "viral_finds": {
        "display_name": "Trending Road (Viral Gadgets)",
        "keywords": [
            "amazon finds under 500",
            "cool smart gadgets india",
            "problem solving gadget",
            "viral amazon products",
            "useful gadgets home"
        ],
        "creators": [
            "techielashit",
            "amazon_finds_india",
            "smartgadgets_trend",
            "trakintech",
            "gadgets_guru_official",
            "coolgadgetsofficial"
        ]
    }
}

ORDERED_CHANNELS = ["startup_road", "healthy_diet", "trading_pulse", "viral_finds"]

def get_channel_cookie_file(channel_id):
    """
    Resolves account-specific cookie file for Option 2:
    e.g. cookies/healthy_diet_cookies.txt for @gudtree_
         cookies/trading_pulse_cookies.txt for @trading_road_
         cookies/viral_finds_cookies.txt for @trending_road
         cookies/startup_road_cookies.txt for @startup_road
    Falls back to root cookies.txt if account cookie not found.
    """
    candidates = [
        f"cookies/{channel_id}_cookies.txt",
        f"cookies_{channel_id}.txt",
        f"{channel_id}_cookies.txt",
        COOKIE_FILE
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return COOKIE_FILE

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

def init_scout_table():
    """Initializes scouted_reels history table."""
    try:
        conn = sqlite3.connect("reels_history.db")
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS scouted_reels (
                shortcode TEXT PRIMARY KEY,
                creator TEXT,
                reel_url TEXT,
                views_str TEXT,
                niche TEXT,
                scouted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Check if niche column exists; if not, add it
        c.execute("PRAGMA table_info(scouted_reels)")
        cols = [r[1] for r in c.fetchall()]
        if "niche" not in cols:
            try:
                c.execute("ALTER TABLE scouted_reels ADD COLUMN niche TEXT")
            except:
                pass
        conn.commit()
        conn.close()
    except Exception as e:
        pass

def mark_scouted(shortcode, creator, reel_url, views_str="", niche=""):
    """Marks a shortcode as scouted in history db to avoid sending it again."""
    init_scout_table()
    try:
        conn = sqlite3.connect("reels_history.db")
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO scouted_reels (shortcode, creator, reel_url, views_str, niche)
            VALUES (?, ?, ?, ?, ?)
        """, (shortcode, creator, reel_url, views_str, niche))
        conn.commit()
        conn.close()
    except Exception as e:
        try:
            conn = sqlite3.connect("reels_history.db")
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO scouted_reels (shortcode, creator, reel_url, views_str) VALUES (?, ?, ?, ?)",
                      (shortcode, creator, reel_url, views_str))
            conn.commit()
            conn.close()
        except:
            pass

def is_shortcode_scouted(shortcode):
    """Checks if reel was already scouted or processed across any channel DB."""
    # Check scouted_reels
    if os.path.exists("reels_history.db"):
        try:
            conn = sqlite3.connect("reels_history.db")
            c = conn.cursor()
            c.execute("SELECT 1 FROM scouted_reels WHERE shortcode = ?", (shortcode,))
            if c.fetchone():
                conn.close()
                return True
            conn.close()
        except:
            pass

    # Check processed_reels in all DBs
    db_paths = [
        "reels_history.db",
        "politics_history.db",
        "databases/startup_road_history.db",
        "databases/healthy_diet_history.db",
        "databases/trading_pulse_history.db",
        "databases/viral_finds_history.db"
    ]
    for db_name in db_paths:
        if os.path.exists(db_name):
            try:
                conn = sqlite3.connect(db_name)
                c = conn.cursor()
                c.execute("SELECT 1 FROM processed_reels WHERE shortcode = ?", (shortcode,))
                if c.fetchone():
                    conn.close()
                    return True
                conn.close()
            except:
                pass
    return False

def parse_views_count(view_text):
    vt = (view_text or "").strip().upper().replace(',', '')
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

def scout_and_send_single_account(channel_id, target_count=10, notify_telegram=True):
    """
    Lightweight, Anti-Crash Viral Reel Scout for a SINGLE account:
    - Blocks images/media/fonts in Chromium: uses ~90MB RAM instead of 2GB+
    - Finds up to target_count fresh viral reels (allows up to 2-3 per top creator)
    - Delivers links to @im_raaaj_ DM chat with gentle 2.5s pauses
    - Completely terminates browser and cleans RAM when finished
    """
    if channel_id not in NICHE_DISCOVERY_PROFILES:
        print(f"❌ Unknown account ID: {channel_id}")
        return 0

    init_scout_table()
    cookie_file = get_channel_cookie_file(channel_id)
    cookies = parse_cookie_file(cookie_file)
    if not cookies:
        print(f"❌ Error: Cookie file missing for [{channel_id}] (Tried: {cookie_file}).")
        return 0

    profile = NICHE_DISCOVERY_PROFILES[channel_id]
    display_name = profile["display_name"]
    creators = list(profile["creators"])
    random.shuffle(creators)

    print(f"\n{'='*60}")
    print(f"🎯 STARTING BATCH: [{display_name}] (ID: {channel_id})")
    print(f"   Target: {target_count} Viral Reels")
    print(f"   Sender Session: Using {cookie_file}")
    print(f"   Creators: {', '.join(creators[:4])}... ({len(creators)} total)")
    print(f"{'='*60}")

    discovered_candidates = []
    discovered_codes = set()
    max_per_creator = max(3, (target_count // max(1, len(creators))) + 2)

    # Launch lightweight Chromium instance
    chromium_args = [
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--renderer-process-limit=2",
        "--blink-settings=imagesEnabled=false",
        "--mute-audio",
        "--disable-background-networking"
    ]

    browser = None
    sent_count = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=chromium_args)
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900}
            )
            ctx.add_cookies(cookies)
            page = ctx.new_page()

            # Anti-Crash Memory Saver: Abort all heavy images, video media, and webfonts
            def block_heavy_assets(route):
                if route.request.resource_type in ["image", "media", "font"]:
                    route.abort()
                else:
                    route.continue_()
            page.route("**/*", block_heavy_assets)

            print(f"🔍 Searching viral reels for [{display_name}]...")
            for creator in creators:
                if len(discovered_candidates) >= target_count:
                    break

                creator_reels_found = 0
                try:
                    url = f"https://www.instagram.com/{creator}/reels/"
                    page.goto(url, timeout=22000, wait_until='domcontentloaded')
                    time.sleep(1.5)

                    links = page.query_selector_all('a[href*="/reel/"]')
                    if len(links) < 16:
                        page.evaluate("window.scrollBy(0, 900)")
                        time.sleep(1.0)
                        links = page.query_selector_all('a[href*="/reel/"]')

                    for link in links[:24]:
                        href = link.get_attribute("href")
                        if not href or "/reel/" not in href:
                            continue

                        code = href.split("/reel/")[1].split("/")[0].strip()
                        if not code or code in discovered_codes or is_shortcode_scouted(code):
                            continue

                        card_text = link.inner_text().strip().replace('\n', ' ')
                        views_num = parse_views_count(card_text)

                        # Viral filter: >= 25k views or 'M'
                        is_viral = False
                        if 'M' in card_text.upper():
                            is_viral = True
                        elif 'K' in card_text.upper() and views_num >= 25_000:
                            is_viral = True
                        elif views_num >= 25_000 or not card_text:
                            is_viral = True

                        if is_viral:
                            discovered_candidates.append({
                                "shortcode": code,
                                "creator": creator,
                                "niche": channel_id,
                                "url": f"https://www.instagram.com/reel/{code}/",
                                "views": card_text or "Viral"
                            })
                            discovered_codes.add(code)
                            creator_reels_found += 1
                            print(f"  🔥 [{len(discovered_candidates)}/{target_count}] Found: @{creator} -> {code} ({card_text})")

                            if len(discovered_candidates) >= target_count or creator_reels_found >= max_per_creator:
                                break
                except Exception as e_cr:
                    pass

            if not discovered_candidates:
                print(f"⚠️ No fresh viral candidates found for [{display_name}].")
                browser.close()
                return 0

            # Step 2: Deliver discovered reels to @im_raaaj_ DM chat
            # Unroute media blocker so Instagram chat renders 100% cleanly
            try:
                page.unroute("**/*")
            except:
                pass

            print(f"\n📨 Delivering {len(discovered_candidates)} viral reels for [{display_name}] to @im_raaaj_ DM...")
            page.goto(STARTUP_THREAD_URL, timeout=35000, wait_until='domcontentloaded')
            time.sleep(3)

            not_now_dm = page.query_selector("button:has-text('Not Now')")
            if not_now_dm:
                try: not_now_dm.click()
                except: pass

            try:
                page.wait_for_selector('div[role="textbox"], div[contenteditable="true"]', timeout=15000)
            except:
                pass

            # Send batch header announcement in chat
            try:
                header_box = page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]')
                if header_box:
                    header_text = f"🎯 [{display_name.upper()} - {len(discovered_candidates)} REELS BATCH]"
                    header_box.click()
                    time.sleep(0.3)
                    page.keyboard.type(header_text, delay=15)
                    time.sleep(0.8)
                    page.keyboard.press("Enter")
                    time.sleep(2.0)
            except:
                pass

            for item in discovered_candidates:
                try:
                    input_box = page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]')
                    if not input_box:
                        time.sleep(1)
                        input_box = page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]')

                    if not input_box:
                        print(f"⚠️ Input box missing, skipping {item['shortcode']}.")
                        continue

                    reel_link = item["url"]
                    input_box.click()
                    time.sleep(0.4)
                    page.keyboard.type(reel_link, delay=15)
                    time.sleep(1.0)

                    # Press Enter to send natively in Instagram chat
                    page.keyboard.press("Enter")
                    time.sleep(1.5)

                    # If text still in box, try Enter once more
                    remaining = input_box.inner_text().strip()
                    if remaining:
                        page.keyboard.press("Enter")
                        time.sleep(1.0)

                    time.sleep(2.0) # Safe pause to avoid rate limits and CPU spikes

                    mark_scouted(item["shortcode"], item["creator"], item["url"], item["views"], channel_id)
                    sent_count += 1
                    print(f"  ✅ [Sent {sent_count}/{len(discovered_candidates)}] {reel_link} (@{item['creator']})")
                except Exception as e_send:
                    print(f"  ❌ Error sending {item['shortcode']}: {e_send}")

            try:
                page.screenshot(path="scratch/last_dm_delivery.png")
            except:
                pass

            browser.close()

    except Exception as e_main:
        print(f"❌ Error during account run [{channel_id}]: {e_main}")
    finally:
        # Force complete garbage collection and memory release
        if browser:
            try: browser.close()
            except: pass
        gc.collect()

    # Step 3: Telegram Notification Summary for this Account
    if notify_telegram and sent_count > 0:
        try:
            import requests
            bot_token = "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A"
            chat_id = "711598335"
            lines = [
                f"🎯 <b>[{display_name}] REEL BATCH DELIVERED!</b>",
                f"Sent <b>{sent_count} viral reels</b> into @im_raaaj_ Instagram DM chat:\n"
            ]
            for idx, c in enumerate(discovered_candidates[:sent_count], 1):
                lines.append(f"{idx}. @{c['creator']} - {c['url']}")
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": "\n".join(lines), "parse_mode": "HTML"},
                timeout=15
            )
        except Exception as e_tg:
            pass

    print(f"🏆 [{display_name}] Finished! Delivered {sent_count} reels.\n")
    return sent_count

def run_all_accounts_sequentially(target_count_per_account=10, cooldown_sec=15):
    """
    Executes each account one-by-one:
    1. Account 1 (Startup Road) -> sends 10 reels -> closes browser -> RAM flushed
    2. Cooldown pause (15s) -> lets CPU & RAM rest
    3. Account 2 (Gudtree) -> sends 10 reels -> closes browser -> RAM flushed
    4. Cooldown pause (15s)
    5. Account 3 (Trading Road) -> sends 10 reels -> closes browser -> RAM flushed
    6. Cooldown pause (15s)
    7. Account 4 (Trending Road) -> sends 10 reels -> closes browser -> RAM flushed
    """
    print("\n" + "=" * 65)
    print("🚀 SEQUENTIAL MULTI-ACCOUNT VIRAL REEL ENGINE")
    print(f"   Quota: {target_count_per_account} reels per account")
    print(f"   Accounts: Startup Road -> Gudtree -> Trading Road -> Trending Road")
    print(f"   Anti-Crash: Isolated browser per account + RAM flush + Cooldown")
    print("=" * 65)

    total_all_sent = 0

    for idx, channel_id in enumerate(ORDERED_CHANNELS, start=1):
        disp_name = NICHE_DISCOVERY_PROFILES[channel_id]["display_name"]
        print(f"\n========================================================")
        print(f"▶ STEP [{idx}/{len(ORDERED_CHANNELS)}]: Processing Account [{disp_name}]")
        print(f"========================================================")

        sent = scout_and_send_single_account(
            channel_id=channel_id,
            target_count=target_count_per_account,
            notify_telegram=True
        )
        total_all_sent += sent

        # Cooldown between accounts so system CPU & RAM reset back to zero
        if idx < len(ORDERED_CHANNELS):
            print(f"\n❄️ [SYSTEM COOLDOWN] Account [{disp_name}] complete ({sent} reels sent).")
            print(f"   Pausing {cooldown_sec}s to flush system RAM & CPU before next account...")
            for remaining in range(cooldown_sec, 0, -1):
                sys.stdout.write(f"\r   ⏳ Cooldown remaining: {remaining:2d} seconds...")
                sys.stdout.flush()
                time.sleep(1)
            print("\r   ✅ System ready! Starting next account...                \n")

    print("\n" + "=" * 65)
    print(f"🎉 ALL 4 ACCOUNTS COMPLETED! Total viral reels sent: {total_all_sent}")
    print("=" * 65)
    return total_all_sent

def scout_and_send_to_imraj(target_count=10, specific_niche=None, notify_telegram=True):
    """Backward compatible entrypoint."""
    if specific_niche and specific_niche in NICHE_DISCOVERY_PROFILES:
        return scout_and_send_single_account(specific_niche, target_count=target_count, notify_telegram=notify_telegram)
    else:
        return run_all_accounts_sequentially(target_count_per_account=target_count)

if __name__ == '__main__':
    # Parse CLI arguments cleanly
    # Usage:
    #   python core/niche_scout.py 10 all
    #   python core/niche_scout.py 10 startup_road
    #   python core/niche_scout.py startup_road 10
    args = sys.argv[1:]
    target_count = 10
    target_channel = "all"

    for a in args:
        if a.isdigit():
            target_count = int(a)
        elif a.lower() in NICHE_DISCOVERY_PROFILES:
            target_channel = a.lower()
        elif a.lower() == "all":
            target_channel = "all"

    if target_channel == "all":
        run_all_accounts_sequentially(target_count_per_account=target_count)
    else:
        scout_and_send_single_account(target_channel, target_count=target_count)
