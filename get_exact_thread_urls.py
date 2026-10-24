from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto("https://www.instagram.com/direct/inbox/", timeout=45000, wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # 1. Click on Raj
    print("Finding 'राज'...")
    raj_elem = page.query_selector("span:has-text('राज')")
    if raj_elem:
        raj_elem.click()
        page.wait_for_timeout(3000)
        print("EXACT URL FOR RAJ (Startup):", page.url)
        page.screenshot(path="raj_chat_view.png")
    
    # 2. Click on Baat leader ki
    print("Finding 'Baat leader ki'...")
    baat_elem = page.query_selector("span:has-text('Baat leader ki')")
    if baat_elem:
        baat_elem.click()
        page.wait_for_timeout(3000)
        print("EXACT URL FOR BAAT LEADER KI (Politics):", page.url)
        page.screenshot(path="baat_chat_view.png")
        
    browser.close()
