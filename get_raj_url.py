from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/inbox/', timeout=45000, wait_until='networkidle')
    
    # Click specifically on the user 'राज' in left sidebar
    print("Looking for 'राज' in conversation sidebar...")
    user_item = page.query_selector("span:has-text('राज')")
    if user_item:
        print("Clicking on 'राज'...")
        user_item.click()
        page.wait_for_timeout(3000)
        print("TRUE URL FOR RAJ:", page.url)
    else:
        print("Could not find 'राज' span")
    browser.close()
