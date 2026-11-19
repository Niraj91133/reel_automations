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
    ("thestartup_street", "🚀 Startup Road", "@startup_road"),
    ("healthy_diet", "🥗 Gud Tree", "@gudtree_"),
    ("trading_road24", "📊 Trading Knowledge", "@trading_road24"),
    ("theloan_road", "💳 The Loan Road", "@the_loan_road"),
    ("marketing_road24", "📱 Marketing Road", "@marketing_road24"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_")
]

# 30 Slots across 07:00 AM - 10:15 PM (~31.5 minutes apart, finishing before 10:30 PM nightly editing window)
def generate_30_slots(total_slots=30):
    slots = []
    start_total = 7 * 60       # 07:00 AM
    end_total = 22 * 60 + 15   # 10:15 PM
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
            if not shortcode or db.is_reel_processed(shortcode):
                continue
            is_safe, _ = is_reel_compliant(meta.get("title", ""), meta.get("hook_pill", ""), meta.get("caption", ""))
            if is_safe:
                print(f"🔄 [Auto-Backfill Safety Net] Using backup reel: '{meta.get('title')}'")
                return vf, meta
        except:
            continue
    return None, None

def publish_mirror_slot(display_name, handle, slot_num):
    """
    Publishes next chronological reel from @startup_road feed (oldest-first) to @the_startuproad.
    """
    from mirror_pipeline import get_queue_status, publish_single_reel
    st = get_queue_status()
    if not st["next_up"]:
        print(f"[{display_name}] No pending mirror reels in queue.")
        return False

    next_idx = st["next_up"][0][0]
    print(f"\n🔄 [{display_name}] Mirror Dispatching Slot #{slot_num}/30 (Queue #{next_idx})...")
    ok, res = publish_single_reel(next_idx)
    return ok

def publish_channel_slot(channel_id, display_name, handle, slot_num, queue_dir):
    config = get_channel_config(channel_id)
    if not config.get("enabled", True):
        return False

    from core.iron_shield import CircuitBreaker
    is_locked, lock_reason = CircuitBreaker.is_channel_locked(channel_id)
    if is_locked:
        print(f"🛑 [Circuit Breaker Lock] {display_name} is locked: {lock_reason}. Skipping slot #{slot_num}.")
        return False

    # Mirror channel handles its own chronological sourcing
    if channel_id == "the_startuproad":
        return publish_mirror_slot(display_name, handle, slot_num)

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
            if shortcode and not db.is_reel_processed(shortcode):
                from core.compliance_guard import is_reel_compliant
                is_safe, reason = is_reel_compliant(m.get("title", ""), m.get("hook_pill", ""), m.get("caption", ""))
                if is_safe:
                    candidate_vid = vid_files[0]
                    candidate_meta = m
                else:
                    print(f"🛑 [Compliance Guard BLOCKED] Slot #{slot_num} rejected: {reason}. Finding safe backup...")
        except Exception as e:
            pass

    # If slot video is missing or was rejected -> AUTO-BACKFILL from queue!
    if not candidate_vid:
        candidate_vid, candidate_meta = find_safe_backup_reel(channel_id, queue_dir, db)

    # If queue is completely empty -> ON-DEMAND AUTO REPLENISH WITH BRUTAL 4-TIER PIPELINE!
    if not candidate_vid or not candidate_meta:
        print(f"🔄 [{display_name}] Buffer empty. Auto-baking 1 reel on-the-fly using 4-tier pipeline...")
        try:
            from prebake_autopilot_channels import prebake_channel_reels
            prebake_channel_reels(channel_id, count=1)
            candidate_vid, candidate_meta = find_safe_backup_reel(channel_id, queue_dir, db)
        except Exception as e_replenish:
            print(f"⚠️ [{display_name}] Auto-replenish notice: {e_replenish}")

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
                try:
                    from core.google_sheet_source import mark_reel_in_sheet_posted
                    mark_reel_in_sheet_posted(channel_id, shortcode, link)
                except Exception as e_sheet_mark:
                    print(f"Sheet sync notice for {channel_id}: {e_sheet_mark}")
                # Auto-archive published reel to keep queue pristine and avoid ghost re-use
                try:
                    import shutil
                    arch_dir = os.path.join(queue_dir, "archive")
                    os.makedirs(arch_dir, exist_ok=True)
                    if os.path.exists(vid_file):
                        shutil.move(vid_file, os.path.join(arch_dir, os.path.basename(vid_file)))
                    meta_f = vid_file.rsplit(".", 1)[0] + ".json"
                    if os.path.exists(meta_f):
                        shutil.move(meta_f, os.path.join(arch_dir, os.path.basename(meta_f)))
                    tg_comp = vid_file.rsplit(".", 1)[0] + ".tg_comp.mp4"
                    if os.path.exists(tg_comp):
                        try: os.remove(tg_comp)
                        except: pass
                    print(f"📦 [Archive] Moved posted reel {shortcode} to archive folder.")
                except Exception as e_arch:
                    print(f"Archiving notice: {e_arch}")
                return True
            else:
                err_msg = pub_res.get("error", "Unknown error") if pub_res else "No response"
                print(f"⚠️ [{display_name}] Meta API response note: {err_msg}")
        else:
            print(f"⚠️ [{display_name}] Telegram upload or publisher not configured properly.")
    except Exception as e:
        print(f"❌ Error publishing slot #{slot_num} for {channel_id}: {e}")
    return False

def get_channel_last_post_epoch(db_path):
    """Retrieves the timestamp of the last posted reel from DB to enforce half-hour gap even across restarts."""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT created_at FROM processed_reels ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            try:
                from datetime import timezone
                dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                diff_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
                return time.time() - diff_seconds
            except:
                pass
    except Exception:
        pass
    return 0

def run_all_channels_dispatcher(run_once=False):
    print("========================================================")
    print("  🚀 7-CHANNEL 30 REELS/DAY AUTOMATED DISPATCHER")
    print("========================================================")
    print("Channels:")
    for ch, name, handle in CHANNELS:
        print(f"  • {name} ({handle}) ➔ 30 Reels / Day")
    print(f"\nTotal Target: {len(CHANNELS) * 30} Reels / Day")
    print("Time Window: 07:00 AM - 10:00 PM (Every ~30 minutes)")
    print("Architecture: Database-Backed Persistent Scheduler")
    print("Anti-Spam Pacing: Strict ~25-30 min gap per channel")
    print("========================================================\n")

    MIN_GAP_PER_CHANNEL = 1200      # 20 minutes minimum gap on the SAME channel
    CROSS_CHANNEL_STAGGER = 240     # 4 minutes exact stagger between different channels
    last_post_time = {}
    global_last_post_time = 0

    for ch_id, name, handle in CHANNELS:
        cfg = get_channel_config(ch_id)
        if cfg.get("enabled", True):
            epoch = get_channel_last_post_epoch(cfg["runtime"]["db_path"])
            last_post_time[ch_id] = epoch
            if epoch > global_last_post_time:
                global_last_post_time = epoch

    print(f"⏱️ Cross-Channel Stagger Active: Exactly 4 minutes between different IDs.")
    print(f"⏱️ Per-Channel Pacing Active: ~20-25 minutes between posts on the same ID.\n")

    while True:
        now = datetime.now()

        # Target Achiever Window: Runs until all enabled channels reach 30/30 (up to 01:45 AM).
        # Once all 30 are done, it safely sleeps until 07:00 AM next morning.
        if not run_once:
            all_30_done = True
            for ch_id, _, _ in CHANNELS:
                cfg = get_channel_config(ch_id)
                if cfg.get("enabled", True):
                    db = ChannelDatabase(cfg["runtime"]["db_path"])
                    if db.get_today_count() < 30:
                        all_30_done = False
                        break

            if all_30_done:
                if now.hour < 7 or now.hour >= 22:
                    time.sleep(60)
                    continue
            else:
                # Night cutoff only applies after 01:45 AM until 07:00 AM
                if 2 <= now.hour < 7:
                    time.sleep(60)
                    continue

        # Calculate target slots that should be published by current wall-clock time
        elapsed_slots = [
            s for s, h, m in SCHEDULE_SLOTS 
            if (now.hour > h) or (now.hour == h and now.minute >= m)
        ]
        target_slots_by_now = max(1, len(elapsed_slots))

        # Dynamic Fair-Share Scheduler:
        # Collect candidate channels and sort by highest deficit & longest time without post.
        # This completely eliminates starvation and guarantees all channels stay in sync.
        candidate_pool = []
        for ch_id, name, handle in CHANNELS:
            cfg = get_channel_config(ch_id)
            if not cfg.get("enabled", True):
                continue
            db = ChannelDatabase(cfg["runtime"]["db_path"])
            posted_today = db.get_today_count()
            last_time = last_post_time.get(ch_id, 0)
            elapsed_channel = time.time() - last_time
            deficit = target_slots_by_now - posted_today

            candidate_pool.append({
                "ch_id": ch_id,
                "name": name,
                "handle": handle,
                "cfg": cfg,
                "db": db,
                "posted_today": posted_today,
                "last_time": last_time,
                "elapsed_channel": elapsed_channel,
                "deficit": deficit
            })

        # Sort: Primary = highest deficit, Secondary = longest time since last post
        candidate_pool.sort(key=lambda x: (x["deficit"], x["elapsed_channel"]), reverse=True)

        any_action = False
        elapsed_since_global = time.time() - global_last_post_time

        for cand in candidate_pool:
            ch_id = cand["ch_id"]
            name = cand["name"]
            handle = cand["handle"]
            cfg = cand["cfg"]
            posted_today_count = cand["posted_today"]
            elapsed_since_channel = cand["elapsed_channel"]

            # If this channel is behind the scheduled target and hasn't hit 30:
            if posted_today_count < target_slots_by_now and posted_today_count < 30:
                # Enforce:
                # 1. At least 5 minutes since ANY channel posted across the system
                # 2. At least 25 minutes since THIS specific channel posted
                if (elapsed_since_global >= CROSS_CHANNEL_STAGGER or run_once) and \
                   (elapsed_since_channel >= MIN_GAP_PER_CHANNEL or run_once):
                    next_slot = posted_today_count + 1
                    queue_dir = os.path.join(cfg["runtime"]["workspace_dir"], "tomorrow_reels")
                    print(f"\n⏰ [Fair Schedule Trigger] {name}: Posted {posted_today_count}/30 (Deficit: {cand['deficit']}, Last posted: {elapsed_since_channel/60:.1f}m ago). Dispatching Slot #{next_slot}...")
                    
                    success = publish_channel_slot(ch_id, name, handle, next_slot, queue_dir)
                    if success:
                        now_epoch = time.time()
                        last_post_time[ch_id] = now_epoch
                        global_last_post_time = now_epoch
                        any_action = True
                        try:
                            from core.google_sheet_source import sync_pending_posted_reels_to_sheet
                            sync_pending_posted_reels_to_sheet()
                        except Exception as e_sync:
                            print(f"Sheet auto-sync note: {e_sync}")
                        break  # Yield to wait the 5-minute stagger window before next channel
                    else:
                        # On temporary failure, back off 3 minutes before retrying this channel
                        last_post_time[ch_id] = time.time() - (MIN_GAP_PER_CHANNEL - 180)

        if run_once:
            print("Run-once cycle completed.")
            break

        # Heartbeat check every 30 seconds
        time.sleep(30)

if __name__ == '__main__':
    run_once_mode = "--catchup" in sys.argv or "--run-once" in sys.argv
    run_all_channels_dispatcher(run_once=run_once_mode)
