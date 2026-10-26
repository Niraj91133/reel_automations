import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import re
import sqlite3
from playwright.sync_api import sync_playwright

COOKIE_FILE = "cookies.txt"
STARTUP_THREAD_URL = "https://www.instagram.com/direct/t/101996904536119/"

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

def get_already_processed_shortcodes():
    """Fetches already processed shortcodes from reels_history.db and politics_history.db."""
    processed = set()
    for db_file, tbl in [("reels_history.db", "processed_reels"), ("politics_history.db", "processed_politics_reels")]:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                c = conn.cursor()
                c.execute(f"SELECT shortcode FROM {tbl}")
                for row in c.fetchall():
                    if row[0]:
                        processed.add(row[0].strip())
                conn.close()
            except Exception:
                pass
    return processed

def get_shared_reels_from_chat(max_count=10):
    print("Navigating to Instagram chat with @im_raaaj_ (Startup)...")
    cookies = parse_cookie_file(COOKIE_FILE)
    processed_codes = get_already_processed_shortcodes()
    print(f"Loaded {len(processed_codes)} already-processed shortcodes from history databases.")

    fresh_reels = []
    seen_in_session = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            page.goto(STARTUP_THREAD_URL, timeout=45000, wait_until="networkidle")
            time.sleep(3)

            not_now = page.query_selector("button:has-text('Not Now')")
            if not_now:
                not_now.click()
                time.sleep(1)

            # NOTE: Scan from bottom (newest messages first) upwards
            print("Scanning @im_raaaj_ chat from the BOTTOM (newest messages first)...")

            for scroll_round in range(8):
                if len(fresh_reels) >= max_count:
                    break

                cards = page.query_selector_all("div[role='button']")
                chat_cards = []
                for card in cards:
                    try:
                        box = card.bounding_box()
                        # Strict right-pane check (x > 350) and card dimensions
                        if not box or box['x'] < 350 or box['width'] < 100 or box['height'] < 150:
                            continue

                        card_text = card.inner_text().strip().replace('\n', ' ')
                        if any(skip in card_text for skip in ['Message...', 'Search', 'Send message', 'Active']):
                            continue

                        chat_cards.append((card, card_text, box['y']))
                    except Exception:
                        pass

                # Sort cards by Y descending (bottom of page to top = newest to oldest!)
                chat_cards.sort(key=lambda x: x[2], reverse=True)

                for card, card_text, y in chat_cards:
                    if len(fresh_reels) >= max_count:
                        break

                    creator = card_text.split()[0] if card_text else "creator"

                    try:
                        card.click(timeout=2000)
                        time.sleep(1.2)

                        cur_url = page.url
                        m = re.search(r"/(?:reel|p)/([^/?]+)", cur_url)
                        if m:
                            code = m.group(1)
                            if code not in seen_in_session:
                                seen_in_session.add(code)
                                is_already_done = code in processed_codes
                                if not is_already_done:
                                    fresh_reels.append({
                                        "shortcode": code,
                                        "url": f"https://www.instagram.com/reel/{code}/",
                                        "creator": creator
                                    })
                                    print(f"🎯 [{len(fresh_reels)}/{max_count}] Verified Fresh Startup Reel: https://www.instagram.com/reel/{code}/ (By @{creator})")
                                else:
                                    print(f"⏩ Skipping already processed startup reel: {code} (By @{creator})")

                            # Close reel modal dialog
                            close_btn = page.query_selector("svg[aria-label='Close']")
                            if close_btn:
                                close_btn.click()
                                time.sleep(0.4)
                            else:
                                page.keyboard.press("Escape")
                                time.sleep(0.3)
                        else:
                            page.keyboard.press("Escape")
                            time.sleep(0.2)
                    except Exception:
                        pass

                if len(fresh_reels) >= max_count:
                    break

                # Scroll upwards slightly to load preceding messages if more are needed
                page.mouse.move(600, 400)
                page.mouse.wheel(0, -1400)
                time.sleep(1.0)

        except Exception as e:
            print("Chat extraction error:", e)
        finally:
            browser.close()

    print(f"\nTotal Verified Fresh Startup Reels from @im_raaaj_ chat: {len(fresh_reels)}")
    return fresh_reels

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    reels = get_shared_reels_from_chat(limit)
    print("Found total startup reels:", len(reels))
