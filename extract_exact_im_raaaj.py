import json
from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0')
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    page.wait_for_timeout(3000)

    # Scroll up to top
    for _ in range(8):
        page.mouse.move(600, 400)
        page.mouse.wheel(0, -4000)
        page.wait_for_timeout(600)

    # Scroll down step-by-step and collect elements
    cards_found = []
    for _ in range(8):
        elements = page.query_selector_all("div[role='button']")
        for el in elements:
            txt = el.inner_text().strip().replace('\n', ' -- ')
            if txt and not any(skip in txt for skip in ['Search', 'Primary', 'General', 'Requests', 'Message...', 'Your note']):
                if txt not in cards_found:
                    cards_found.append(txt)
        page.mouse.move(600, 400)
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(600)

    print("\n==========================================")
    print(f"TOTAL EXACT REEL CARDS IN IM_RAAAJ CHAT: {len(cards_found)}")
    print("==========================================")
    for idx, card in enumerate(cards_found, 1):
        print(f"[{idx}] {card[:100]}")
    browser.close()
