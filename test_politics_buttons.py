from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto("https://www.instagram.com/direct/t/17887646322533789/", timeout=45000, wait_until="networkidle")
    
    buttons = page.query_selector_all("div[role='button']")
    print("Buttons count:", len(buttons))
    for i, b in enumerate(buttons):
        txt = b.inner_text().strip().replace('\n', ' | ')
        if txt:
            print(f"Btn {i}: {txt[:100]}")
    browser.close()
