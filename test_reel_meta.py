import sys
import time
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
    page.goto('https://www.instagram.com/reel/DfFOevaNt1E/', timeout=25000, wait_until='domcontentloaded')
    time.sleep(3)
    
    og_desc = page.evaluate("() => document.querySelector('meta[property=\"og:description\"]')?.content || ''")
    og_title = page.evaluate("() => document.querySelector('meta[property=\"og:title\"]')?.content || ''")
    body = page.evaluate("() => document.body.innerText || ''")
    
    print('TITLE:', og_title, flush=True)
    print('DESC:', og_desc, flush=True)
    print('BODY SAMPLE:', body[:300].replace('\n', ' '), flush=True)
    browser.close()

