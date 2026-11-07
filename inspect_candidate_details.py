import os
import sys
import time
import re
import json
import sqlite3
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.niche_hunter import get_channel_cookies, parse_views_count

# Check DB for existing shortcodes
conn = sqlite3.connect("database/startup_road.db")
c = conn.cursor()
posted_shortcodes = set(row[0] for row in c.execute("SELECT shortcode FROM processed_reels"))
conn.close()

candidates = [
    {"creator": "kartikcreatebusiness", "code": "DfFOevaNt1E"},
    {"creator": "kartikcreatebusiness", "code": "DbilS1FJUA-"},
    {"creator": "kartikcreatebusiness", "code": "DaVP60GSPDc"},
    {"creator": "kartikcreatebusiness", "code": "DfZ4RAit0Jl"},
    {"creator": "kartikcreatebusiness", "code": "DfZldkiSfhc"},
    {"creator": "businessidea_841", "code": "DfbHRHKhoRu"},
    {"creator": "businessidea_841", "code": "DfZFYesh8SS"},
    {"creator": "businessidea_841", "code": "DfYibT-BI-I"},
    {"creator": "businessidea_841", "code": "DfWf99LBMKd"},
    {"creator": "businessidea_841", "code": "DfV9plphcK3"},
    {"creator": "ideas_logix", "code": "DfZJa1KuI5p"},
    {"creator": "ideas_logix", "code": "DfWwAI5uqHS"},
    {"creator": "ideas_logix", "code": "DfTnI4kP-Ug"},
    {"creator": "ideas_logix", "code": "DfR3C4FBpEq"},
    {"creator": "ideas_logix", "code": "DfRAzCiPgTh"},
    {"creator": "speedgyaan", "code": "DfZ7tmeB2Tj"},
    {"creator": "speedgyaan", "code": "DfXW3nsBsGh"},
    {"creator": "speedgyaan", "code": "DfUyHR_BqA0"},
    {"creator": "speedgyaan", "code": "DfSNQP4Bvab"},
    {"creator": "speedgyaan", "code": "DfPofaBh4p4"},
    {"creator": "ecom.deep", "code": "DfZnHjDvNKV"},
    {"creator": "ecom.deep", "code": "DfXC46yPsp6"},
    {"creator": "ecom.deep", "code": "DfR4uoYvDm5"},
    {"creator": "ecom.deep", "code": "DfPT2w1PbFZ"},
    {"creator": "ecom.deep", "code": "DfMvGhyv5D6"},
    {"creator": "actual.abhishek", "code": "DdOh60vTLRp"},
    {"creator": "actual.abhishek", "code": "DeMVdn2Czop"},
    {"creator": "actual.abhishek", "code": "DbVmX9WCq4t"},
    {"creator": "actual.abhishek", "code": "DfZ1s0-BE4B"},
    {"creator": "actual.abhishek", "code": "DfSE72MT7CX"},
    {"creator": "theexportdiary", "code": "Ddq1n2hMDcs"},
    {"creator": "theexportdiary", "code": "DbkP-L0s9iu"},
    {"creator": "theexportdiary", "code": "Dau-myHInUP"},
    {"creator": "theexportdiary", "code": "DfR4m_Gs2wy"},
    {"creator": "theexportdiary", "code": "DfKMAdXsIfY"}
]

cookies = get_channel_cookies("startup_road")

inspected_results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    # Block heavy media like video streams and images to load fast
    def block_media(route):
        if route.request.resource_type in ["media", "image", "font"]:
            route.abort()
        else:
            route.continue_()
    page.route("**/*", block_media)

    for item in candidates:
        code = item["code"]
        creator = item["creator"]
        reel_url = f"https://www.instagram.com/reel/{code}/"
        
        if code in posted_shortcodes:
            print(f"Skipping {code}: Already posted on startup_road!")
            continue

        try:
            print(f"Inspecting {reel_url} ({creator})...")
            page.goto(reel_url, timeout=25000, wait_until='domcontentloaded')
            time.sleep(2)

            content = page.content()
            
            # Extract meta tags
            # og:description often has: "15K likes, 420 comments - creator on Date: 'Caption text...'"
            og_desc = page.evaluate("() => document.querySelector('meta[property=\"og:description\"]')?.content || ''")
            og_title = page.evaluate("() => document.querySelector('meta[property=\"og:title\"]')?.content || ''")
            
            # Also extract body text
            body_text = page.evaluate("() => document.body.innerText || ''")

            # Extract likes and comments from og_desc
            # e.g., "34K likes, 2,410 comments - ..." or "1.2M plays, 4,500 comments"
            likes = 0
            comments = 0
            views = 0

            m_likes = re.search(r'([\d\.,\s]+[KkMm]?)\s+likes', og_desc)
            if m_likes:
                likes = parse_views_count(m_likes.group(1))

            m_comments = re.search(r'([\d\.,\s]+[KkMm]?)\s+comments', og_desc)
            if m_comments:
                comments = parse_views_count(m_comments.group(1))

            # Sometimes likes/comments in body text:
            if comments == 0:
                m_c_body = re.search(r'View all ([\d,]+) comments', body_text)
                if m_c_body:
                    comments = parse_views_count(m_c_body.group(1))
                else:
                    m_c2 = re.search(r'([\d,]+)\s+comments', body_text)
                    if m_c2:
                        comments = parse_views_count(m_c2.group(1))

            # Extract caption from og_desc or body
            caption = ""
            if " - " in og_desc and ":" in og_desc:
                caption = og_desc.split(":", 1)[-1].strip()
            elif og_desc:
                caption = og_desc

            # Clean caption quotes
            caption = caption.strip('"\'')

            # Extract view count or calculate proxy (usually views = 10x-20x likes)
            # Instagram sometimes shows plays count
            m_plays = re.search(r'([\d\.,\s]+[KkMm]?)\s+(?:plays|views)', body_text, re.IGNORECASE)
            if m_plays:
                views = parse_views_count(m_plays.group(1))
            else:
                # If likes > 10,000, views are guaranteed > 200,000 (typical reel view-to-like ratio is 15:1 to 30:1)
                views = likes * 15

            res = {
                "creator": creator,
                "code": code,
                "url": reel_url,
                "likes": likes,
                "comments": comments,
                "estimated_views": views,
                "og_desc": og_desc[:200],
                "caption": caption[:300]
            }
            print(f"  -> Likes: {likes:,} | Comments: {comments:,} | Views: {views:,}")
            print(f"  -> Caption preview: {caption[:100]!r}")
            inspected_results.append(res)
            
        except Exception as e:
            print(f"Error on {code}: {e}")

    browser.close()

with open("inspected_results.json", "w", encoding="utf-8") as f:
    json.dump(inspected_results, f, indent=2)

print(f"\nDone! Inspected {len(inspected_results)} reels.")

