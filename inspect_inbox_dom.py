from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto("https://www.instagram.com/direct/inbox/", timeout=45000, wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    page.screenshot(path="inbox_screenshot.png")
    
    # Check text
    text = page.evaluate("() => document.body.innerText")
    print("Inbox text (first 1000 chars):")
    print(text[:1000])
    
    browser.close()
