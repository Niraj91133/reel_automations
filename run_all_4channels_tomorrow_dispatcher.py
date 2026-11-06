import os
import sys
import time
import glob
import json
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

CHANNELS = [
    ("startup_road", "💼 Startup Road", "@startup_road"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_"),
    ("healthy_diet", "🥗 Gudtree", "@gudtree_"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road")
]

# 30 Slots across 15 hours (07:00 AM - 10:00 PM) ~ 31 minutes apart
def generate_30_slots(start_hour=7, end_hour=22, total_slots=30):
    slots = []
    total_minutes = (end_hour - start_hour) * 60
    interval = total_minutes / (total_slots - 1)
    
    for i in range(total_slots):
        slot_mins = int(i * interval)
        h = start_hour + (slot_mins // 60)
        m = slot_mins % 60
        slots.append((i + 1, h, m))
    return slots

SCHEDULE_SLOTS = generate_30_slots(7, 22, 30)

def publish_channel_slot(channel_id, display_name, handle, slot_num, queue_dir, posted_set):
    key = f"{channel_id}_{slot_num}"
    if key in posted_set:
        return False

    config = get_channel_config(channel_id)
    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))
    db = ChannelDatabase(config["runtime"]["db_path"])

    vid_pattern = os.path.join(queue_dir, f"ready_{slot_num:02d}_*.mp4")
    meta_pattern = os.path.join(queue_dir, f"ready_{slot_num:02d}_*.json")

    vid_files = glob.glob(vid_pattern)
    meta_files = glob.glob(meta_pattern)

    if not vid_files or not meta_files:
        print(f"[{display_name}] No pre-baked video found for slot #{slot_num}. Trying fallback...")
        return False

    vid_file = vid_files[0]
    with open(meta_files[0], 'r', encoding='utf-8') as f:
        meta = json.load(f)

    shortcode = meta.get("shortcode")
    title = meta.get("title", f"Post #{slot_num}")
    caption = meta.get("caption", f"Insights from {handle}")
    creator = meta.get("creator", "creator")

    print(f"\n🚀 [{display_name}] Publishing Slot #{slot_num}/30: {title}...")

    try:
        sent, cdn_url = hub.send_video_with_cdn_url(vid_file, f"<b>[{display_name}]</b>\n\n{caption}")
        if sent and cdn_url and publisher.is_configured():
            first_comment = config.get("content_settings", {}).get("first_comment_template")
            pub_res = publisher.publish_reel(
                public_video_url=cdn_url,
                caption=caption,
                creator_username=creator,
                first_comment=first_comment
            )
            if pub_res and "permalink" in pub_res:
                link = pub_res["permalink"]
                print(f"🎉 SUCCESS! [{display_name}] Slot #{slot_num} LIVE: {link}")
                hub.send_message(
                    f"🎉 <b>{display_name} Reel #{slot_num}/30 LIVE!</b>\n\n"
                    f"🎬 <b>Title:</b> {title}\n"
                    f"🔗 <b>Watch Reel:</b> {link}"
                )
                db.mark_reel_processed(shortcode, creator, title, link)
                posted_set.add(key)
                return True
            else:
                err_msg = pub_res.get("error", "Unknown error") if pub_res else "No response"
                print(f"⚠️ [{display_name}] Meta API response note: {err_msg}")
    except Exception as e:
        print(f"❌ Error publishing {key}: {e}")
    return False

def run_all_4channels_dispatcher():
    print("========================================================")
    print("  🚀 4-CHANNEL 30 REELS/DAY AUTOMATED DISPATCHER")
    print("========================================================")
    print("Channels:")
    for ch, name, handle in CHANNELS:
        print(f"  • {name} ({handle}) ➔ 30 Reels / Day")
    print(f"\nTotal Posts per Day: {len(CHANNELS) * 30} Reels")
    print("Time Window: 07:00 AM - 10:00 PM (Every ~31 minutes)")
    print("========================================================\n")

    posted_today = set()
    current_day = None

    while True:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # Reset trackers at midnight
        if current_day != today_str:
            current_day = today_str
            posted_today.clear()

        # Check each slot
        for slot_num, slot_hour, slot_min in SCHEDULE_SLOTS:
            if now.hour == slot_hour and now.minute >= slot_min:
                # Dispatch for each of the 4 channels with a small stagger (15 seconds between accounts)
                for ch_id, name, handle in CHANNELS:
                    key = f"{ch_id}_{slot_num}"
                    if key not in posted_today:
                        cfg = get_channel_config(ch_id)
                        queue_dir = os.path.join(cfg["runtime"]["workspace_dir"], "tomorrow_reels")
                        publish_channel_slot(ch_id, name, handle, slot_num, queue_dir, posted_today)
                        time.sleep(15)

        time.sleep(20)

if __name__ == '__main__':
    run_all_4channels_dispatcher()

