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
    print("Navigating to Instagram chat with @im_raaaj_...")
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

            # Scroll up to top of history
            print("Step 1: Scrolling conversation history...")
            for _ in range(8):
                page.mouse.move(600, 400)
                page.mouse.wheel(0, -4000)
                time.sleep(0.5)

            # Discover all distinct creator handles by sweeping downwards
            all_creators = []
            for _ in range(8):
                anchors = page.query_selector_all("a[href^='/']")
                for a in anchors:
                    h = a.get_attribute('href')
                    if h:
                        cleaned = h.strip('/')
                        if cleaned and not any(skip == cleaned for skip in ['direct', 'explore', 'reels', 'home', 'messages', 'p', 'reel', 'stories', 'im_raaaj_', 'startup_road']):
                            if cleaned not in all_creators:
                                all_creators.append(cleaned)
                page.mouse.move(600, 400)
                page.mouse.wheel(0, 2000)
                time.sleep(0.5)

            print(f"Step 2: Found {len(all_creators)} creators in thread. Resolving exact Reel URLs...")
            
            # Step 2: Now resolve each creator button by scrolling upwards
            for cr in all_creators:
                if len(reels) >= max_count:
                    break

                btn = page.query_selector(f"div[role='button']:has-text('{cr}')")
                if not btn:
                    for _ in range(3):
                        page.mouse.move(600, 400)
                        page.mouse.wheel(0, -2500)
                        time.sleep(0.5)
                        btn = page.query_selector(f"div[role='button']:has-text('{cr}')")
                        if btn:
                            break

                if btn:
                    try:
                        btn.dispatch_event('click')
                        time.sleep(1.8)
                        cur_url = page.url
                        m = re.search(r"/(?:reel|p)/([^/?]+)", cur_url)
                        if m:
                            code = m.group(1)
                            if code not in seen:
                                seen.add(code)
                                reels.append({
                                    "shortcode": code,
                                    "url": f"https://www.instagram.com/reel/{code}/",
                                    "creator": cr
                                })
                                print(f"🎯 [{len(reels)}/{max_count}] Verified Reel: https://www.instagram.com/reel/{code}/ (By @{cr})")
                            
                            close_btn = page.query_selector("svg[aria-label='Close']")
                            if close_btn:
                                close_btn.click()
                                time.sleep(0.5)
                            else:
                                page.keyboard.press("Escape")
                                time.sleep(0.4)
                        else:
                            page.keyboard.press("Escape")
                            time.sleep(0.2)
                    except Exception:
                        pass

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
