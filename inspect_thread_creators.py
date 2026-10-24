import sys
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

    # Scroll up and down collecting creator handles from anchor tags
    all_creators = []
    for _ in range(8):
        page.mouse.move(600, 400)
        page.mouse.wheel(0, -4000)
        page.wait_for_timeout(500)

    for _ in range(8):
        anchors = page.query_selector_all("a[href^='/']")
        for a in anchors:
            h = a.get_attribute('href')
            if h:
                cleaned = h.strip('/')
                if cleaned and not any(skip == cleaned for skip in ['direct', 'explore', 'reels', 'home', 'messages', 'p', 'reel', 'stories', 'im_raaaj_', 'startup_road']):
                    if cleaned not in all_creators:
                        all_creators.append(cleaned)
        page.mouse.move(600, 400)
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(500)

    print(f"\nTOTAL DISTINCT CREATOR HANDLES IN THREAD: {len(all_creators)}")
    for idx, c in enumerate(all_creators, 1):
        print(f"[{idx}] @{c}")
    browser.close()
