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

    creators = ["kartikcreatebusiness", "actual.abhishek", "ecom.deep", "businessidea_841"]
    for c in creators:
        url = f"https://www.instagram.com/{c}/reels/"
        page.goto(url, timeout=25000, wait_until='domcontentloaded')
        time.sleep(3)
        # Scroll twice to load 20-30 reels
        page.evaluate("window.scrollBy(0, 1500)")
        time.sleep(2)
        page.evaluate("window.scrollBy(0, 1500)")
        time.sleep(2)
        
        links = page.query_selector_all('a[href*="/reel/"]')
        print(f"\n--- Creator @{c}: found {len(links)} reels ---", flush=True)
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip().replace('\n', ' ')
            m = re.search(r'/reel/([^/?]+)', href)
            code = m.group(1) if m else ""
            if any(k in text for k in ['M', 'm']) or (any(k in text for k in ['K', 'k']) and not any(text.startswith(x) for x in ['1K', '2K', '3K', '4K', '5K', '6K', '7K', '8K', '9K', '1', '2', '3', '4', '5', '6', '7', '8', '9'] if len(text) < 5)):
                # Print only high views
                print(f"Code: {code} | Text: {text!r}", flush=True)

    browser.close()

