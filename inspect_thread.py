from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    page.screenshot(path='thread_startup_screenshot.png')
    
    # Dump visible text
    text = page.evaluate("() => document.body.innerText")
    with open("thread_startup_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    print("Screenshot saved to thread_startup_screenshot.png and text saved!")
    browser.close()
