import sys
sys.stdout.reconfigure(encoding='utf-8')
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

    cards = page.query_selector_all("div[role='button']")
    print('Testing card list filtering:')
    for idx, c in enumerate(cards):
        t = c.inner_text().strip().replace('\n', ' ')
        has_media = bool(c.query_selector('img, video'))
        skip = any(s in t for s in ['Search', 'Primary', 'General', 'Requests', 'Message...', 'Your note', 'startup_road', 'Active', 'seen', 'sent an attachment'])
        if has_media:
            print(f'{idx}: skip={skip} | t={repr(t[:40])}')
    browser.close()
