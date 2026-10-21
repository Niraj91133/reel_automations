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
    captured_reels = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies(cookies)
        page = context.new_page()

        # Intercept network responses for direct clip/reel data
        def handle_response(response):
            if "direct_v2" in response.url or "graphql" in response.url:
                try:
                    res_json = response.json()
                    def find_reels(obj):
                        if isinstance(obj, dict):
                            code = obj.get("code")
                            if code and 9 <= len(code) <= 13:
                                user_obj = obj.get("user") or {}
                                creator = user_obj.get("username") or "creator"
                                if code not in captured_reels:
                                    captured_reels[code] = creator
                            for k, v in obj.items():
                                find_reels(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                find_reels(item)
                    find_reels(res_json)
                except:
                    pass

        page.on("response", handle_response)

        try:
            page.goto(POLITICS_CHAT_THREAD_URL, timeout=45000, wait_until="networkidle")
            time.sleep(3)

            not_now = page.query_selector("button:has-text('Not Now')")
            if not_now:
                not_now.click()
                time.sleep(1)

            # Deep scroll up to 20 times to paginate chat and extract all reels
            print("Deep scrolling chat to extract shared reels from @baatleaderki...")
            for i in range(20):
                page.mouse.wheel(0, -6000)
                page.keyboard.press("PageUp")
                time.sleep(1.2)
                if len(captured_reels) >= max_count:
                    break

            # DOM fallback extraction if any cards in DOM
            dom_reels = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll("a[href*='/reel/'], a[href*='/p/']"))
                        .map(a => a.href);
                    return links;
                }
            """)
            for dl in dom_reels:
                m = re.search(r"/(?:reel|p)/([^/?]+)", dl)
                if m and m.group(1) not in captured_reels:
                    captured_reels[m.group(1)] = "creator"

        except Exception as e:
            print("Chat extraction error:", e)
        finally:
            browser.close()

    result = []
    for code, creator in captured_reels.items():
        result.append({
            "shortcode": code,
            "url": f"https://www.instagram.com/reel/{code}/",
            "creator": creator
        })
    print(f"Total Unique Shared Reels Extracted from @baatleaderki: {len(result)}")
    return result

if __name__ == '__main__':
    reels = get_politics_reels_from_chat(15)
    print("Found reels:", len(reels))
