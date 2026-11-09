import os
import sys
import time
import glob
import json
import random
import socket
import atexit
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase
from core.channel_lock import channel_lock
from core.garbage_collector import run_global_cleanup

# 5 Production Channels with Staggered Offsets (Every 6 minutes apart)
CHANNELS = [
    ("startup_road", "💼 Startup Road", "@startup_road", 0),       # :00 / :30
    ("trading_pulse", "📈 Trading Road", "@trading_road_", 6),     # :06 / :36
    ("healthy_diet", "🥗 Gudtree", "@gudtree_", 12),               # :12 / :42
    ("viral_finds", "🛍️ Trending Road", "@trending_road", 18),     # :18 / :48
    ("trading_road24", "📈 Trading Road 24", "@trading_road24", 24) # :24 / :54
]

# Strict timing constants
MIN_CHANNEL_INTERVAL_SECONDS = 25 * 60  # Minimum 25 minutes between posts on SAME channel
DAILY_TARGET_PER_CHANNEL = 30           # Exactly 30 reels per day per channel
START_HOUR = 7                          # 07:00 AM IST
LOCK_PORT = 54321                       # OS-level Singleton socket port

_singleton_socket = None

def acquire_singleton_lock():
    """
    Enforces a strict kernel-level singleton lock.
    Guarantees NEVER MORE THAN ONE master dispatcher process can run at the same time.
    Prevents duplicate posts 100%.
    """
    global _singleton_socket
    try:
        _singleton_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _singleton_socket.bind(('127.0.0.1', LOCK_PORT))
        _singleton_socket.listen(1)
        
        lock_dir = os.path.join(BASE_DIR, "databases", "locks")
        os.makedirs(lock_dir, exist_ok=True)
        pid_file = os.path.join(lock_dir, "master_dispatcher.pid")
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
            
        def cleanup_pid():
            try:
                if os.path.exists(pid_file):
                    os.remove(pid_file)
            except Exception:
                pass
        atexit.register(cleanup_pid)
        return True
    except OSError:
        print(f"\n🛑 [SINGLETON LOCK ACTIVE] Another master dispatcher instance is already running (Port {LOCK_PORT} busy)!")
        print("🛑 Aborting this instance immediately to guarantee ZERO DUPLICATE POSTS.\n")
        sys.exit(0)

def find_safe_backup_reel(channel_id, queue_dir, db):
    """
    Auto-Backfill Safety Net:
    Scans the queue directory for ANY unposted, 100% compliant reel with unique AI titles.
    """
    from core.compliance_guard import is_reel_compliant

    all_vids = sorted(glob.glob(os.path.join(queue_dir, "ready_*.mp4")))
    if not all_vids:
        archive_dir = os.path.join(os.path.dirname(queue_dir), "archive_posted")
        if os.path.exists(archive_dir):
            all_vids = sorted(glob.glob(os.path.join(archive_dir, "ready_*.mp4")))
            
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
            title = meta.get("title", "")
            
            # Reject stale fallback titles
            if any(stale in title for stale in ["HOW SMART MONEY TRAPS", "THE HIDDEN INGREDIENTS", "BUSINESS BREAKDOWN: SCALING BLUEPRINT"]):
                continue
                
            if not shortcode or db.is_reel_processed(shortcode) or db.is_reel_rejected(shortcode):
                continue
            
            # Instagram Reels duration safety: Must be <= 90 seconds
            from core.video_engine import get_video_duration
            if get_video_duration(vf) > 90.0:
                continue

            is_safe, _ = is_reel_compliant(title, meta.get("hook_pill", ""), meta.get("caption", ""))
            if is_safe:
                print(f"🔄 [Auto-Backfill Safety Net] Using backup reel: '{title}'")
                return vf, meta
        except Exception:
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

    # Check Meta Daily Publishing Quota & Velocity Lock
    import requests
    try:
        q_url = f"https://graph.facebook.com/v21.0/{creds.get('instagram_account_id')}/content_publishing_limit"
        r_q = requests.get(q_url, params={"access_token": creds.get("page_access_token"), "fields": "quota_usage,config"}, timeout=5)
        if r_q.status_code == 200:
            q_data = r_q.json().get("data", [{}])[0]
            usage = q_data.get("quota_usage", 0)
            total = q_data.get("config", {}).get("quota_total", 100)
            if usage >= total - 3:
                print(f"🛑 [Quota Safety Lock] {display_name} has used {usage}/{total} today. Pausing to avoid Meta API restriction.")
                return False
    except Exception:
        pass

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
            title = m.get("title", "")
            
            # Reject stale fallback titles
            if any(stale in title for stale in ["HOW SMART MONEY TRAPS", "THE HIDDEN INGREDIENTS", "BUSINESS BREAKDOWN: SCALING BLUEPRINT"]):
                print(f"🧹 Purging stale fallback reel for Slot #{slot_num}: {title}")
                try:
                    os.remove(meta_files[0])
                    os.remove(vid_files[0])
                except Exception:
                    pass
            elif shortcode and not db.is_reel_processed(shortcode) and not db.is_reel_rejected(shortcode):
                from core.compliance_guard import is_reel_compliant
                is_safe, reason = is_reel_compliant(title, m.get("hook_pill", ""), m.get("caption", ""))
                if is_safe:
                    candidate_vid = vid_files[0]
                    candidate_meta = m
                else:
                    print(f"🛑 [Compliance Guard BLOCKED] Slot #{slot_num} rejected: {reason}. Finding safe backup...")
        except Exception:
            pass

    # If slot video is missing or was rejected -> AUTO-BACKFILL!
    if not candidate_vid:
        candidate_vid, candidate_meta = find_safe_backup_reel(channel_id, queue_dir, db)

    if not candidate_vid or not candidate_meta:
        print(f"🔄 [{display_name}] Queue empty for slot #{slot_num}! Triggering On-The-Fly Auto-Bake...")
        try:
            from prebake_autopilot_channels import prebake_channel_reels
            prebake_channel_reels(channel_id, count=slot_num)
            candidate_vid, candidate_meta = find_safe_backup_reel(channel_id, queue_dir, db)
        except Exception as e_bake:
            print(f"⚠️ Error during on-the-fly bake for {display_name}: {e_bake}")

    if not candidate_vid or not candidate_meta:
        print(f"[{display_name}] No compliant backup video found for slot #{slot_num}.")
        return False

    vid_file = candidate_vid
    meta = candidate_meta
    shortcode = meta.get("shortcode")
    title = meta.get("title", f"Post #{slot_num}")
    caption = meta.get("caption", "")
    creator = meta.get("creator", "creator")

    # Dynamic Rich Caption Safety Net: Guarantee multi-paragraph, engaging caption
    from core.caption_engine import generate_rich_caption
    if not caption or len(caption.splitlines()) <= 3 or len(caption) < 150 or "valuable insights" in caption.lower() or "strategic insights for modern" in caption.lower():
        caption = generate_rich_caption(
            channel_id=channel_id,
            title=title,
            hook_pill=meta.get("hook_pill", ""),
            creator=creator
        )
        meta["caption"] = caption

    print(f"\n🚀 [{display_name}] Publishing Slot #{slot_num}/30: {title}...")

    try:
        with channel_lock(channel_id):
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

                    # ZERO-BLOAT PURGE: Immediately delete published video & metadata from disk
                    try:
                        if os.path.exists(vid_file):
                            os.remove(vid_file)
                        meta_path = os.path.splitext(vid_file)[0] + ".json"
                        if os.path.exists(meta_path):
                            os.remove(meta_path)
                        for extra in glob.glob(os.path.splitext(vid_file)[0] + "*"):
                            try: os.remove(extra)
                            except: pass
                        print(f"🧹 [Zero-Bloat Purge] Instantly deleted published reel: {os.path.basename(vid_file)}")
                    except Exception as e_purge:
                        print(f"Note on post-publish purge: {e_purge}")

                    return True
                else:
                    err_msg = pub_res.get("error", "Unknown error") if pub_res else "No response"
                    print(f"⚠️ [{display_name}] Meta API response note: {err_msg}")
            else:
                print(f"⚠️ [{display_name}] Telegram upload or publisher not configured properly.")
    except Exception as e:
        print(f"❌ Error publishing slot #{slot_num} for {channel_id}: {e}")
    return False

def get_slot_scheduled_time(slot_index, offset_minutes):
    """Calculates the scheduled wall-clock datetime for slot_index (1-based)."""
    # Slot 1 starts at 07:00 AM + offset_minutes
    # Slot 2 at 07:30 AM + offset_minutes
    minutes_from_start = (slot_index - 1) * 30 + offset_minutes
    total_minutes = START_HOUR * 60 + minutes_from_start
    h = total_minutes // 60
    m = total_minutes % 60
    return h, m

def run_all_4channels_dispatcher():
    acquire_singleton_lock()

    print("========================================================")
    print("  🚀 5-CHANNEL 30 REELS/DAY AUTOMATED MASTER DISPATCHER")
    print("========================================================")
    print("Channels & Staggered Schedule (30-min window per channel):")
    for ch, name, handle, offset in CHANNELS:
        print(f"  • {name} ({handle}) ➔ 30 Reels/Day | Offset: +{offset}m (:{(offset):02d} & :{(offset+30):02d})")
    print(f"\nTotal Posts per Day: {len(CHANNELS) * DAILY_TARGET_PER_CHANNEL} Reels")
    print("Window: 07:00 AM - 11:30 PM (Strict 25-30 min gap per channel)")
    print("Anti-Duplicate: Kernel-Level Singleton Socket Lock (Active)")
    print("Anti-Burst: Database-Backed Minimum 25-Min Interval Enforcement")
    print("========================================================\n")

    last_cleanup_time = 0

    while True:
        try:
            now = datetime.now()
            now_utc = datetime.now(timezone.utc)

            # Automatic Disk Space Garbage Collector (Runs every 4 hours)
            if time.time() - last_cleanup_time > 14400:
                try:
                    run_global_cleanup()
                    last_cleanup_time = time.time()
                except Exception as e_clean:
                    print(f"Note on cleanup: {e_clean}")

            # Sleep during night hours before 07:00 AM
            if now.hour < START_HOUR:
                time.sleep(60)
                continue

            for ch_id, name, handle, offset in CHANNELS:
                try:
                    cfg = get_channel_config(ch_id)
                    db = ChannelDatabase(cfg["runtime"]["db_path"])
                    posted_today = db.get_today_count()

                    # Check if daily quota is already completed
                    if posted_today >= DAILY_TARGET_PER_CHANNEL:
                        continue

                    # 1. Strict Cooldown Guard: Must be >= 25 minutes since channel's last post
                    last_dt = db.get_last_post_datetime()
                    if last_dt:
                        elapsed_seconds = (now_utc - last_dt).total_seconds()
                        if elapsed_seconds < MIN_CHANNEL_INTERVAL_SECONDS:
                            remaining_min = int((MIN_CHANNEL_INTERVAL_SECONDS - elapsed_seconds) / 60)
                            # Still in cooldown, do not dispatch
                            continue

                    # 2. Wall-Clock Schedule Guard: Is the current slot due yet?
                    next_slot = posted_today + 1
                    target_h, target_m = get_slot_scheduled_time(next_slot, offset)
                    is_slot_due = (now.hour > target_h) or (now.hour == target_h and now.minute >= target_m)

                    if not is_slot_due:
                        # Slot is scheduled for a future time today
                        continue

                    # Slot is DUE and Channel Cooldown is MET! Proceed to publish!
                    queue_dir = os.path.join(cfg["runtime"]["workspace_dir"], "tomorrow_reels")
                    print(f"\n⏰ [Schedule Trigger] {name}: Slot #{next_slot}/30 due (Scheduled: {target_h:02d}:{target_m:02d}). Dispatching...")

                    success = publish_channel_slot(ch_id, name, handle, next_slot, queue_dir)
                    if success:
                        print(f"✅ [{name}] Slot #{next_slot} successfully posted! Next slot in ~30 minutes.")
                        # Small 15-second breather before evaluating next channel
                        time.sleep(15)
                    else:
                        print(f"⚠️ [{name}] Slot #{next_slot} dispatch deferred. Retrying next check cycle.")

                except Exception as ch_err:
                    print(f"⚠️ Error in dispatcher channel loop for {ch_id}: {ch_err}")
                    time.sleep(5)

            # Heartbeat check every 30 seconds
            time.sleep(30)
        except Exception as loop_err:
            print(f"⚠️ Master dispatcher loop exception: {loop_err}")
            time.sleep(30)

if __name__ == '__main__':
    run_all_4channels_dispatcher()
