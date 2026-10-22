import sys
import time
import re
from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

sys.stdout.reconfigure(encoding='utf-8')
cookies = parse_cookie_file(COOKIE_FILE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0')
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    page.wait_for_timeout(3000)

    reels = []
    seen = set()

    # Step up gradually: at each scroll position, resolve all currently visible media cards
    for step in range(10):
        cards = page.query_selector_all("div[role='button']")
        for c in cards:
            t = c.inner_text().strip().replace('\n', ' ')
            if not t or any(skip in t for skip in ['Search', 'Primary', 'General', 'Requests', 'Message...', 'Your note', 'startup_road', 'Active', 'seen', 'sent an attachment']):
                continue
            if not c.query_selector("img, video"):
                continue

            # If we haven't resolved this card yet
            card_key = t[:30]
            if card_key not in seen:
                seen.add(card_key)
                try:
                    c.dispatch_event('click')
                    page.wait_for_timeout(2000)
                    cur = page.url
                    m = re.search(r"/(?:reel|p)/([^/?]+)", cur)
                    if m:
                        code = m.group(1)
                        reels.append({'creator': card_key, 'code': code, 'url': f'https://www.instagram.com/reel/{code}/'})
                        print(f"[{len(reels)}] CAPTURED: https://www.instagram.com/reel/{code}/ (By {card_key})")
                    
                    # Close overlay
                    close_btn = page.query_selector("svg[aria-label='Close']")
                    if close_btn:
                        close_btn.click()
                        page.wait_for_timeout(500)
                    else:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(300)
                except Exception as err:
                    pass

        # Scroll up slightly to bring older messages into the viewport
        page.mouse.move(600, 400)
        page.mouse.wheel(0, -1800)
        page.wait_for_timeout(1000)

    print(f"\n==========================================")
    print(f"TOTAL REELS CAPTURED VIA GRADUAL SCROLL: {len(reels)}")
    print(f"==========================================")
    for r in reels:
        print(f"• {r['url']} ({r['creator']})")
    browser.close()
