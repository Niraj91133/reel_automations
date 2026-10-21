import os
import sys
import time
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

COOKIE_FILE = "cookies.txt"

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

def extract_all_reels_from_thread(thread_url, target_name="Chat"):
    print(f"\n==========================================")
    print(f"Deep scanning {target_name} thread: {thread_url}")
    print(f"==========================================")
    
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

        # Intercept ALL JSON responses looking for xma_share, clip, media items
        def handle_response(response):
            if "direct_v2" in response.url or "graphql" in response.url:
                try:
                    res_json = response.json()
                    # Recursively traverse JSON to find clips / reels
                    def find_reels(obj):
                        if isinstance(obj, dict):
                            # Instagram reel/clip item signature
                            code = obj.get("code")
                            if code and len(code) >= 10 and len(code) <= 12:
                                user_obj = obj.get("user") or {}
                                creator = user_obj.get("username") or "creator"
                                if code not in captured_reels:
                                    captured_reels[code] = creator
                            # Check reel_share / clip / media
                            for k, v in obj.items():
                                find_reels(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                find_reels(item)

                    find_reels(res_json)
                except:
                    pass

        page.on("response", handle_response)
        page.goto(thread_url, timeout=45000, wait_until="networkidle")
        time.sleep(3)

        # Scroll up 15 times inside chat box to trigger pagination
        for s in range(15):
            page.mouse.wheel(0, -6000)
            page.keyboard.press("PageUp")
            time.sleep(1.2)
            if len(captured_reels) >= 10:
                print(f"Reached {len(captured_reels)} reels during scroll step {s+1}!")
                break

        browser.close()

    print(f"Total Unique Shared Reels Extracted: {len(captured_reels)}")
    for code, creator in list(captured_reels.items())[:12]:
        print(f"  • https://www.instagram.com/reel/{code}/ (By @{creator})")
    
    return captured_reels

if __name__ == '__main__':
    # Test on im_raaaj_
    extract_all_reels_from_thread("https://www.instagram.com/direct/t/101996904536119/", "im_raaaj_")
    # Test on baatleaderki
    extract_all_reels_from_thread("https://www.instagram.com/direct/t/17887646322533789/", "baatleaderki")
