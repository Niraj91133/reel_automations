import os
import sys
import time
import re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

COOKIE_FILE = "cookies.txt"
CHAT_THREAD_URL = "https://www.instagram.com/direct/t/101996904536119/"

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

def get_shared_reels_from_chat(max_count=15):
    print("Navigating strictly to Instagram chat with @im_raaaj_...")
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
            page.goto(CHAT_THREAD_URL, timeout=45000, wait_until="networkidle")
            time.sleep(3)

            not_now = page.query_selector("button:has-text('Not Now')")
            if not_now:
                not_now.click()
                time.sleep(1)

            # Deep scroll to load conversation history
            print("Scrolling conversation in @im_raaaj_ chat...")
            for s in range(10):
                page.mouse.wheel(0, -4000)
                time.sleep(0.7)

            # Extract distinct usernames present in message elements
            creators = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll("a[href^='/']")).map(a => a.getAttribute('href').replace(/\\//g, ''));
                    const filtered = links.filter(l => l && !['direct', 'reels', 'explore', 'im_raaaj_', 'uxwithraaj', 'home', 'messages', 'p'].includes(l));
                    return Array.from(new Set(filtered));
                }
            """)
            print(f"Detected creator handles inside @im_raaaj_ chat: {creators}")

            for cr in creators:
                if len(reels) >= max_count:
                    break
                try:
                    card = page.query_selector(f"div[role='button']:has-text('{cr}')")
                    if card:
                        card.click(timeout=2000)
                        time.sleep(2)
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
                                print(f"🎯 Verified Reel [{len(reels)}] from @im_raaaj_ chat: https://www.instagram.com/reel/{code}/ (By @{cr})")
                            page.keyboard.press("Escape")
                            time.sleep(0.5)
                        else:
                            page.keyboard.press("Escape")
                            time.sleep(0.2)
                except Exception as card_err:
                    continue

        except Exception as e:
            print("Chat extraction error:", e)
        finally:
            browser.close()

    print(f"\nTotal Verified Reels strictly from @im_raaaj_ chat: {len(reels)}")
    return reels

if __name__ == '__main__':
    reels = get_shared_reels_from_chat(15)
    print("Found reels:", len(reels))
