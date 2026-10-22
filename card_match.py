from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    
    # Query cards
    cards = page.query_selector_all("div[role='button']")
    print(f"Total role=button found: {len(cards)}")
    reels = []
    for i, c in enumerate(cards):
        txt = c.inner_text().replace('\n', ' ')
        try:
            c.click(timeout=1500)
            page.wait_for_timeout(1800)
            cur = page.url
            if '/p/' in cur or '/reel/' in cur:
                print(f"MATCH [{i}]: {cur} (Text: {txt[:40]})")
                reels.append(cur)
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
        except:
            pass
    print("Final Extracted Reels:", len(reels), reels)
    browser.close()
