import sys
import time
import re
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies, parse_views_count

sys.stdout.reconfigure(encoding='utf-8')

cookies = get_channel_cookies('startup_road')

candidates = ["DLEbhn4TZhQ", "DfGzOqKOWQo", "DcJh9jdT-mH", "DdvypzgS-jf", "DW1F4mlgqMX"]

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--disable-dev-shm-usage', '--no-sandbox', '--blink-settings=imagesEnabled=false']
    )
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    for code in candidates:
        url = f"https://www.instagram.com/reel/{code}/"
        try:
            page.goto(url, timeout=20000, wait_until='domcontentloaded')
            time.sleep(2.5)

            og_title = page.evaluate("() => document.querySelector('meta[property=\"og:title\"]')?.content || ''")
            og_desc = page.evaluate("() => document.querySelector('meta[property=\"og:description\"]')?.content || ''")
            body = page.evaluate("() => document.body.innerText || ''")

            creator = ""
            m_c = re.search(r'([a-zA-Z0-9_\.]+) on Instagram', og_title)
            if m_c:
                creator = m_c.group(1).strip()
            elif " - " in og_desc:
                creator = og_desc.split(" - ")[-1].split(" on ")[0].replace("@", "").strip()

            lines = [l.strip() for l in body.split('\n') if l.strip()]
            counts = []
            for l in lines[8:25]:
                if any(c in l for c in ['K', 'M', 'k', 'm']) or (l.replace(',', '').isdigit() and int(l.replace(',', '')) > 10):
                    counts.append(l)

            caption = og_desc.split(":", 1)[-1].strip() if ":" in og_desc else og_desc
            caption = caption.strip('"\'')

            print(f"\n[{creator}] {url}")
            print(f"  Counts: {counts[:4]}")
            print(f"  Caption: {caption[:120]!r}")

        except Exception as e:
            print(f"Error on {code}: {e}")

    browser.close()

