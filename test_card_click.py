from playwright.sync_api import sync_playwright
import re
import time
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto("https://www.instagram.com/direct/t/101996904536119/", timeout=45000, wait_until="networkidle")
    time.sleep(3)
    
    # Try finding the card with anah.mika_
    card = page.query_selector("div[role='button']:has-text('anah.mika_')")
    if card:
        print("Found card for anah.mika_! Clicking with page.click or card.click...")
        card.click()
        time.sleep(2)
        print("URL after click:", page.url)
        page.screenshot(path="clicked_anah_mika.png")
    else:
        print("Card for anah.mika_ not found")
        
    browser.close()
