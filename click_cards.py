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

def click_and_capture_reel_url():
    cookies = parse_cookie_file(COOKIE_FILE)
    captured_urls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies(cookies)
        page = context.new_page()

        # Listen to dialogs or new pages or URL changes
        context.on("page", lambda new_p: captured_urls.append(new_p.url))

        page.goto(CHAT_THREAD_URL, timeout=45000, wait_until="networkidle")
        time.sleep(4)

        # Find the reel cards by their creator text
        for creator in ["irfan_bhai90k", "just_sfurti", "vaidant.jain"]:
            card = page.query_selector(f"div[role='button']:has-text('{creator}')")
            if card:
                print(f"Clicking reel card of @{creator}...")
                card.click()
                time.sleep(3)
                current_url = page.url
                print(f"Current page URL after click: {current_url}")
                if "/reel/" in current_url or "/p/" in current_url:
                    captured_urls.append(current_url)

                # Check if a dialog or modal opened
                modal_reel = page.query_selector("a[href*='/reel/'], a[href*='/p/']")
                if modal_reel:
                    href = modal_reel.get_attribute("href")
                    print(f"Found modal reel link: {href}")
                    captured_urls.append(href)

                # Close modal if escape works
                page.keyboard.press("Escape")
                time.sleep(1)

        browser.close()

    print("Captured reel URLs:", set(captured_urls))

if __name__ == '__main__':
    click_and_capture_reel_url()
