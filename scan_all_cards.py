from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    
    # Check all button card indices and what opens
    cards = page.query_selector_all("div[role='button']")
    print(f"Total role=button found: {len(cards)}")
    for i in range(len(cards)):
        c = cards[i]
        txt = c.inner_text().replace('\n', ' ').strip()
        # Filter obvious UI
        if txt in ["Message...", "Search", "Primary", "General", "Requests", "Your note", "Active now"]:
            continue
        try:
            c.click(timeout=1500)
            page.wait_for_timeout(1500)
            cur = page.url
            if '/p/' in cur or '/reel/' in cur:
                print(f"Index [{i}] opens reel/post: {cur} (Text: {repr(txt[:40])})")
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            else:
                # print(f"Index [{i}] didn't change URL (Text: {repr(txt[:25])})")
                pass
        except Exception as e:
            pass
    browser.close()
