from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')

    # Scroll up inside chat conversation to make sure all recent messages are visible
    for s in range(5):
        page.mouse.wheel(0, -3000)
        page.wait_for_timeout(600)

    cards = page.query_selector_all("div[role='button']")
    found_reels = []
    seen = set()

    print(f"Total clickable cards found: {len(cards)}")
    for i, card in enumerate(cards):
        txt = card.inner_text().strip().replace('\n', ' ')
        if not txt or txt in ["Message...", "Search", "Primary", "General", "Requests", "Your note", "Active now", "Active"]:
            continue
        try:
            card.click(timeout=1500)
            page.wait_for_timeout(1800)
            cur = page.url
            if '/p/' in cur or '/reel/' in cur:
                if cur not in seen:
                    seen.add(cur)
                    found_reels.append({"index": i, "url": cur, "text": txt[:60]})
                    print(f"[{len(found_reels)}] FOUND: {cur} | Text: {txt[:50]}")
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
        except:
            pass

    print(f"\n==========================================")
    print(f"TOTAL REELS ACTUALLY FOUND: {len(found_reels)}")
    for r in found_reels:
        print(f"• {r['url']} ({r['text']})")
    print(f"==========================================")
    browser.close()
