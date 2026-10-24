from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto("https://www.instagram.com/direct/inbox/", timeout=45000, wait_until="networkidle")
    
    threads = page.evaluate("""() => {
        const items = [];
        const anchors = document.querySelectorAll('a[href*="/direct/t/"]');
        anchors.forEach(a => {
            items.push({
                href: a.href,
                text: a.innerText.replace(/\\n/g, ' -- ')
            });
        });
        return items;
    }""")
    print(f"Total Inbox Threads: {len(threads)}")
    for t in threads:
        print(f"{t['href']} ===> {t['text']}")
    browser.close()
