import json
import time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

import sys
sys.stdout.reconfigure(encoding='utf-8')
cookies = parse_cookie_file(COOKIE_FILE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    raw_items = []

    def on_response(response):
        # Capture raw thread items payload from Instagram
        if "graphql" in response.url or "direct_v2" in response.url or "threads" in response.url:
            try:
                data = response.json()
                def extract_items(obj):
                    if isinstance(obj, dict):
                        # If object has code or reel_share / clip
                        code = obj.get("code")
                        ts = obj.get("timestamp") or obj.get("taken_at")
                        user_obj = obj.get("user") or {}
                        creator = user_obj.get("username")
                        caption_obj = obj.get("caption") or {}
                        caption_text = caption_obj.get("text") if isinstance(caption_obj, dict) else str(caption_obj)

                        if code and 9 <= len(code) <= 13:
                            raw_items.append({
                                "code": code,
                                "creator": creator or "unknown",
                                "timestamp": ts,
                                "snippet": (caption_text or "")[:80]
                            })
                        for k, v in obj.items():
                            extract_items(v)
                    elif isinstance(obj, list):
                        for el in obj:
                            extract_items(el)
                extract_items(data)
            except:
                pass

    page.on("response", on_response)
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    time.sleep(3)

    # Scroll up 25 times inside the conversation to load the last 24 hours of messages
    print("Scrolling 25 times to load full 24-hour history...")
    for i in range(25):
        page.mouse.wheel(0, -5000)
        page.keyboard.press("PageUp")
        time.sleep(0.8)

    # Also extract any visual links present in DOM
    dom_links = page.evaluate("""
        () => {
            const list = [];
            const anchors = document.querySelectorAll("a[href*='/reel/'], a[href*='/p/']");
            anchors.forEach(a => list.push(a.href));
            return list;
        }
    """)
    print(f"DOM Links found: {len(dom_links)}")

    # Deduplicate captured items
    unique_reels = {}
    for item in raw_items:
        code = item["code"]
        if code not in unique_reels:
            unique_reels[code] = item

    print(f"\n=======================================================")
    print(f"TOTAL UNIQUE REELS FOUND IN IM_RAAAJ_ CHAT: {len(unique_reels)}")
    print(f"=======================================================")
    
    idx = 1
    for code, info in unique_reels.items():
        print(f"[{idx}] https://www.instagram.com/reel/{code}/ | Creator: @{info['creator']} | Info: {info['snippet']}")
        idx += 1

    browser.close()
