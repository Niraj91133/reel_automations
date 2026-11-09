import os
import sys
import json
import sqlite3
import subprocess
import glob
import time
import re
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.video_engine import render_channel_video
from core.database import ChannelDatabase
import yt_dlp

SR_DB = os.path.join(BASE_DIR, "databases", "startup_road_history.db")
TARGET_DB_PATH = os.path.join(BASE_DIR, "databases", "the_startuproad_history.db")
QUEUE_DIR = r"C:\reel_cache\the_startuproad\tomorrow_reels"
TEMP_DIR = r"C:\reel_cache\the_startuproad\temp_downloads"

os.makedirs(QUEUE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def prebake_startuproad_mirror(count=30):
    print("========================================================")
    print("  🔄 PRE-BAKING MIRROR REELS FOR @the_startuproad")
    print(f"  Source: @startup_road (Chronological order: ID 1 ➔ {count})")
    print("========================================================")

    # 1. Fetch all startup_road reels
    conn_sr = sqlite3.connect(SR_DB)
    c_sr = conn_sr.cursor()
    c_sr.execute("SELECT id, shortcode, username, title, permalink FROM processed_reels WHERE permalink != '' ORDER BY id ASC")
    sr_reels = c_sr.fetchall()
    conn_sr.close()

    # 2. Fetch already processed reels for the_startuproad
    db_target = ChannelDatabase(TARGET_DB_PATH)

    candidates = []
    for row in sr_reels:
        rid, shortcode, username, title, permalink = row
        if not db_target.is_reel_processed(shortcode) and not db_target.is_reel_rejected(shortcode):
            candidates.append(row)

    print(f"Total source reels: {len(sr_reels)}")
    print(f"Available unposted candidates: {len(candidates)}")

    # 3. Check existing files in queue
    existing_reels = glob.glob(os.path.join(QUEUE_DIR, "ready_*.mp4"))
    print(f"Already baked in tomorrow's queue: {len(existing_reels)} reels")
    
    existing_slots = set()
    for f in existing_reels:
        base = os.path.basename(f)
        m = re.match(r'ready_(\d+)_', base)
        if m:
            existing_slots.add(int(m.group(1)))

    if len(existing_reels) >= count:
        print(f"✅ Target of {count} reels already satisfied in queue!")
        return len(existing_reels)

    ydl_opts_meta = {
        'quiet': True,
        'skip_download': True,
        'cookiefile': os.path.join(BASE_DIR, 'cookies.txt')
    }

    slot = 1
    baked_count = len(existing_reels)

    for item in candidates:
        if baked_count >= count:
            break

        # Find next available slot
        while slot in existing_slots:
            slot += 1
        if slot > count:
            break

        rid, shortcode, creator, title, permalink = item
        print(f"\n▶ [{slot}/{count}] Mirroring Reel #{rid}: {title}")
        print(f"  Source Permalink: {permalink}")

        # Extract caption and video URL from permalink
        raw_video = os.path.join(TEMP_DIR, f"raw_{shortcode}.mp4")
        out_video = os.path.join(QUEUE_DIR, f"ready_{slot:02d}_{shortcode}.mp4")
        out_meta = os.path.join(QUEUE_DIR, f"ready_{slot:02d}_{shortcode}.json")

        caption = ""
        try:
            with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
                info = ydl.extract_info(permalink, download=False)
                caption = info.get('description', '') or ''
        except Exception as e_meta:
            print(f"  Warning: Could not fetch caption from permalink: {e_meta}")

        # If caption not fetched from permalink, try original shortcode
        if not caption:
            try:
                orig_url = f"https://www.instagram.com/reel/{shortcode}/"
                with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
                    info = ydl.extract_info(orig_url, download=False)
                    caption = info.get('description', '') or ''
            except Exception:
                pass

        # Fallback to rich caption if still empty
        if not caption or len(caption) < 50:
            from core.caption_engine import generate_rich_caption
            caption = generate_rich_caption("the_startuproad", title, "BUSINESS MODEL", creator)

        # Replace any mention of @startup_road with @the_startuproad
        caption = caption.replace("@startup_road", "@the_startuproad")
        caption = caption.replace("#StartupRoad", "#TheStartupRoad")

        # Download raw video
        ydl_opts_dl = {
            'outtmpl': raw_video,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
            'cookiefile': os.path.join(BASE_DIR, 'cookies.txt'),
            'merge_output_format': 'mp4'
        }

        dl_success = False
        try:
            with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
                ydl.download([permalink])
            if os.path.exists(raw_video) and os.path.getsize(raw_video) > 50000:
                dl_success = True
        except Exception as e_dl:
            print(f"  Download from permalink failed: {e_dl}, trying shortcode...")
            try:
                orig_url = f"https://www.instagram.com/reel/{shortcode}/"
                with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
                    ydl.download([orig_url])
                if os.path.exists(raw_video) and os.path.getsize(raw_video) > 50000:
                    dl_success = True
            except Exception as e_dl2:
                print(f"  Download from shortcode also failed: {e_dl2}")

        if not dl_success:
            print(f"  ❌ Skipping {shortcode}: video download failed.")
            continue

        # Render video with micro-transformation (contrast, saturation, audio pitch shift)
        try:
            print(f"  🎬 Rendering with anti-duplicate transform for @the_startuproad...")
            from core.config_manager import get_channel_config
            cfg = get_channel_config("the_startuproad")
            rendered_temp, _ = render_channel_video(
                input_video_path=raw_video,
                channel_config=cfg,
                hook_pill="BUSINESS MODEL",
                main_title=title,
                sub_quote="PRACTICAL BUSINESS:"
            )
            shutil.move(rendered_temp, out_video)

            # Write metadata
            meta_data = {
                "shortcode": shortcode,
                "title": title,
                "creator": creator,
                "caption": caption,
                "hook_pill": "BUSINESS MODEL",
                "first_comment": 'Want the complete supplier list, machine contact & breakdown? Comment "DETAILS" below and I will DM you instantly! 📩',
                "source_id": rid,
                "source_permalink": permalink,
                "rendered_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(out_meta, 'w', encoding='utf-8') as mf:
                json.dump(meta_data, mf, indent=2, ensure_ascii=False)

            existing_slots.add(slot)
            slot += 1
            baked_count += 1
            print(f"  ✅ Successfully baked Slot #{slot-1}: {os.path.basename(out_video)} ({os.path.getsize(out_video)/(1024*1024):.1f} MB)")

        except Exception as e_render:
            print(f"  ❌ Rendering failed: {e_render}")
        finally:
            if os.path.exists(raw_video):
                try: os.remove(raw_video)
                except: pass

    print(f"\n========================================================")
    print(f"  🏁 Mirror pre-bake complete! Total in queue: {baked_count}/{count}")
    print(f"========================================================\n")
    return baked_count

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    prebake_startuproad_mirror(count)
