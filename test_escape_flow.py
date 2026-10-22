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

    # First scroll up to top of history
    for _ in range(8):
        page.mouse.move(600, 400)
        page.mouse.wheel(0, -4000)
        page.wait_for_timeout(600)

    # Now step down and test clicking with Escape
    resolved = []
    seen = set()

    for step in range(8):
        elements = page.query_selector_all("div[role='button']")
        for el in elements:
            txt = el.inner_text().strip().replace('\n', ' ')
            if not txt or any(skip in txt for skip in ['Search', 'Primary', 'General', 'Requests', 'Message...', 'Your note', 'Active', 'startup_road']):
                continue
            if not el.query_selector("img, video"):
                continue

            try:
                el.click(timeout=1000)
                page.wait_for_timeout(1800)
                cur = page.url
                m = re.search(r"/(?:reel|p)/([^/?]+)", cur)
                if m:
                    code = m.group(1)
                    if code not in seen:
                        seen.add(code)
                        resolved.append({'code': code, 'url': f'https://www.instagram.com/reel/{code}/', 'creator': txt[:30]})
                        print(f"[{len(resolved)}] CLICK SUCCESS: https://www.instagram.com/reel/{code}/ ({txt[:25]})")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(200)
            except:
                pass

        page.mouse.move(600, 400)
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(600)

    print(f"\nTOTAL RESOLVED VIA ESCAPE: {len(resolved)}")
    browser.close()
