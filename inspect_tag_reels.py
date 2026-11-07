import sys
import time
import re
import json
import sqlite3
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies, parse_views_count

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect("database/startup_road.db")
c = conn.cursor()
posted_shortcodes = set(row[0] for row in c.execute("SELECT shortcode FROM processed_reels"))
conn.close()

with open("tag_hunted_reels.json", "r", encoding="utf-8") as f:
    tag_reels = json.load(f)

# Filter out duplicates and startup_road shortcodes
unique_codes = []
seen = set()
for r in tag_reels:
    code = r["code"]
    if code in seen or code in posted_shortcodes:
        continue
    seen.add(code)
    unique_codes.append(r)

print(f"Total unique candidates to inspect: {len(unique_codes)}")

cookies = get_channel_cookies('startup_road')
inspected_creators = []

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

    for item in unique_codes[:25]:
        code = item["code"]
        url = f"https://www.instagram.com/reel/{code}/"
        try:
            page.goto(url, timeout=18000, wait_until='domcontentloaded')
            time.sleep(2)

            og_title = page.evaluate("() => document.querySelector('meta[property=\"og:title\"]')?.content || ''")
            og_desc = page.evaluate("() => document.querySelector('meta[property=\"og:description\"]')?.content || ''")
            body = page.evaluate("() => document.body.innerText || ''")

            # Creator handle
            # og:title usually has "Creator (@handle) on Instagram..." or "Creator on Instagram: ..."
            creator = ""
            m_creator = re.search(r'([a-zA-Z0-9_\.]+) on Instagram', og_title)
            if m_creator:
                creator = m_creator.group(1).strip()
            elif " - " in og_desc:
                creator = og_desc.split(" - ")[-1].split(" on ")[0].replace("@", "").strip()

            if not creator or creator == "startup_road":
                continue

            lines = [l.strip() for l in body.split('\n') if l.strip()]
            
            # Find counts
            # In body text, line after description usually has Likes, Comments, Saves, Shares
            counts = []
            for l in lines[8:25]:
                if any(c in l for c in ['K', 'M', 'k', 'm']) or (l.replace(',', '').isdigit() and int(l.replace(',', '')) > 10):
                    counts.append(l)

            # Caption
            caption = og_desc.split(":", 1)[-1].strip() if ":" in og_desc else og_desc
            caption = caption.strip('"\'')

            print(f"[{creator}] Code: {code} | Counts: {counts[:4]}", flush=True)
            print(f"  Caption: {caption[:100]!r}\n", flush=True)

            inspected_creators.append({
                "creator": creator,
                "code": code,
                "url": url,
                "counts": counts[:4],
                "caption": caption
            })

        except Exception as e:
            print(f"Error on {code}: {e}", flush=True)

    browser.close()

with open("tag_inspected_results.json", "w", encoding="utf-8") as f:
    json.dump(inspected_creators, f, indent=2)

print(f"Done inspecting {len(inspected_creators)} tag reels!", flush=True)

