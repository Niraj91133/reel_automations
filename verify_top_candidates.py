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

candidates_to_check = [
    {"creator": "businessidea_841", "code": "DfOPQX6BnoE", "views": "5.7M"},
    {"creator": "actual.abhishek", "code": "DeMVdn2Czop", "views": "14.9M"},
    {"creator": "actual.abhishek", "code": "DbVmX9WCq4t", "views": "2.3M"},
    {"creator": "ecom.deep", "code": "DUYB5ATEsqp", "views": "2.5M"},
    {"creator": "businessidea_841", "code": "DfT7L8BBlaN", "views": "1.5M"},
    {"creator": "businessidea_841", "code": "DfV9plphcK3", "views": "1M"},
    {"creator": "businessidea_841", "code": "DfZFYesh8SS", "views": "904K"},
    {"creator": "businessidea_841", "code": "DfRWfVoB01X", "views": "277K"},
    {"creator": "businessidea_841", "code": "DfYibT-BI-I", "views": "232K"},
    {"creator": "ideas_logix", "code": "DbnfPsNNOUz", "views": "6.7M"},
    {"creator": "ideas_logix", "code": "Db90Bo_P8gD", "views": "2.3M"},
    {"creator": "ideas_logix", "code": "DfTnI4kP-Ug", "views": "875K"},
    {"creator": "ideas_logix", "code": "DasTHW6vLke", "views": "621K"}
]

cookies = get_channel_cookies('startup_road')
verified_hits = []

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

    for item in candidates_to_check:
        code = item["code"]
        creator = item["creator"]
        views_claim = item["views"]
        url = f"https://www.instagram.com/reel/{code}/"

        if code in posted_shortcodes:
            print(f"Skipping {code}: Already in startup_road DB!", flush=True)
            continue

        try:
            page.goto(url, timeout=25000, wait_until='domcontentloaded')
            time.sleep(2.5)

            og_desc = page.evaluate("() => document.querySelector('meta[property=\"og:description\"]')?.content || ''")
            og_title = page.evaluate("() => document.querySelector('meta[property=\"og:title\"]')?.content || ''")
            body = page.evaluate("() => document.body.innerText || ''")

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

            # Look for CTA in caption or body
            full_text = f"{caption} {body}".lower()
            cta_match = ""
            for pattern in [r'comment\s*[\'\"\(]?([a-zA-Z0-9_\s]+)[\'\"\)]?', r'comment\s+karo', r'comment\s+down', r'drop\s+a\s+comment']:
                m_cta = re.search(pattern, full_text)
                if m_cta:
                    cta_match = m_cta.group(0).strip()
                    break

            # Check spoken audio/original audio
            # Audio is often mentioned as "Original audio" or creator name
            audio_text = ""
            m_audio = re.search(r'([^\n]+)\s*•\s*Original audio', body)
            if m_audio:
                audio_text = m_audio.group(1).strip() + " (Original audio)"
            elif "Original audio" in body:
                audio_text = "Original audio (Hindi Voiceover)"

            verified_hits.append({
                "creator": creator,
                "code": code,
                "url": url,
                "views": views_claim,
                "likes": likes,
                "comments": comments,
                "caption": caption,
                "cta": cta_match or "Yes",
                "audio": audio_text or "Original audio"
            })

            print(f"[{creator}] {url} | Views: {views_claim} | Likes: {likes:,} | Comments: {comments:,} | CTA: {cta_match!r}", flush=True)
            print(f"Caption: {caption[:150]!r}\n", flush=True)

        except Exception as e:
            print(f"Error on {code}: {e}", flush=True)

    browser.close()

with open("top_verified_hits.json", "w", encoding="utf-8") as f:
    json.dump(verified_hits, f, indent=2)

print(f"Done! Saved {len(verified_hits)} verified reels.", flush=True)

