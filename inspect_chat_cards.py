from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

def inspect_chat_dom(url, name):
    print(f"\n==========================================")
    print(f"Inspecting chat DOM for: {name} ({url})")
    print(f"==========================================")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.goto(url, timeout=45000, wait_until="networkidle")
        page.wait_for_timeout(3000)
        
        # Check all buttons / clickable cards
        cards_info = page.evaluate("""() => {
            const results = [];
            // Look for any interactive elements inside the main chat area
            const main = document.querySelector("div[role='main']") || document.body;
            const buttons = main.querySelectorAll("div[role='button'], button, a");
            buttons.forEach((b, i) => {
                const rect = b.getBoundingClientRect();
                // ignore elements in left sidebar (x < 350)
                if (rect.x > 350 && rect.width > 50 && rect.height > 50) {
                    results.push({
                        tag: b.tagName,
                        role: b.getAttribute('role'),
                        ariaLabel: b.getAttribute('aria-label'),
                        innerText: b.innerText.slice(0, 80).replace(/\\n/g, ' '),
                        href: b.getAttribute('href'),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height)
                    });
                }
            });
            return results;
        }""")
        print(f"Found {len(cards_info)} interactive elements in right pane:")
        for c in cards_info:
            print(f"  [{c['tag']}|{c['role']}] ({c['x']},{c['y']} {c['w']}x{c['h']}) href={c['href']} text='{c['innerText']}' label='{c['ariaLabel']}'")
            
        browser.close()

inspect_chat_dom("https://www.instagram.com/direct/t/101996904536119/", "im_raaaj_ (Startup)")
inspect_chat_dom("https://www.instagram.com/direct/t/17887646322533789/", "baatleaderki (Politics)")
