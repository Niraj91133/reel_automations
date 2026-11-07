import sys
import time
import re
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies

sys.stdout.reconfigure(encoding='utf-8')

codes = ["DbnfPsNNOUz", "Db90Bo_P8gD", "DasTHW6vLke", "DfTnI4kP-Ug", "DfT7L8BBlaN"]
cookies = get_channel_cookies('startup_road')

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-dev-shm-usage', '--no-sandbox', '--blink-settings=imagesEnabled=false']
    )
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    for code in codes:
        url = f"https://www.instagram.com/reel/{code}/"
        page.goto(url, timeout=25000, wait_until='networkidle')
        time.sleep(2)

        # Look for comment count in buttons or aria-labels
        # Look for svg aria-label="Comment" parent button or sibling span
        stats = page.evaluate("""() => {
            const spans = Array.from(document.querySelectorAll('span, a, button'));
            const commentElems = spans.filter(el => /comment|comments/i.test(el.innerText) || /comment/i.test(el.getAttribute('aria-label') || ''));
            const texts = commentElems.map(e => e.innerText || e.getAttribute('aria-label')).slice(0, 5);
            
            // Also check all buttons
            const buttons = Array.from(document.querySelectorAll('button'));
            const btnTexts = buttons.map(b => b.innerText + ' [label=' + (b.getAttribute('aria-label')||'') + ']').filter(t => /like|comment|\d/i.test(t)).slice(0, 10);
            
            return { texts, btnTexts, bodySnippet: document.body.innerText.substring(0, 500) };
        }""")
        print(f"\n--- Code: {code} ---")
        print("Comment elements:", stats["texts"])
        print("Button texts:", stats["btnTexts"][:5])
        
    browser.close()

