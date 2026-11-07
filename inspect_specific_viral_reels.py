import sys
import time
import re
import json
import sqlite3
from playwright.sync_api import sync_playwright
from core.niche_hunter import get_channel_cookies, parse_views_count

sys.stdout.reconfigure(encoding='utf-8')

# 1. Check startup_road database
conn = sqlite3.connect("database/startup_road.db")
c = conn.cursor()
posted_shortcodes = set(row[0] for row in c.execute("SELECT shortcode FROM processed_reels"))
conn.close()

test_candidates = [
    # ideas_logix
    {"creator": "ideas_logix", "code": "DbnfPsNNOUz", "views_text": "6.7M"},
    {"creator": "ideas_logix", "code": "Db90Bo_P8gD", "views_text": "2.3M"},
    {"creator": "ideas_logix", "code": "DfTnI4kP-Ug", "views_text": "875K"},
    {"creator": "ideas_logix", "code": "DasTHW6vLke", "views_text": "621K"},
    {"creator": "ideas_logix", "code": "DfOwHt3yCU6", "views_text": "216K"},
    # businessidea_841
    {"creator": "businessidea_841", "code": "DfT7L8BBlaN", "views_text": "1.5M"},
    {"creator": "businessidea_841", "code": "DfV9plphcK3", "views_text": "1M"},
    {"creator": "businessidea_841", "code": "DfZFYesh8SS", "views_text": "904K"},
    {"creator": "businessidea_841", "code": "DfRWfVoB01X", "views_text": "277K"},
    {"creator": "businessidea_841", "code": "DfYibT-BI-I", "views_text": "232K"},
    # speedgyaan
    {"creator": "speedgyaan", "code": "DWtwBAYSDpB", "views_text": "2.3M"},
    {"creator": "speedgyaan", "code": "DS7uWooAc_Z", "views_text": "1.8M"},
    {"creator": "speedgyaan", "code": "DS-Tj-WgVCj", "views_text": "1.1M"},
    {"creator": "speedgyaan", "code": "DfPofaBh4p4", "views_text": "1M"},
    {"creator": "speedgyaan", "code": "DfNDq3FhSol", "views_text": "366K"}
]

cookies = get_channel_cookies('startup_road')
detailed_reels = []

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

    for item in test_candidates:
        code = item["code"]
        creator = item["creator"]
        views_text = item["views_text"]
        url = f"https://www.instagram.com/reel/{code}/"

        if code in posted_shortcodes:
            print(f"Skipping {code}: in DB already!", flush=True)
            continue

        try:
            page.goto(url, timeout=25000, wait_until='domcontentloaded')
            time.sleep(2)

            og_desc = page.evaluate("() => document.querySelector('meta[property=\"og:description\"]')?.content || ''")
            og_title = page.evaluate("() => document.querySelector('meta[property=\"og:title\"]')?.content || ''")
            body = page.evaluate("() => document.body.innerText || ''")

            # Extract likes and comments
            likes = 0
            comments = 0

            m_likes = re.search(r'([\d\.,\s]+[KkMm]?)\s+likes', og_desc)
            if m_likes:
                likes = parse_views_count(m_likes.group(1))

            m_comments = re.search(r'([\d\.,\s]+[KkMm]?)\s+comments', og_desc)
            if m_comments:
                comments = parse_views_count(m_comments.group(1))

            if comments == 0:
                m_c_body = re.search(r'View all ([\d,]+) comments', body)
                if m_c_body:
                    comments = parse_views_count(m_c_body.group(1))
                else:
                    m_c2 = re.search(r'([\d,]+)\s+comments', body)
                    if m_c2:
                        comments = parse_views_count(m_c2.group(1))

            if likes == 0:
                m_l_body = re.search(r'Liked by [^\n]+ and ([\d,]+) others', body)
                if m_l_body:
                    likes = parse_views_count(m_l_body.group(1))
                else:
                    m_l2 = re.search(r'([\d,]+)\s+likes', body)
                    if m_l2:
                        likes = parse_views_count(m_l2.group(1))

            caption = ""
            if " - " in og_desc and ":" in og_desc:
                caption = og_desc.split(":", 1)[-1].strip()
            elif og_desc:
                caption = og_desc
            caption = caption.strip('"\'')

            # Check comment CTA in caption or title
            has_cta = any(k in (caption + body).lower() for k in [
                "comment", "comment karo", "comment down", "dm", "link in bio", 
                "share", "pdf", "supplier", "machine", "details", "contact"
            ])

            res = {
                "creator": creator,
                "code": code,
                "url": url,
                "views_text": views_text,
                "likes": likes,
                "comments": comments,
                "caption": caption[:400],
                "has_cta": has_cta,
                "in_startup_road_db": code in posted_shortcodes
            }
            detailed_reels.append(res)
            print(f"[{creator}] Reel: {code} | Views: {views_text} | Likes: {likes:,} | Comments: {comments:,} | CTA: {has_cta}", flush=True)
            print(f"   Caption: {caption[:120]!r}\n", flush=True)

        except Exception as e:
            print(f"Error on {code}: {e}", flush=True)

    browser.close()

with open("detailed_viral_reels.json", "w", encoding="utf-8") as f:
    json.dump(detailed_reels, f, indent=2)

print("Finished inspecting batch!", flush=True)

