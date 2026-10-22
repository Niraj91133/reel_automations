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

    # Let's inspect the HTML of the first message bubble / card
    cards = page.query_selector_all("div[role='button']")
    for c in cards:
        txt = c.inner_text().strip()
        if 'srijan_chadha' in txt or 'ankitbansalofficial' in txt or 'diamondgurusuuraj' in txt:
            print("FOUND TARGET CARD:")
            print("TEXT:", txt[:60])
            print("INNER HTML:", c.inner_html()[:400])
            # Check if there is an anchor or img inside
            a_tags = c.query_selector_all("a")
            print("A TAGS INSIDE:", [a.get_attribute("href") for a in a_tags])
            img_tags = c.query_selector_all("img")
            print("IMG TAGS INSIDE:", [img.get_attribute("src")[:60] for img in img_tags if img.get_attribute("src")])
            break
    browser.close()
