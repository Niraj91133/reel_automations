import os
import sys
import time
import glob
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from scraper import download_reel_video

# 15 Verified Fresh Reels from Raj (@im_raaaj_)
APPROVED_REELS = [
    {"code": "DdyxfYbTAQ_", "creator": "adovionlabs"},
    {"code": "DQ__4iiARbu", "creator": "pushkarrajthakur"},
    {"code": "DSFUe31AcoK", "creator": "pushkarrajthakur"},
    {"code": "DY34KkYP_m0", "creator": "techcm_"},
    {"code": "DYkAhoYNkeF", "creator": "ninfinitytech"},
    {"code": "De8UOCAoRjs", "creator": "mayankraj_tandan"},
    {"code": "DfHcoCcyOSz", "creator": "farming_champions"},
    {"code": "DfFVUtcBMoC", "creator": "speedgyaan"},
    {"code": "DfT15UZutL6", "creator": "kartikcreatebusiness"},
    {"code": "Dcn1-PcznH3", "creator": "abhirathore_1"},
    {"code": "DfOPQX6BnoE", "creator": "businessidea_841"},
    {"code": "DetMnCzBR9H", "creator": "ideas_logix"},
    {"code": "DctRjiSSNDg", "creator": "ecomharnoor"},
    {"code": "DdJhOqrS-Ai", "creator": "teekendra_sharma"},
    {"code": "Dd6VUwCPILX", "creator": "ideas_logix"},
]

# 15 High-Converting Tomorrow Time Slots (06 Nov)
TOMORROW_SLOTS = [
    (8, 30),   # 08:30 AM
    (9, 25),   # 09:25 AM
    (10, 20),  # 10:20 AM
    (11, 15),  # 11:15 AM
    (12, 10),  # 12:10 PM
    (13, 5),   # 01:05 PM
    (14, 0),   # 02:00 PM
    (14, 55),  # 02:55 PM
    (15, 50),  # 03:50 PM
    (16, 45),  # 04:45 PM
    (17, 40),  # 05:40 PM
    (18, 35),  # 06:35 PM
    (19, 30),  # 07:30 PM
    (20, 25),  # 08:25 PM
    (21, 20),  # 09:20 PM
]

def prebake_reels_for_tomorrow():
    """Pre-downloads and GPU-renders all 15 reels tonight so tomorrow morning CPU is 0%."""
    config = get_channel_config("startup_road")
    db = ChannelDatabase(config["runtime"]["db_path"])
    queue_dir = os.path.join(config["runtime"]["workspace_dir"], "tomorrow_reels")
    os.makedirs(queue_dir, exist_ok=True)

    print("========================================================")
    print("  🌙 PRE-BAKING 15 REELS FOR TOMORROW'S STARTUP ROAD")
    print("========================================================")

    baked = []
    for idx, item in enumerate(APPROVED_REELS):
        code = item["code"]
        creator = item["creator"]
        out_file = os.path.join(queue_dir, f"ready_{idx+1:02d}_{code}.mp4")

        if os.path.exists(out_file) and os.path.getsize(out_file) > 100_000:
            print(f"[{idx+1}/15] Already rendered: {out_file}")
            baked.append((idx + 1, out_file, code, creator))
            continue

        reel_url = f"https://www.instagram.com/reel/{code}/"
        print(f"\n▶ [{idx+1}/15] Pre-baking {code} (by @{creator})...")

        temp_dl = os.path.join(queue_dir, f"raw_{code}.mp4")
        cookie_file = os.path.join(BASE_DIR, "cookies/startup_road_cookies.txt")
        raw_video = download_reel_video(reel_url, temp_dl, cookie_file=cookie_file)

        if not raw_video or not os.path.exists(raw_video):
            print(f"⚠️ Failed download for {code}. Skipping.")
            continue

        try:
            ai_data = analyze_reel_for_channel(raw_video, config, creator)
            hook_pill = ai_data.get("hook_pill", "STARTUP LESSON")
            main_title = ai_data.get("main_title", "BUSINESS STRATEGY")
            sub_quote = ai_data.get("sub_quote", "")

            rendered_path, _ = render_channel_video(
                input_video_path=raw_video,
                channel_config=config,
                hook_pill=hook_pill,
                main_title=main_title,
                sub_quote=sub_quote
            )
            import shutil
            shutil.move(rendered_path, out_file)

            # Save metadata alongside video
            meta_file = os.path.join(queue_dir, f"ready_{idx+1:02d}_{code}.json")
            import json
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "shortcode": code,
                    "creator": creator,
                    "title": main_title,
                    "caption": ai_data.get("caption", f"Insights from @{creator}"),
                    "hook_pill": hook_pill
                }, f, indent=2)

            baked.append((idx + 1, rendered_path, code, creator))
            print(f"✅ [{idx+1}/15] Successfully baked: {main_title}")

        except Exception as e:
            print(f"❌ Error pre-baking {code}: {e}")
        finally:
            if os.path.exists(temp_dl):
                try: os.remove(temp_dl)
                except: pass

    print(f"\n🎉 Successfully pre-baked {len(baked)}/15 reels for tomorrow!")
    return baked

def run_tomorrow_schedule_loop():
    """Standing automated dispatcher for tomorrow that posts according to TOMORROW_SLOTS."""
    config = get_channel_config("startup_road")
    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))
    db = ChannelDatabase(config["runtime"]["db_path"])
    queue_dir = os.path.join(config["runtime"]["workspace_dir"], "tomorrow_reels")

    # Pre-bake reels if not already done
    prebake_reels_for_tomorrow()

    print("\n========================================================")
    print("  🚀 TOMORROW'S STARTUP ROAD AUTOMATED DISPATCHER READY")
    print("========================================================")
    print(f"Scheduled 15 Reels throughout tomorrow across peak engagement hours.")
    print("========================================================\n")

    posted_indices = set()

    # Calculate tomorrow target date
    now = datetime.now()
    tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    while True:
        now = datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")

        # Process each slot
        for idx, (slot_hour, slot_min) in enumerate(TOMORROW_SLOTS):
            slot_num = idx + 1
            if slot_num in posted_indices:
                continue

            # Check if we have arrived at or passed slot time on tomorrow's date
            if current_date_str >= tomorrow_date and now.hour == slot_hour and now.minute >= slot_min:
                meta_pattern = os.path.join(queue_dir, f"ready_{slot_num:02d}_*.json")
                vid_pattern = os.path.join(queue_dir, f"ready_{slot_num:02d}_*.mp4")
                
                meta_files = glob.glob(meta_pattern)
                vid_files = glob.glob(vid_pattern)

                if vid_files and meta_files:
                    vid_file = vid_files[0]
                    import json
                    with open(meta_files[0], 'r', encoding='utf-8') as f:
                        meta = json.load(f)

                    shortcode = meta.get("shortcode")
                    title = meta.get("title")
                    caption = meta.get("caption")
                    creator = meta.get("creator")

                    print(f"\n🚀 [Triggered {now.strftime('%I:%M %p')}] Publishing Reel #{slot_num}: {title}...")

                    # 1. Upload to Telegram CDN
                    sent, cdn_url = hub.send_video_with_cdn_url(vid_file, f"<b>[Startup Road]</b>\n\n{caption}")

                    if sent and cdn_url:
                        first_comment = config.get("content_settings", {}).get("first_comment_template")
                        pub_res = publisher.publish_reel(
                            public_video_url=cdn_url,
                            caption=caption,
                            creator_username=creator,
                            first_comment=first_comment
                        )
                        if pub_res and "permalink" in pub_res:
                            link = pub_res["permalink"]
                            print(f"🎉 SUCCESS! Reel #{slot_num} LIVE: {link}")
                            hub.send_message(
                                f"🎉 <b>Startup Road Reel #{slot_num} LIVE!</b>\n\n"
                                f"🎬 <b>Title:</b> {title}\n"
                                f"🔗 <b>Watch Reel:</b> {link}"
                            )
                            db.mark_reel_processed(shortcode, creator, title, link)
                            posted_indices.add(slot_num)

            time.sleep(20)

if __name__ == '__main__':
    args = sys.argv[1:]
    if "--bake-only" in args:
        prebake_reels_for_tomorrow()
    else:
        run_tomorrow_schedule_loop()
