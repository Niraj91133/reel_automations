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

    btn = page.query_selector("div[role='button']:has-text('srijan_chadha')")
    if btn:
        print('Found srijan_chadha button! Clicking...')
        btn.click()
        page.wait_for_timeout(3000)
        print('Current URL after click:', page.url)
    else:
        print('Button not found')
    browser.close()
