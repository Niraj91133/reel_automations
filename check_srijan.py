from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    
    # Click directly on the bottom card in chat (srijan_chandel)
    srijan = page.query_selector("div[role='button']:has-text('srijan_')")
    if srijan:
        srijan.click()
        page.wait_for_timeout(2000)
        print("Srijan Reel URL:", page.url)
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)
    else:
        print("Srijan card not found by text")
    
    browser.close()
