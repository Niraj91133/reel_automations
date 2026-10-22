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

    targets = ['srijan_chadha', 'whfmedia', 'diamondgurusuuraj', 'ankitbansalofficial', 'rise_with_rahul', 'vaidant.jain', 'startupbydoc', 'tonddesign']
    reels = []
    for t in targets:
        btn = page.query_selector(f'div[role="button"]:has-text("{t}")')
        if btn:
            btn.click()
            page.wait_for_timeout(2000)
            cur = page.url
            if '/p/' in cur or '/reel/' in cur:
                reels.append({'creator': t, 'url': cur})
                print(f'FOUND: {t} -> {cur}')
            page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=30000, wait_until='networkidle')
            page.wait_for_timeout(2000)
    print('TOTAL FOUND:', len(reels))
    browser.close()
