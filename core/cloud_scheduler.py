import os
import sys
import time
import gc
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config, list_available_channels, load_master_config
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.niche_hunter import fetch_approved_reels_from_raj
from scraper import download_reel_video

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def calculate_tomorrow_schedule_slots(start_hour=7, end_hour=22, total_slots=25):
    """
    Calculates unix timestamps evenly spread across tomorrow between start_hour and end_hour IST.
    E.g., 25 slots between 07:00 AM and 10:00 PM IST (approx 36 minutes apart).
    """
    now = datetime.now()
    tomorrow = now.date() + timedelta(days=1)
    
    start_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, start_hour, 0, 0)
    end_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, end_hour, 0, 0)
    
    total_duration_secs = (end_dt - start_dt).total_seconds()
    step_secs = total_duration_secs / max(1, total_slots - 1)
    
    slots = []
    for i in range(total_slots):
        slot_dt = start_dt + timedelta(seconds=i * step_secs)
        slots.append({
            "datetime": slot_dt,
            "timestamp": int(slot_dt.timestamp()),
            "time_str": slot_dt.strftime("%I:%M %p")
        })
    return slots

def cloud_schedule_channel_for_tomorrow(channel_id, target_count=25, notify_telegram=True):
    """
    Executes the Nightly Pre-Baking & Cloud-Scheduling pipeline:
    1. Fetches Raj-approved reels from chat.
    2. Downloads raw video.
    3. Gemini AI writes viral hook & caption.
    4. FFmpeg renders Ultra-HD branded 9:16 layout.
    5. Gets public CDN URL via Telegram.
    6. Official Meta Graph API schedules the Reel on Meta's servers for tomorrow!
    7. Cleans up files immediately.
    """
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", channel_id)
    username = config.get("instagram_username", channel_id)
    workspace_dir = config["runtime"]["workspace_dir"]
    db = ChannelDatabase(config["runtime"]["db_path"])

    creds = config.get("credentials", {})
    hub = TelegramHub(
        bot_token=creds.get("telegram_bot_token"),
        default_chat_id=creds.get("telegram_chat_id")
    )
    publisher = InstagramPublisher(
        instagram_account_id=creds.get("instagram_account_id"),
        page_access_token=creds.get("page_access_token")
    )

    print(f"\n========================================================")
    print(f"📅 NIGHTLY CLOUD-SCHEDULER: [{display_name}] (@{username})")
    print(f"Target: Schedule up to {target_count} reels for tomorrow")
    print(f"========================================================")

    if notify_telegram:
        hub.send_message(
            f"🌙 <b>Starting Nightly Cloud-Scheduling for {display_name}</b> (@{username})\n"
            f"🎯 Target: Scheduling up to {target_count} approved reels for tomorrow!"
        )

    # 1. Fetch Raj-approved reels from chat
    approved_candidates = fetch_approved_reels_from_raj(config, max_count=target_count)
    if not approved_candidates:
        print(f"⚠️ No fresh Raj-approved reels found for {display_name}.")
        if notify_telegram:
            hub.send_message(f"⚠️ No fresh approved reels found in chat for {display_name}. Please ensure Raj shared reels back!")
        return 0

    # 2. Calculate tomorrow's exact schedule timestamps
    slots = calculate_tomorrow_schedule_slots(start_hour=7, end_hour=22, total_slots=len(approved_candidates))
    scheduled_success = 0

    for idx, item in enumerate(approved_candidates):
        shortcode = item["shortcode"]
        reel_url = item["url"]
        creator = item.get("creator", "approved_creator")
        slot = slots[idx]
        slot_time_str = slot["time_str"]
        slot_ts = slot["timestamp"]

        print(f"\n🎬 [{idx+1}/{len(approved_candidates)}] Scheduling reel: {shortcode} for tomorrow at {slot_time_str}...")

        # A. Download raw video
        download_dir = os.path.join(workspace_dir, "downloads")
        download_file_path = os.path.join(download_dir, f"{shortcode}.mp4")
        raw_video = download_reel_video(reel_url, download_file_path)

        if not raw_video or not os.path.exists(raw_video):
            print(f"❌ Failed to download {shortcode}. Skipping.")
            continue

        rendered_video = None
        try:
            # B. Gemini AI synthesis
            ai_data = analyze_reel_for_channel(
                video_file_path=raw_video,
                channel_config=config,
                creator_username=creator
            )
            hook_pill = ai_data.get("hook_pill", "KEY LESSON")
            main_title = ai_data.get("main_title", "IMPORTANT INSIGHT")
            sub_quote = ai_data.get("sub_quote", "")
            caption = ai_data.get("caption", f"Insights from @{creator}")

            # C. FFmpeg branded rendering
            rendered_video, job_id = render_channel_video(
                input_video_path=raw_video,
                channel_config=config,
                hook_pill=hook_pill,
                main_title=main_title,
                sub_quote=sub_quote
            )

            # D. Public CDN URL via Telegram
            caption_formatted = f"<b>[{display_name}]</b>\n\n{caption}"
            sent, cdn_url = hub.send_video_with_cdn_url(rendered_video, caption_formatted)

            # E. Meta Cloud Scheduling
            first_comment = config.get("content_settings", {}).get("first_comment_template")
            if sent and cdn_url and publisher.is_configured():
                pub_res = publisher.publish_reel(
                    public_video_url=cdn_url,
                    caption=caption,
                    creator_username=creator,
                    first_comment=first_comment,
                    scheduled_publish_time=slot_ts
                )

                if pub_res and "media_id" in pub_res:
                    scheduled_success += 1
                    status_text = f"SCHEDULED for Tomorrow at {slot_time_str}"
                    db.mark_reel_processed(shortcode, creator, main_title, status_text)
                    print(f"✅ [Meta Cloud] Reel scheduled for tomorrow {slot_time_str}! (Media ID: {pub_res['media_id']})")

            gc.collect()

        except Exception as e:
            print(f"Error processing {shortcode}: {e}")
        finally:
            # Clean up local temporary files immediately to free up disk
            if raw_video and os.path.exists(raw_video):
                try: os.remove(raw_video)
                except: pass
            if rendered_video and os.path.exists(rendered_video):
                try: os.remove(rendered_video)
                except: pass

        time.sleep(3)

    if notify_telegram:
        hub.send_message(
            f"🏆 <b>[{display_name}] Cloud-Scheduling Complete!</b>\n\n"
            f"📅 <b>Total Scheduled:</b> {scheduled_success} Reels for Tomorrow\n"
            f"⏰ <b>Timing:</b> Spaced evenly from 07:00 AM to 10:00 PM\n"
            f"☁️ <i>All reels are safely loaded on Meta's servers!</i>"
        )

    return scheduled_success

