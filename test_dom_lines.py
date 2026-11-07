import sys
import time
import re
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies

sys.stdout.reconfigure(encoding='utf-8')

cookies = get_channel_cookies('startup_road')
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-dev-shm-usage', '--no-sandbox', '--blink-settings=imagesEnabled=false']
    )
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    url = "https://www.instagram.com/reel/DbnfPsNNOUz/"
    page.goto(url, timeout=25000, wait_until='domcontentloaded')
    time.sleep(4)
    
    # Click on the comment icon or look for comment section
    text = page.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    print("Found total lines:", len(lines))
    for i, l in enumerate(lines[:35]):
        print(f"L{i}: {l}")

    browser.close()

