import os
import sys
import sqlite3
from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

# Connect to politics db
conn = sqlite3.connect("politics_history.db")
c = conn.cursor()
c.execute("SELECT shortcode FROM processed_politics_reels")
processed = set(row[0] for row in c.fetchall())
conn.close()

print(f"Total already processed reels in DB: {len(processed)}")
print("Processed shortcodes:", processed)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto("https://www.instagram.com/direct/t/17887646322533789/", timeout=45000, wait_until="networkidle")
    
    # Intercept network responses for clip codes
    chat_reels = []
    def handle_resp(res):
        if "graphql" in res.url or "direct_v2" in res.url:
            try:
                data = res.json()
                def find_codes(obj):
                    if isinstance(obj, dict):
                        code = obj.get("code")
                        if code and 9 <= len(code) <= 13:
                            chat_reels.append(code)
                        for v in obj.values():
                            find_codes(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_codes(item)
                find_codes(data)
            except:
                pass
    page.on("response", handle_resp)
    
    # Scroll chat upwards to load messages
    for _ in range(5):
        page.mouse.move(600, 400)
        page.mouse.wheel(0, -3000)
        page.wait_for_timeout(1000)

    print("Reels found in chat response:", set(chat_reels))
    fresh = [r for r in set(chat_reels) if r not in processed]
    print(f"FRESH REELS THAT ARE NOT IN DB: {fresh}")
    browser.close()
