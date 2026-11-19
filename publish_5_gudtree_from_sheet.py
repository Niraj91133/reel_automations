import os
import sys
import re
import csv
import io
import time
import json
import urllib.request
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from core.telegram_hub import TelegramHub
from core.publisher import InstagramPublisher
from scraper import download_reel_video
from core.google_sheet_source import mark_reel_in_sheet_posted
from playwright.sync_api import sync_playwright

SHEET_ID = "1hID-uXSmtTGR7wJq1Xbzl9kH73OemGlHluppqM1BQ7s"
GUDTREE_GID = "1153198966"

def get_target_reels_from_sheet(count=5):
    """Fetches up to 5 target reels from Gudtree tab (specifically starting at row 32)."""
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GUDTREE_GID}"
    req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
    
    reader = list(csv.reader(io.StringIO(content)))
    header = [h.strip().lower() for h in reader[0]]
    
    col_link = 1
    col_shortcode = 2
    col_caption = 7
    col_status = 8
    
    candidates = []
    
    # We want rows 32-36 specifically (or first unposted/pending)
    for idx, row in enumerate(reader[1:], start=2):
        if idx < 32:
            continue
        if len(row) <= col_link:
            continue
        link = row[col_link].strip()
        sc = row[col_shortcode].strip() if len(row) > col_shortcode else ""
        if not sc and link:
            m = re.search(r'/(?:reel|p)/([A-Za-z0-9_-]+)', link)
            if m: sc = m.group(1)
            
        caption = row[col_caption].strip() if len(row) > col_caption else ""
        creator = "creator"
        m_cr = re.search(r'@([A-Za-z0-9._]{3,30})', caption)
        if m_cr:
            creator = m_cr.group(1)
            
        candidates.append({
            "row_num": idx,
            "shortcode": sc,
            "url": f"https://www.instagram.com/reel/{sc}/",
            "creator": creator,
            "caption": caption
        })
        
        if len(candidates) >= count:
            break
            
    return candidates

def update_sheet_rows_via_playwright(rows_to_update):
    """Updates the specified row numbers in the Gudtree tab via Playwright."""
    if not rows_to_update:
        return
        
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={GUDTREE_GID}"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n📊 [Sheet Auto-Sync] Opening sheet in browser to update {len(rows_to_update)} rows...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(url)
        page.wait_for_timeout(8000)
        
        for r_num in rows_to_update:
            print(f"   -> Updating Row {r_num}: Status='Sent', Sent Date='{today_str}'")
            # Update Column I (Status)
            name_box = page.wait_for_selector("#t-name-box", timeout=10000)
            name_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.type(f"I{r_num}")
            page.keyboard.press("Enter")
            page.wait_for_timeout(400)
            
            f_bar = page.wait_for_selector("#t-formula-bar-input", timeout=5000)
            f_bar.click()
            page.keyboard.press("Control+A")
            page.keyboard.type("Sent")
            page.keyboard.press("Enter")
            page.wait_for_timeout(600)
            
            # Update Column J (Sent Date)
            name_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.type(f"J{r_num}")
            page.keyboard.press("Enter")
            page.wait_for_timeout(400)
            
            f_bar.click()
            page.keyboard.press("Control+A")
            page.keyboard.type(today_str)
            page.keyboard.press("Enter")
            page.wait_for_timeout(600)
            
        print("💾 Waiting 3 seconds for Google Drive auto-save...")
        page.wait_for_timeout(3500)
        browser.close()
        print("✅ [Sheet Auto-Sync] Sheet update completed!")

def main():
    print("==================================================================")
    print("🚀 GUDTREE SHEET AUTO-POSTING PIPELINE: 5 REELS")
    print("==================================================================")
    
    channel_id = "healthy_diet"
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", "Gud Tree")
    workspace_dir = config["runtime"]["workspace_dir"]
    db = ChannelDatabase(config["runtime"]["db_path"])
    cookie_file = os.path.join(BASE_DIR, f"cookies/{channel_id}_cookies.txt")
    
    creds = config["credentials"]
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))
    
    if not publisher.is_configured():
        print(f"❌ Instagram publisher not configured for {channel_id}!")
        return
        
    candidates = get_target_reels_from_sheet(count=5)
    print(f"🎯 Target reels selected from Google Sheet:")
    for c in candidates:
        print(f"   - Row {c['row_num']}: {c['shortcode']} by @{c['creator']}")
        
    published_results = []
    rows_to_mark = []
    
    for i, item in enumerate(candidates, start=1):
        sc = item["shortcode"]
        row_num = item["row_num"]
        creator = item["creator"]
        reel_url = item["url"]
        orig_caption = item["caption"]
        
        print(f"\n------------------------------------------------------------------")
        print(f"🎬 [{i}/5] Processing Row {row_num}: {sc} (by @{creator})...")
        print(f"------------------------------------------------------------------")
        
        # 1. Download
        temp_raw = os.path.join(workspace_dir, f"sheet_raw_{sc}.mp4")
        raw_video, dl_meta = download_reel_video(reel_url, temp_raw, return_meta=True, cookie_file=cookie_file)
        if not raw_video or not os.path.exists(raw_video):
            print(f"⚠️ Failed download for {sc}. Skipping.")
            continue
            
        # 2. AI Synthesis
        print(f"🧠 [AI Engine] Analyzing and synthesizing healthy diet hook & caption...")
        dl_desc = dl_meta.get("description", "") or orig_caption
        dl_title = dl_meta.get("title", "") or ""
        ai_data = analyze_reel_for_channel(
            raw_video,
            config,
            creator,
            original_description=dl_desc,
            original_title=dl_title
        )
        
        hook_pill = ai_data.get("hook_pill", "NUTRITION FACTS")
        main_title = ai_data.get("main_title", "HEALTHY DIET INSIGHT")
        sub_quote = ai_data.get("sub_quote", "")
        caption = ai_data.get("caption", f"Health tips from @{creator}")
        first_comment = config.get("content_settings", {}).get("first_comment_template", "Comment DIET for diet plan! 🥗")
        
        print(f"   🏷️ Hook Pill: {hook_pill}")
        print(f"   📝 Title: {main_title}")
        
        # 3. GPU Video Render
        print(f"🎨 [Video Engine] Rendering emerald green branded reel...")
        try:
            rendered_video, job_id = render_channel_video(
                input_video_path=raw_video,
                channel_config=config,
                hook_pill=hook_pill,
                main_title=main_title,
                sub_quote=sub_quote
            )
        except Exception as e_rend:
            print(f"❌ Render failed for {sc}: {e_rend}")
            continue
            
        # 4. Telegram Upload for CDN URL
        print(f"📤 [Telegram CDN] Uploading to high-speed CDN...")
        try:
            sent, cdn_url = hub.send_video_with_cdn_url(rendered_video, f"<b>[{display_name}]</b>\n\n{caption}")
        except Exception as e_hub:
            print(f"❌ Telegram CDN error: {e_hub}")
            continue
            
        if not sent or not cdn_url:
            print(f"❌ Failed to get CDN URL from Telegram.")
            continue
            
        # 5. Instagram Graph API Publish
        print(f"🚀 [Instagram Publisher] Publishing live to @gudtree_...")
        try:
            pub_res = publisher.publish_reel(
                public_video_url=cdn_url,
                caption=caption,
                creator_username=creator,
                first_comment=first_comment
            )
        except Exception as e_pub:
            print(f"❌ Publish call failed: {e_pub}")
            pub_res = None
            
        if pub_res and "permalink" in pub_res:
            live_link = pub_res["permalink"]
            print(f"🎉 SUCCESS! Reel is LIVE: {live_link}")
            
            # Send alert to Telegram Hub
            hub.send_message(
                f"🎉 <b>{display_name} Reel LIVE from Sheet!</b>\n\n"
                f"🎬 <b>Title:</b> {main_title}\n"
                f"👤 <b>Creator:</b> @{creator}\n"
                f"🔗 <b>Watch:</b> {live_link}"
            )
            
            # Mark in local DB
            db.mark_reel_processed(sc, creator, main_title, live_link)
            
            # Mark in sheet log
            mark_reel_in_sheet_posted(channel_id, sc, live_link)
            
            published_results.append({
                "row_num": row_num,
                "shortcode": sc,
                "title": main_title,
                "creator": creator,
                "permalink": live_link
            })
            rows_to_mark.append(row_num)
        else:
            err = pub_res.get("error", "Unknown error") if pub_res else "No response"
            print(f"⚠️ Instagram Publish failed: {err}")
            
        # Clean up temporary raw video
        try:
            if os.path.exists(temp_raw): os.remove(temp_raw)
            if os.path.exists(rendered_video): os.remove(rendered_video)
        except:
            pass
            
        # 10s cooldown between reels
        time.sleep(10)
        
    print(f"\n==================================================================")
    print(f"📊 SUMMARY: {len(published_results)}/5 REELS PUBLISHED LIVE!")
    print(f"==================================================================")
    for p_item in published_results:
        print(f"✅ Row {p_item['row_num']} ({p_item['shortcode']}): {p_item['permalink']}")
        
    # Update Google Sheet for all published rows
    if rows_to_mark:
        update_sheet_rows_via_playwright(rows_to_mark)
        
    print("\n🏁 All tasks finished successfully!")

if __name__ == "__main__":
    main()
