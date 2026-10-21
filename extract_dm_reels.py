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

def extract_reels_from_chat():
    cookies = parse_cookie_file(COOKIE_FILE)
    reels_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies(cookies)
        page = context.new_page()
        
        # Intercept graphql / api requests to get the exact message list with reel media ids
        def handle_response(response):
            if "graphql" in response.url or "/api/v1/direct_v2/threads/" in response.url:
                try:
                    data = response.json()
                    # Search recursively for clip/reel items
                    text = str(data)
                    matches = re.findall(r'"code"\s*:\s*"([A-Za-z0-9_-]{10,12})"', text)
                    for code in matches:
                        if code not in [r["shortcode"] for r in reels_data]:
                            reels_data.append({
                                "shortcode": code,
                                "url": f"https://www.instagram.com/reel/{code}/"
                            })
                except:
                    pass

        page.on("response", handle_response)
        page.goto(CHAT_THREAD_URL, timeout=45000, wait_until="networkidle")
        time.sleep(5)

        # Also inspect DOM for clip cards
        cards = page.query_selector_all("div[role='button']")
        print("Found interactive message cards:", len(cards))

        browser.close()

    print(f"Extracted {len(reels_data)} reels from GraphQL thread data:")
    for r in reels_data:
        print("Reel:", r["url"])
    return reels_data

if __name__ == '__main__':
    extract_reels_from_chat()
