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
    for c in cards:
        t = c.inner_text().strip().replace('\n', ' ')
        if 'srijan' in t:
            print('Text:', t)
            print('c.query_selector("img"):', bool(c.query_selector('img')))
            print('c.query_selector("video"):', bool(c.query_selector('video')))
            print('c.query_selector("img, video"):', bool(c.query_selector('img, video')))
            break
    browser.close()
