"""
================================================================================
🔄 EXACT MIRROR ENGINE: @startup_road ➔ @the_startuproad
================================================================================
Mirrors @startup_road from the BOTTOM of the feed upwards to the top (Oldest ➔ Newest):
1. Starts from the earliest/bottom posts of @startup_road and moves chronologically forward.
2. Downloads the exact original video from Meta CDN / permalink.
3. Takes the EXACT SAME CAPTION as posted on @startup_road (same hook, structure, tags).
4. Fast metadata & hash scrub so Meta accepts the upload without duplicate cross-account collision.
5. Zero new AI rewriting: 100% exact 1:1 mirror of @startup_road's authentic feed.
================================================================================
"""

import os
import sys
import re
import json
import time
import glob
import shutil
import sqlite3
import requests
import subprocess
from pathlib import Path
import yt_dlp

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.database import ChannelDatabase

TARGET_CHANNEL_ID = "the_startuproad"
SOURCE_CHANNEL_ID = "startup_road"
QUEUE_DIR = r"C:\reel_cache\the_startuproad\tomorrow_reels"
TEMP_DIR = r"C:\reel_cache\the_startuproad\temp_downloads"

os.makedirs(QUEUE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def fetch_startup_road_reels_from_bottom(max_fetch=300):
    """
    Fetches all published reels from @startup_road via Meta Graph API,
    and reverses the order so they start from the BOTTOM (Oldest) and go to the TOP (Newest).
    """
    cfg = get_channel_config(SOURCE_CHANNEL_ID)
    creds = cfg.get("credentials", {})
    token = creds.get("page_access_token")
    acc_id = creds.get("instagram_account_id")

    all_media = []
    if token and acc_id:
        url = f"https://graph.facebook.com/v21.0/{acc_id}/media?fields=id,caption,permalink,timestamp,media_type,media_url&limit=100&access_token={token}"
        while url and len(all_media) < max_fetch:
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", [])
                    all_media.extend(items)
                    url = data.get("paging", {}).get("next")
                else:
                    break
            except Exception as e:
                print(f"⚠️ Meta API pagination note: {e}")
                break

    # Format items
    reels = []
    if all_media:
        # REVERSE so it goes from BOTTOM (Oldest) to TOP (Newest)
        bottom_to_top = list(reversed(all_media))
        for it in bottom_to_top:
            permalink = it.get("permalink", "")
            m = re.search(r"/reel/([^/?]+)", permalink)
            shortcode = m.group(1) if m else it.get("id")
            reels.append({
                "shortcode": shortcode,
                "permalink": permalink,
                "caption": it.get("caption", ""),
                "media_url": it.get("media_url"),
                "timestamp": it.get("timestamp")
            })
    else:
        # Fallback to local database ordered from earliest ID ASC
        print("🔄 Falling back to startup_road_history.db (ORDER BY id ASC from bottom)...")
        db_path = os.path.join(BASE_DIR, "databases", "startup_road_history.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT id, shortcode, username, title, permalink FROM processed_reels WHERE permalink != '' ORDER BY id ASC")
            for rid, sc, user, title, perm in c.fetchall():
                reels.append({
                    "shortcode": sc,
                    "permalink": perm,
                    "caption": title,
                    "media_url": None,
                    "timestamp": None
                })
            conn.close()

    return reels

def download_video_fast(media_url, permalink, shortcode, dest_path):
    """
    Downloads reel video:
    1. Direct fast HTTP stream from Meta CDN (1-2s).
    2. Fallback to yt-dlp.
    """
    if media_url:
        try:
            r = requests.get(media_url, stream=True, timeout=30)
            if r.status_code == 200:
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
                    return True
        except Exception as e_cdn:
            print(f"  Note: Direct CDN stream failed ({e_cdn}), switching to yt-dlp...")

    ydl_opts = {
        'outtmpl': dest_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'cookiefile': os.path.join(BASE_DIR, 'cookies.txt'),
        'merge_output_format': 'mp4'
    }
    target_url = permalink or f"https://www.instagram.com/reel/{shortcode}/"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target_url])
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
            return True
    except Exception as e_dl:
        print(f"  ❌ yt-dlp download failed for {shortcode}: {e_dl}")

    return False

def scrub_video_metadata(input_path, output_path):
    """
    Fast binary hash alteration & metadata strip (preserves 100% quality and visual layout).
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-map_metadata", "-1",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 50000:
            return True
    except Exception as e:
        print(f"FFmpeg scrub notice: {e}")

    try:
        shutil.copy2(input_path, output_path)
        return True
    except Exception:
        return False

def prebake_startuproad_mirror(count=5):
    """
    Main mirror synchronizer:
    Takes posts from @startup_road starting from the BOTTOM (Oldest ➔ Newest)
    with their EXACT ORIGINAL CAPTIONS.
    """
    print("========================================================")
    print("  🔄 EXACT MIRROR ENGINE: @startup_road ➔ @the_startuproad")
    print(f"  Picks from BOTTOM (Oldest ➔ Newest) with EXACT SAME CAPTIONS")
    print("========================================================")

    target_cfg = get_channel_config(TARGET_CHANNEL_ID)
    db_target = ChannelDatabase(target_cfg["runtime"]["db_path"])

    # 1. Fetch reels from startup_road ordered from bottom (oldest first)
    source_reels = fetch_startup_road_reels_from_bottom(max_fetch=300)
    print(f"Total source reels available from @startup_road: {len(source_reels)}")

    # 2. Check existing ready reels in queue
    existing_meta = sorted(glob.glob(os.path.join(QUEUE_DIR, "ready_*.json")))
    
    queued_shortcodes = set()
    used_slots = set()
    for mf in existing_meta:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                d = json.load(f)
            sc = d.get("shortcode")
            if sc and not db_target.is_reel_processed(sc):
                queued_shortcodes.add(sc)
            base = os.path.basename(mf)
            parts = base.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                used_slots.add(int(parts[1]))
        except Exception:
            pass

    today_posted = db_target.get_today_count()
    valid_in_queue = len(queued_shortcodes)
    print(f"Posted today: {today_posted} | Unprocessed in queue: {valid_in_queue}")

    needed = count - valid_in_queue
    if needed <= 0:
        print(f"✅ Buffer satisfied ({valid_in_queue} ready reels). No need to bake now.\n")
        return valid_in_queue

    print(f"Replenishing {needed} reels starting from the BOTTOM (Oldest ➔ Newest)...\n")

    baked_count = valid_in_queue
    next_slot = max(used_slots | {today_posted}) + 1

    for item in source_reels:
        if baked_count >= count:
            break

        sc = item["shortcode"]
        permalink = item["permalink"]
        orig_caption = item["caption"]
        media_url = item.get("media_url")
        timestamp = item.get("timestamp")

        # Skip if already posted on the_startuproad or already in queue
        if db_target.is_reel_processed(sc) or db_target.is_reel_rejected(sc) or sc in queued_shortcodes:
            continue

        print(f"▶ [Slot #{next_slot:02d}] Mirroring from BOTTOM: {sc} (Date: {timestamp})")
        print(f"  Source URL: {permalink}")

        # Exact caption mirroring (Adapt signature mention to @the_startuproad)
        mirror_caption = orig_caption
        if "@startup_road" in mirror_caption:
            mirror_caption = mirror_caption.replace("@startup_road", "@the_startuproad")
        elif "Follow" in mirror_caption:
            mirror_caption += "\n\nFollow @the_startuproad for daily startup insights."

        # Extract title from caption first line
        first_line = mirror_caption.split("\n")[0] if mirror_caption else "BUSINESS MODEL"
        clean_title = re.sub(r'[^\w\s\-,:!\?\.]', '', first_line).strip()
        words = [w for w in clean_title.split() if not w.startswith("#")][:10]
        title = " ".join(words) or "BUSINESS MODEL BREAKDOWN"

        temp_dl = os.path.join(TEMP_DIR, f"raw_{sc}.mp4")
        out_video = os.path.join(QUEUE_DIR, f"ready_{next_slot:02d}_{sc}.mp4")
        out_meta = os.path.join(QUEUE_DIR, f"ready_{next_slot:02d}_{sc}.json")

        # Download original video
        dl_ok = download_video_fast(media_url, permalink, sc, temp_dl)
        if not dl_ok:
            print(f"  ❌ Could not download video for {sc}, skipping...")
            continue

        try:
            # Fast metadata scrub
            scrub_ok = scrub_video_metadata(temp_dl, out_video)
            if not scrub_ok:
                print(f"  ❌ Scrub failed for {sc}")
                continue

            # Save exact metadata
            meta_data = {
                "shortcode": sc,
                "title": title,
                "creator": "startup_road",
                "caption": mirror_caption,
                "hook_pill": "BUSINESS MODEL",
                "first_comment": 'Want the complete supplier list, machine contact & breakdown? Comment "DETAILS" below and I will DM you instantly! 📩',
                "source_permalink": permalink,
                "mirrored_from": "@startup_road",
                "mirrored_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(out_meta, "w", encoding="utf-8") as mf:
                json.dump(meta_data, mf, indent=2, ensure_ascii=False)

            print(f"  ✅ Successfully baked Slot #{next_slot:02d}: {title[:40]}")
            print(f"     Caption: {mirror_caption.splitlines()[0][:50]}... ({len(mirror_caption)} chars)")
            print(f"     Size: {os.path.getsize(out_video)/(1024*1024):.1f} MB\n")

            queued_shortcodes.add(sc)
            used_slots.add(next_slot)
            next_slot += 1
            baked_count += 1

        except Exception as e_bake:
            print(f"  ❌ Error baking slot {next_slot}: {e_bake}")
        finally:
            if os.path.exists(temp_dl):
                try: os.remove(temp_dl)
                except: pass

    print("========================================================")
    print(f"  🏁 Mirror sync complete! Ready in queue: {baked_count}/{count}")
    print("========================================================\n")
    return baked_count

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    prebake_startuproad_mirror(count)
