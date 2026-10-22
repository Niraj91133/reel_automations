from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', viewport={'width': 1280, 'height': 900})
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    
    # Click on the creator avatar / username badge at top left of bottom card: (430, 540)
    print("Clicking card header avatar at (430, 540)...")
    page.mouse.click(430, 540)
    page.wait_for_timeout(2500)
    print("URL after clicking (430, 540):", page.url)
    
    # Click at top card avatar (430, 135)
    print("Clicking top card at (480, 250)...")
    page.mouse.click(480, 250)
    page.wait_for_timeout(2500)
    print("URL after clicking (480, 250):", page.url)
    
    browser.close()
