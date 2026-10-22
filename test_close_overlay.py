from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0')
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    page.wait_for_timeout(3000)

    c = page.query_selector("div[role='button']:has-text('srijan_chadha')")
    c.dispatch_event('click')
    page.wait_for_timeout(2000)
    print('URL AFTER CLICK:', page.url)

    close_btn = page.query_selector("svg[aria-label='Close']")
    print('Close SVG found?', bool(close_btn))
    if close_btn:
        close_btn.click()
        page.wait_for_timeout(1500)
        print('URL AFTER CLOSE:', page.url)
    browser.close()
