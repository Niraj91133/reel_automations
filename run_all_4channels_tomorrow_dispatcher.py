import os
import sys
import time
import glob
import json
import random
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
    ("viral_finds", "🛍️ Trending Road", "@trending_road"),
    ("trading_road24", "📈 Trading Road 24", "@trading_road24")
]

# 30 Slots across 07:00 AM - 09:50 PM (~30.7 minutes apart, finishing before 10:00 PM nightly editing window)
def generate_30_slots(total_slots=30):
    slots = []
    start_total = 7 * 60       # 07:00 AM
    end_total = 21 * 60 + 50   # 09:50 PM
    interval = (end_total - start_total) / (total_slots - 1)
    for i in range(total_slots):
        m_total = int(start_total + i * interval)
        h = m_total // 60
        m = m_total % 60
        slots.append((i + 1, h, m))
    return slots

SCHEDULE_SLOTS = generate_30_slots(30)

def find_safe_backup_reel(channel_id, queue_dir, db):
    """
    Auto-Backfill Safety Net:
    Scans the queue directory for ANY unposted, 100% compliant reel.
    Guarantees you NEVER lose daily post quotas due to rejections!
    """
    from core.compliance_guard import is_reel_compliant

    all_vids = sorted(glob.glob(os.path.join(queue_dir, "ready_*.mp4")))
    for vf in all_vids:
        if vf.endswith(".tg_comp.mp4"):
            continue
        mf = vf.rsplit(".", 1)[0] + ".json"
        if not os.path.exists(mf):
            continue
        try:
            with open(mf, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            shortcode = meta.get("shortcode")
            if not shortcode or db.is_reel_processed(shortcode) or db.is_reel_rejected(shortcode):
                continue
            is_safe, _ = is_reel_compliant(meta.get("title", ""), meta.get("hook_pill", ""), meta.get("caption", ""))
            if is_safe:
                print(f"🔄 [Auto-Backfill Safety Net] Using backup reel: '{meta.get('title')}'")
                return vf, meta
        except:
            continue
    return None, None

def publish_channel_slot(channel_id, display_name, handle, slot_num, queue_dir):
    config = get_channel_config(channel_id)
    if not config.get("enabled", True):
        return False

    from core.iron_shield import CircuitBreaker
    is_locked, lock_reason = CircuitBreaker.is_channel_locked(channel_id)
    if is_locked:
        print(f"🛑 [Circuit Breaker Lock] {display_name} is locked: {lock_reason}. Skipping slot #{slot_num}.")
        return False

    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))
    db = ChannelDatabase(config["runtime"]["db_path"])

    vid_pattern = os.path.join(queue_dir, f"ready_{slot_num:02d}_*.mp4")
    meta_pattern = os.path.join(queue_dir, f"ready_{slot_num:02d}_*.json")

    vid_files = glob.glob(vid_pattern)
    meta_files = glob.glob(meta_pattern)

    candidate_vid = None
    candidate_meta = None

    if vid_files and meta_files:
        try:
            with open(meta_files[0], 'r', encoding='utf-8') as f:
                m = json.load(f)
            shortcode = m.get("shortcode")
            if shortcode and not db.is_reel_processed(shortcode) and not db.is_reel_rejected(shortcode):
                from core.compliance_guard import is_reel_compliant
                is_safe, reason = is_reel_compliant(m.get("title", ""), m.get("hook_pill", ""), m.get("caption", ""))
                if is_safe:
                    candidate_vid = vid_files[0]
                    candidate_meta = m
                else:
                    print(f"🛑 [Compliance Guard BLOCKED] Slot #{slot_num} rejected: {reason}. Finding safe backup...")
        except Exception as e:
            pass

    # If slot video is missing or was rejected -> AUTO-BACKFILL!
    if not candidate_vid:
        candidate_vid, candidate_meta = find_safe_backup_reel(channel_id, queue_dir, db)

    if not candidate_vid or not candidate_meta:
        print(f"[{display_name}] No compliant backup video found for slot #{slot_num}.")
        return False

    vid_file = candidate_vid
    meta = candidate_meta
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
                return True
            else:
                err_msg = pub_res.get("error", "Unknown error") if pub_res else "No response"
                print(f"⚠️ [{display_name}] Meta API response note: {err_msg}")
        else:
            print(f"⚠️ [{display_name}] Telegram upload or publisher not configured properly.")
    except Exception as e:
        print(f"❌ Error publishing slot #{slot_num} for {channel_id}: {e}")
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
    print("Architecture: Database-Backed Persistent Scheduler")
    print("Anti-Spam Pacing: Minimum 7-min gap per channel")
    print("========================================================\n")

    last_post_time = {}

    while True:
        try:
            now = datetime.now()

            # Posting window is strictly 07:00 AM to 10:00 PM (10 PM to 2 AM is pre-baking window)
            if now.hour < 7 or now.hour >= 22:
                time.sleep(60)
                continue

            # Calculate target slots that should be published by current wall-clock time
            elapsed_slots = [
                s for s, h, m in SCHEDULE_SLOTS 
                if (now.hour > h) or (now.hour == h and now.minute >= m)
            ]
            target_slots_by_now = len(elapsed_slots)

            for ch_id, name, handle in CHANNELS:
                try:
                    cfg = get_channel_config(ch_id)
                    db = ChannelDatabase(cfg["runtime"]["db_path"])
                    posted_today_count = db.get_today_count()

                    # If this channel is behind the scheduled target and hasn't hit 30:
                    if posted_today_count < target_slots_by_now and posted_today_count < 30:
                        last_time = last_post_time.get(ch_id, 0)
                        # Ensure at least 420 seconds (7 minutes) gap between consecutive posts on the SAME channel
                        if time.time() - last_time >= 420:
                            next_slot = posted_today_count + 1
                            queue_dir = os.path.join(cfg["runtime"]["workspace_dir"], "tomorrow_reels")
                            print(f"\n⏰ [Schedule Trigger] {name}: Posted {posted_today_count}/30 (Target by now: {target_slots_by_now}). Dispatching Slot #{next_slot}...")
                            
                            success = publish_channel_slot(ch_id, name, handle, next_slot, queue_dir)
                            if success:
                                last_post_time[ch_id] = time.time()
                                # Small stagger of 20 seconds between different channels
                                time.sleep(20)
                            else:
                                # On temporary failure, back off 3 minutes before retrying this channel
                                last_post_time[ch_id] = time.time() - 240
                except Exception as ch_err:
                    print(f"⚠️ Error in dispatcher channel loop for {ch_id}: {ch_err}")
                    time.sleep(5)

            # Heartbeat check every 30 seconds
            time.sleep(30)
        except Exception as loop_err:
            print(f"⚠️ Unexpected error in master dispatcher loop: {loop_err}")
            time.sleep(30)

if __name__ == '__main__':
    run_all_4channels_dispatcher()
