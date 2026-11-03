from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE, STARTUP_THREAD_URL
import time

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto(STARTUP_THREAD_URL, timeout=45000, wait_until='networkidle')
    time.sleep(3)
    
    # Check if there is a textbox
    tb = page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]')
    if tb:
        print("Textbox found!")
        tb.click()
        page.keyboard.type("https://www.instagram.com/reel/DfHGAcHqLAX/")
        time.sleep(1)
        # Try both Enter and clicking Send button
        send_btn = page.query_selector('div[role="button"]:has-text("Send"), svg[aria-label="Send"]')
        if send_btn:
            print("Found Send button! Clicking...")
            send_btn.click()
        else:
            print("Pressing Enter...")
            page.keyboard.press("Enter")
        time.sleep(2)
        page.screenshot(path="scratch/chat_send_test.png")
        print("Screenshot saved to scratch/chat_send_test.png")
    else:
        print("Textbox NOT found!")
    browser.close()
