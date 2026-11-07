import sys
import time
import re
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies, parse_views_count

sys.stdout.reconfigure(encoding='utf-8')

cookies = get_channel_cookies('startup_road')

creators = ["abhishekgoswamivlogs", "kvtraders_jaipur", "biharstorymedia", "aloksrivastva"]

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-dev-shm-usage', '--no-sandbox', '--blink-settings=imagesEnabled=false']
    )
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    for handle in creators:
        url = f"https://www.instagram.com/{handle}/reels/"
        page.goto(url, timeout=20000, wait_until='domcontentloaded')
        time.sleep(2.5)
        page.evaluate("window.scrollBy(0, 1500)")
        time.sleep(1.5)

        links = page.query_selector_all('a[href*="/reel/"]')
        print(f"@{handle}: found {len(links)} reels", flush=True)
        for link in links[:6]:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip().replace('\n', ' ')
            m = re.search(r'/reel/([^/?]+)', href)
            code = m.group(1) if m else ""
            views = parse_views_count(text)
            print(f"  Code: {code} | Text: {text!r} | Views: {views}", flush=True)

    browser.close()

