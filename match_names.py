from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    
    # Scroll up to load cards
    for s in range(6):
        page.mouse.wheel(0, -4000)
        page.wait_for_timeout(500)

    # Get all usernames inside chat
    names = page.evaluate("""
        () => {
            const spans = Array.from(document.querySelectorAll("span, div")).map(e => e.innerText.trim());
            const filtered = spans.filter(s => s && s.length > 3 && !s.includes('\\n') && !['Message...', 'Search', 'Primary', 'General', 'Requests'].includes(s));
            return Array.from(new Set(filtered));
        }
    """)
    print("Found names in chat:", len(names), names[:30])
    
    # Click each creator handle card
    reels = []
    for name in names:
        card = page.query_selector(f"div[role='button']:has-text('{name}')")
        if card:
            try:
                card.click(timeout=1000)
                page.wait_for_timeout(1500)
                cur = page.url
                if '/p/' in cur or '/reel/' in cur:
                    print(f"MATCH: {name} -> {cur}")
                    reels.append({'creator': name, 'url': cur})
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(400)
            except:
                pass
    print("TOTAL MATCHED REELS:", len(reels), reels)
    browser.close()
