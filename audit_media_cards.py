from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    
    # Scroll up 5 times to reveal previous messages
    for i in range(5):
        page.mouse.wheel(0, -3000)
        page.wait_for_timeout(600)

    # In Instagram DMs, each reel message container has creator name or text inside
    # Find all elements inside conversation pane
    print("Finding all reel cards in message conversation...")
    cards = page.query_selector_all("div[role='button']")
    results = []
    seen = set()

    for idx, card in enumerate(cards):
        try:
            # Check if this button contains a nested img or video or span with username
            has_media = card.query_selector("img, video")
            txt = card.inner_text().strip().replace('\n', ' ')
            if has_media and txt and not any(skip in txt for skip in ["Message...", "Search", "Primary", "General", "Requests"]):
                card.click(timeout=1500)
                page.wait_for_timeout(2000)
                cur_url = page.url
                if ('/p/' in cur_url or '/reel/' in cur_url) and cur_url not in seen:
                    seen.add(cur_url)
                    results.append({'url': cur_url, 'text': txt})
                    print(f"[{len(results)}] FOUND REEL: {cur_url} | Text: {txt[:60]}")
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                else:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(200)
        except:
            pass

    print(f"\n==========================================")
    print(f"TOTAL REELS FOUND: {len(results)}")
    for r in results:
        print(f"• {r['url']} ({r['text'][:50]})")
    print(f"==========================================")
    browser.close()
