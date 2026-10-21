import os
import sys
import time
import re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

COOKIE_FILE = "cookies.txt"
POLITICS_CHAT_THREAD_URL = "https://www.instagram.com/direct/t/17887646322533789/"

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

def get_politics_reels_from_chat(max_count=15):
    print("Navigating to Instagram chat with @baatleaderki...")
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
            page.goto(POLITICS_CHAT_THREAD_URL, timeout=45000, wait_until="networkidle")
            time.sleep(4)

            # Dismiss notification popups if any
            not_now = page.query_selector("button:has-text('Not Now')")
            if not_now:
                not_now.click()
                time.sleep(1)

            # Deep scroll up to load previous shared reels in chat
            print("Scrolling chat to load shared reels from @baatleaderki...")
            for i in range(8):
                page.mouse.wheel(0, -4000)
                time.sleep(1.5)

            # Find all creator handles in chat cards
            creators = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll("a[href^='/']")).map(a => a.getAttribute('href').replace(/\\//g, ''));
                    const filtered = links.filter(l => l && !['direct', 'reels', 'explore', 'baatleaderki', 'uxwithraaj'].includes(l));
                    return Array.from(new Set(filtered));
                }
            """)
            print(f"Found {len(creators)} creators in @baatleaderki chat: {creators}")

            for creator in creators:
                if len(reels) >= max_count:
                    break
                try:
                    card = page.query_selector(f"div[role='button']:has-text('{creator}')")
                    if card:
                        card.click()
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
                                    "creator": creator
                                })
                                print(f"Found Politics Reel [{len(reels)}]: {code} from @{creator}")
                        page.keyboard.press("Escape")
                        time.sleep(0.5)
                except Exception as card_err:
                    continue

        except Exception as e:
            print("Chat extraction error:", e)
        finally:
            browser.close()

    return reels

if __name__ == '__main__':
    reels = get_politics_reels_from_chat(5)
    print("Total reels found:", len(reels))
