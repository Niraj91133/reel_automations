from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto('https://www.instagram.com/direct/inbox/', timeout=45000, wait_until='networkidle')
    
    # Extract all inbox thread links and user handles
    threads = page.evaluate("""
        () => {
            const list = [];
            const links = document.querySelectorAll("a[href*='/direct/t/']");
            links.forEach(a => {
                list.push({
                    href: a.href,
                    text: a.innerText.replace(/\\n/g, ' ')
                });
            });
            return list;
        }
    """)
    print("=== ALL INBOX THREADS FOUND ===")
    for t in threads:
        print(f"URL: {t['href']} | Text: {t['text']}")
    browser.close()
