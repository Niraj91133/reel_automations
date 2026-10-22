import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import re
from playwright.sync_api import sync_playwright

COOKIE_FILE = "cookies.txt"
STARTUP_THREAD_URL = "https://www.instagram.com/direct/t/101996904536119/"

def parse_cookie_file(cookie_file):
    cookies = []
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

def get_shared_reels_from_chat(max_count=10):
    print("Navigating to Instagram chat with @im_raaaj_ (Startup)...")
    cookies = parse_cookie_file(COOKIE_FILE)
    reels = []
    seen = set()

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

            # Scroll up to load older messages
            print("Step 1: Scrolling conversation history upwards in @im_raaaj_ chat...")
            for _ in range(6):
                page.mouse.move(600, 400)
                page.mouse.wheel(0, -3000)
                time.sleep(0.4)

            # Sweep downwards and click every reel card in right chat container
            print("Step 2: Resolving interactive reel cards downwards in @im_raaaj_ chat...")
            for step in range(12):
                if len(reels) >= max_count:
                    break

                cards = page.query_selector_all("div[role='button']")
                for card in cards:
                    if len(reels) >= max_count:
                        break
                    try:
                        box = card.bounding_box()
                        # Strict right-pane check (x > 350) and card dimensions
                        if not box or box['x'] < 350 or box['width'] < 100 or box['height'] < 150:
                            continue

                        card_text = card.inner_text().strip().replace('\n', ' ')
                        if any(skip in card_text for skip in ['Message...', 'Search', 'Send message', 'Active']):
                            continue

                        # Extract creator from card text
                        creator = card_text.split()[0] if card_text else "creator"

                        card.click(timeout=2000)
                        time.sleep(1.5)

                        cur_url = page.url
                        m = re.search(r"/(?:reel|p)/([^/?]+)", cur_url)
                        if m:
                            code = m.group(1)
                            if code not in seen:
                                seen.add(code)
                                reels.append({
                                    "shortcode": code,
                                    "url": f"https://www.instagram.com/reel/{code}/",
                                    "creator": creator
                                })
                                print(f"🎯 [{len(reels)}/{max_count}] Verified Startup Reel: https://www.instagram.com/reel/{code}/ (By @{creator})")

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

                page.mouse.move(600, 400)
                page.mouse.wheel(0, 1600)
                time.sleep(0.5)

        except Exception as e:
            print("Chat extraction error:", e)
        finally:
            browser.close()

    print(f"\nTotal Verified Reels strictly from @im_raaaj_ chat: {len(reels)}")
    return reels

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    reels = get_shared_reels_from_chat(limit)
    print("Found total:", len(reels))
