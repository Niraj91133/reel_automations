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

candidates = [
    # Creator 1: biharstorymedia
    {"creator": "biharstorymedia", "code": "DWtE2K9E9bf", "views": "3.4M"},
    {"creator": "biharstorymedia", "code": "DWqd9-AjfKJ", "views": "3.2M"},
    {"creator": "biharstorymedia", "code": "DSEgEjhilKv", "views": "1.8M"},
    
    # Creator 2: abhishekgoswamivlogs
    {"creator": "abhishekgoswamivlogs", "code": "DQAFgXkEuqi", "views": "9.1M"},
    {"creator": "abhishekgoswamivlogs", "code": "DUzzYEcEqlq", "views": "3.0M"},
    {"creator": "abhishekgoswamivlogs", "code": "DVJSm2OEuYL", "views": "3.3M"},

    # Creator 3: theexportdiary
    {"creator": "theexportdiary", "code": "Ddq1n2hMDcs", "views": "481K"},

    # Creator 4: actual.abhishek
    {"creator": "actual.abhishek", "code": "DeMVdn2Czop", "views": "14.9M"},
    {"creator": "actual.abhishek", "code": "DbVmX9WCq4t", "views": "2.3M"},
    {"creator": "actual.abhishek", "code": "DfKKLM9TRzR", "views": "899K"},

    # Creator 5: speedgyaan
    {"creator": "speedgyaan", "code": "DWtwBAYSDpB", "views": "2.3M"},
    {"creator": "speedgyaan", "code": "DS7uWooAc_Z", "views": "1.8M"},
    {"creator": "speedgyaan", "code": "DS-Tj-WgVCj", "views": "1.1M"},

    # Creator 6: ecom.deep
    {"creator": "ecom.deep", "code": "DUYB5ATEsqp", "views": "2.5M"},
    {"creator": "ecom.deep", "code": "De_2v_vBmny", "views": "267K"},

    # Creator 7: ideas_logix
    {"creator": "ideas_logix", "code": "DbnfPsNNOUz", "views": "6.7M"},

    # Creator 8: businessidea_841
    {"creator": "businessidea_841", "code": "DfV9plphcK3", "views": "1.0M"}
]

cookies = get_channel_cookies('startup_road')
inspected = []

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

    for item in candidates:
        code = item["code"]
        creator = item["creator"]
        views = item["views"]
        url = f"https://www.instagram.com/reel/{code}/"

        if code in posted_shortcodes:
            print(f"Skipping {code}: Already in startup_road DB!", flush=True)
            continue

        try:
            page.goto(url, timeout=20000, wait_until='domcontentloaded')
            time.sleep(2.5)

            og_desc = page.evaluate("() => document.querySelector('meta[property=\"og:description\"]')?.content || ''")
            body = page.evaluate("() => document.body.innerText || ''")

            lines = [l.strip() for l in body.split('\n') if l.strip()]
            
            # Find counts
            counts = []
            for l in lines[8:25]:
                if any(c in l for c in ['K', 'M', 'k', 'm']) or (l.replace(',', '').isdigit() and int(l.replace(',', '')) > 10):
                    counts.append(l)

            caption = og_desc.split(":", 1)[-1].strip() if ":" in og_desc else og_desc
            caption = caption.strip('"\'')

            print(f"\n[{creator}] {url} ({views} views)", flush=True)
            print(f"  Counts: {counts[:4]}", flush=True)
            print(f"  Caption: {caption[:120]!r}", flush=True)

            inspected.append({
                "creator": creator,
                "code": code,
                "url": url,
                "views": views,
                "counts": counts[:4],
                "caption": caption
            })

        except Exception as e:
            print(f"Error on {code}: {e}", flush=True)

    browser.close()

with open("distinct_inspected_output.json", "w", encoding="utf-8") as f:
    json.dump(inspected, f, indent=2)

print("\nDone inspecting candidates!", flush=True)

