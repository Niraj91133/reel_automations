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

    print('BEFORE SCROLL:')
    cards = page.query_selector_all("div[role='button']")
    for idx, c in enumerate(cards):
        t = c.inner_text().strip().replace('\n', ' ')
        if t and not any(s in t for s in ['Search', 'Primary', 'General', 'Requests', 'Message...', 'Your note']):
            print(f'{idx}: {t[:40]}')

    # Scroll up
    for _ in range(8):
        page.mouse.move(600, 400)
        page.mouse.wheel(0, -4000)
        page.wait_for_timeout(500)

    print('\nAFTER SCROLL:')
    cards2 = page.query_selector_all("div[role='button']")
    for idx, c in enumerate(cards2):
        t = c.inner_text().strip().replace('\n', ' ')
        if t and not any(s in t for s in ['Search', 'Primary', 'General', 'Requests', 'Message...', 'Your note']):
            print(f'{idx}: {t[:40]}')
    browser.close()
