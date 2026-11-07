import sys
import time
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies

sys.stdout.reconfigure(encoding='utf-8')

codes = [
    {"creator": "ideas_logix", "code": "Db90Bo_P8gD", "views": "2.3M"},
    {"creator": "ideas_logix", "code": "DasTHW6vLke", "views": "621K"},
    {"creator": "ideas_logix", "code": "DfTnI4kP-Ug", "views": "875K"},
    {"creator": "businessidea_841", "code": "DfT7L8BBlaN", "views": "1.5M"}
]

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

    for item in codes:
        code = item["code"]
        creator = item["creator"]
        views = item["views"]
        url = f"https://www.instagram.com/reel/{code}/"
        page.goto(url, timeout=25000, wait_until='domcontentloaded')
        time.sleep(3)
        
        text = page.evaluate("() => document.body.innerText")
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Find lines with counts
        counts = []
        for l in lines[8:25]:
            if any(c in l for c in ['K', 'M', 'k', 'm']) or (l.replace(',', '').isdigit() and int(l.replace(',', '')) > 10):
                counts.append(l)
        
        print(f"\n--- {creator} [{code}] ({views} views) ---", flush=True)
        print(f"Lines 8 to 22: {lines[8:22]}", flush=True)
        print(f"Detected Counts (Likes, Comments, Saves, Shares): {counts}", flush=True)

    browser.close()

