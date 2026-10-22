from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    
    cards = page.query_selector_all("div[role='button']")
    for i, c in enumerate(cards):
        txt = c.inner_text().replace('\n', ' ')
        if "ONE PRODUCT" in txt or "diamondguru" in txt or "ankitbansal" in txt or "vaidant" in txt or "startupbydoc" in txt:
            print(f"Matched Card [{i}]: {repr(txt[:60])}")
            c.click()
            page.wait_for_timeout(2000)
            print(f"URL for [{i}]: {page.url}")
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
    browser.close()
