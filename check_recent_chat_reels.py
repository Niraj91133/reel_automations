from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE, STARTUP_THREAD_URL
import time

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto(STARTUP_THREAD_URL, timeout=45000, wait_until='networkidle')
    time.sleep(4)
    links = page.evaluate("() => Array.from(document.querySelectorAll(\"a[href*='/reel/']\")).map(a => a.href)")
    print(f"Total Reel Links found in chat: {len(links)}")
    for l in links[-12:]:
        print("  ->", l)
    browser.close()
