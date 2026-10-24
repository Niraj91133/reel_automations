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

    # All 16 creator handles found in thread
    targets = [
        'srijan_chadha', 'rise_with_rahul', 'whfmedia', 'diamondgurusuuraj',
        'ankitbansalofficial', 'startupbydoc', 'vaidant.jain', 'indiafounder',
        'harsh.solankii', 'devtalksbusiness', 'startup.playbookx', 'thechangingorder',
        'therawfeed.ig', 'techxalpha', 'tonddesign'
    ]

    reels = []
    for t in targets:
        # Check if button exists right now
        btn = page.query_selector(f'div[role="button"]:has-text("{t}")')
        if not btn:
            # Scroll up slightly to bring it into DOM
            page.mouse.move(600, 400)
            page.mouse.wheel(0, -2500)
            page.wait_for_timeout(800)
            btn = page.query_selector(f'div[role="button"]:has-text("{t}")')

        if btn:
            print(f'Found button for @{t}, dispatching click...')
            btn.dispatch_event('click')
            page.wait_for_timeout(1800)
            cur = page.url
            if '/p/' in cur or '/reel/' in cur:
                reels.append({'creator': t, 'url': cur})
                print(f'🎯 [{len(reels)}] SUCCESS: @{t} -> {cur}')
            
            # Close overlay cleanly
            close_btn = page.query_selector("svg[aria-label='Close']")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(600)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)

    print(f"\n==========================================")
    print(f"TOTAL REELS RESOLVED DIRECTLY: {len(reels)}")
    print(f"==========================================")
    for r in reels:
        print(f"• {r['url']} (@{r['creator']})")
    browser.close()
