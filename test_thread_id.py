from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/17847817809098169/', timeout=45000, wait_until='networkidle')
    page.screenshot(path='true_im_raaaj_thread.png')
    text = page.evaluate("() => document.body.innerText")
    print("PAGE TITLE:", page.title())
    print("URL:", page.url)
    print("SNIPPET:", repr(text[:300]))
    browser.close()
