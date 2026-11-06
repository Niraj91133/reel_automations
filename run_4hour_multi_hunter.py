import os
import sys
import time
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath('reel_automations-main')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.database import ChannelDatabase
from core.niche_hunter import get_channel_cookies
from core.niche_scout import NICHE_DISCOVERY_PROFILES, parse_views_count

CHANNELS = [
    {
        "id": "startup_road",
        "display": "💼 Startup Road",
        "handle": "@startup_road"
    },
    {
        "id": "trading_pulse",
        "display": "📈 Trading Road",
        "handle": "@trading_road_"
    },
    {
        "id": "healthy_diet",
        "display": "🥗 Gudtree",
        "handle": "@gudtree_"
    },
    {
        "id": "viral_finds",
        "display": "🛍️ Trending Road",
        "handle": "@trending_road"
    }
]

def hunt_single_fresh_reel(page, channel_id, db):
    """
    Finds exactly 1 fresh viral reel (>25k views) for the specified channel.
    Checks top niche creators and hashtags.
    """
    profile = NICHE_DISCOVERY_PROFILES.get(channel_id, {})
    creators = list(profile.get("creators", []))
    random.shuffle(creators)

    # 1. Check top creators
    for creator in creators[:6]:
        try:
            url = f"https://www.instagram.com/{creator}/reels/"
            page.goto(url, timeout=25000, wait_until='domcontentloaded')
            page.wait_for_timeout(4000)

            links = page.query_selector_all('a[href*="/reel/"]')
            for link in links[:12]:
                href = link.get_attribute("href") or ""
                m = re.search(r'/reel/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1).strip()
                if db.is_reel_processed(code) or db.is_reel_hunted(code):
                    continue

                card_text = link.inner_text().strip().replace('\n', ' ')
                views_num = parse_views_count(card_text)
                if 'M' in card_text.upper() or views_num >= 25000 or not card_text:
                    return {
                        "shortcode": code,
                        "url": f"https://www.instagram.com/reel/{code}/",
                        "creator": f"@{creator}",
                        "views": card_text or "Viral"
                    }
        except Exception:
            pass

    # 2. Check hashtags
    cfg = get_channel_config(channel_id)
    hashtags = list(cfg.get("hunting_settings", {}).get("hashtags", []))
    random.shuffle(hashtags)
    for tag in hashtags[:4]:
        clean_tag = tag.replace('#', '').strip()
        try:
            url = f"https://www.instagram.com/explore/tags/{clean_tag}/"
            page.goto(url, timeout=25000, wait_until='domcontentloaded')
            page.wait_for_timeout(4000)
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(1500)

            links = page.query_selector_all('a[href*="/reel/"], a[href*="/p/"]')
            for link in links[:10]:
                href = link.get_attribute("href") or ""
                m = re.search(r'/(?:reel|p)/([^/?]+)', href)
                if not m:
                    continue
                code = m.group(1).strip()
                if db.is_reel_processed(code) or db.is_reel_hunted(code):
                    continue

                card_text = link.inner_text().strip().replace('\n', ' ')
                return {
                    "shortcode": code,
                    "url": f"https://www.instagram.com/reel/{code}/",
                    "creator": f"#{clean_tag}",
                    "views": card_text or "Trending"
                }
        except Exception:
            pass

    return None

def open_raj_chat_for_channel(page, channel_id):
    """Directly opens chat with Raj for whichever channel is logged in."""
    if channel_id == "healthy_diet":
        page.goto('https://www.instagram.com/im_raaaj_/', timeout=30000, wait_until='domcontentloaded')
        page.wait_for_timeout(3500)
        btn = page.query_selector("div[role='button']:has-text('Message'), button:has-text('Message')")
        if btn:
            btn.click()
            page.wait_for_timeout(3500)
            return True
    else:
        # startup_road, trading_pulse, and viral_finds direct thread
        page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=30000, wait_until='domcontentloaded')
        page.wait_for_timeout(3500)
        tb = page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]')
        if tb:
            return True

        # Fallback to inbox
        page.goto('https://www.instagram.com/direct/inbox/', timeout=30000, wait_until='domcontentloaded')
        page.wait_for_timeout(3500)
        elems = page.query_selector_all("span:has-text('राज')")
        if elems:
            elems[0].click()
            page.wait_for_timeout(3500)
            return True

    return True

def send_reel_in_raj_chat(page, reel_url):
    """Types the reel URL and sends it into the active chat."""
    try:
        tb = page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]')
        if tb:
            tb.click()
            page.wait_for_timeout(500)
            page.keyboard.type(reel_url)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
            return True
        else:
            print("Chat textbox element not found.")
    except Exception as e:
        print(f"Error typing into chat: {e}")
    return False

def run_4hour_continuous_hunt(duration_hours=4.0):
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=duration_hours)

    print("========================================================")
    print("  🚀 4-HOUR MULTI-ACCOUNT VIRAL REELS HUNTER ONLINE")
    print("========================================================")
    print(f"Start Time : {start_time.strftime('%I:%M %p')}")
    print(f"End Time   : {end_time.strftime('%I:%M %p')} (~{duration_hours:.1f} hours)")
    print(f"Target DM  : @im_raaaj_ (Raj)")
    print("Accounts   : @startup_road, @trading_road_, @gudtree_, @trending_road")
    print("Delivery   : 1 reel at a time, round-robin rotation")
    print("========================================================\n")

    chromium_args = [
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--renderer-process-limit=2",
        "--mute-audio"
    ]

    channel_stats = {ch["id"]: 0 for ch in CHANNELS}
    total_sent = 0
    cycle_count = 0

    while datetime.now() < end_time:
        cycle_count += 1
        now_str = datetime.now().strftime('%I:%M %p')
        print(f"\n--- [Cycle #{cycle_count} | {now_str}] Rotating Across 4 Accounts ---")

        for ch in CHANNELS:
            if datetime.now() >= end_time:
                break

            ch_id = ch["id"]
            display = ch["display"]
            handle = ch["handle"]
            cfg = get_channel_config(ch_id)
            db = ChannelDatabase(cfg["runtime"]["db_path"])
            cookies = get_channel_cookies(ch_id)

            if not cookies:
                print(f"⚠️ [{display}] No valid cookies found. Skipping.")
                continue

            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True, args=chromium_args)
                    ctx = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        viewport={"width": 1280, "height": 900}
                    )
                    ctx.add_cookies(cookies)
                    page = ctx.new_page()

                    # 1. Hunt 1 fresh candidate
                    candidate = hunt_single_fresh_reel(page, ch_id, db)

                    if candidate:
                        shortcode = candidate["shortcode"]
                        reel_url = candidate["url"]
                        views = candidate["views"]
                        creator = candidate["creator"]

                        # 2. Open Raj DM and send it
                        ok = open_raj_chat_for_channel(page, ch_id)
                        if ok:
                            sent = send_reel_in_raj_chat(page, reel_url)
                            if sent:
                                db.mark_reel_hunted(
                                    shortcode=shortcode,
                                    source_query=creator,
                                    views_text=views,
                                    has_comment_cta=0
                                )
                                channel_stats[ch_id] += 1
                                total_sent += 1
                                print(f"[{datetime.now().strftime('%I:%M %p')}] ✅ {display} ({handle}) sent #{channel_stats[ch_id]} to Raj: {reel_url} ({creator} | {views})")
                            else:
                                print(f"[{display}] Error: Could not type into chat textbox.")
                        else:
                            print(f"[{display}] Error: Could not open chat with Raj.")
                    else:
                        print(f"[{display}] No unhunted candidate found in this pass.")

                    browser.close()
            except Exception as e:
                print(f"[{display}] Error during cycle: {e}")

            # Natural delay between accounts (25 to 35 seconds)
            time.sleep(random.randint(25, 35))

        remaining_mins = max(0, int((end_time - datetime.now()).total_seconds() / 60))
        print(f"📊 Status: Total Sent: {total_sent} | Remaining Time: ~{remaining_mins} mins | By Channel: {channel_stats}")

    print("\n========================================================")
    print(f"🎉 4-HOUR HUNTING COMPLETED AT {datetime.now().strftime('%I:%M %p')}!")
    print(f"Total Sent: {total_sent} | Breakdown: {channel_stats}")
    print("========================================================")

if __name__ == '__main__':
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
    run_4hour_continuous_hunt(duration)
