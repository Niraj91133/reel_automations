import os
import sys
import time
import json
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dm_scraper import get_shared_reels_from_chat
from core.database import ChannelDatabase
from core.config_manager import get_channel_config

LOCKOUT_FILE = os.path.join(BASE_DIR, "databases/dm_harvest_timestamps.json")

def can_harvest_dm(channel_id):
    """Enforces strict 24-hour window between DM scans to protect account safety."""
    if not os.path.exists(LOCKOUT_FILE):
        return True, 0

    try:
        with open(LOCKOUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        last_str = data.get(channel_id)
        if not last_str:
            return True, 0
            
        last_dt = datetime.strptime(last_str, "%Y-%m-%d %H:%M:%S")
        elapsed = datetime.now() - last_dt
        if elapsed < timedelta(hours=24):
            remaining_hours = 24 - (elapsed.total_seconds() / 3600)
            return False, remaining_hours
        return True, 0
    except Exception:
        return True, 0

def record_harvest_timestamp(channel_id):
    """Records the timestamp of successful DM harvest."""
    try:
        os.makedirs(os.path.dirname(LOCKOUT_FILE), exist_ok=True)
        data = {}
        if os.path.exists(LOCKOUT_FILE):
            with open(LOCKOUT_FILE, "r", encoding="utf-8") as f:
                try: data = json.load(f)
                except: data = {}
                
        data[channel_id] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOCKOUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Timestamp save notice: {e}")

def harvest_daily_30_from_chat(channel_id, target_count=30, force=False):
    """
    Safely harvests up to 30 fresh reels from chat.
    1. Checks 24-hour lockout to guarantee zero bot spam.
    2. Opens chat and scrolls gently from the bottom.
    3. STOPS IMMEDIATELY as soon as target_count (30) is reached.
    4. Closes browser immediately.
    """
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", channel_id)
    
    if not force:
        can_run, remaining = can_harvest_dm(channel_id)
        if not can_run:
            print(f"⏳ [24h Safety Lockout] {display_name} chat was scanned recently. Remaining cooldown: {remaining:.1f} hours.")
            return []

    print(f"\n🔍 [Controlled 24h DM Harvester] Scanning {display_name} chat for strictly {target_count} fresh reels...")
    
    reels = get_shared_reels_from_chat(
        max_count=target_count,
        channel_id=channel_id
    )

    if reels:
        record_harvest_timestamp(channel_id)
        print(f"✅ Successfully harvested {len(reels)}/{target_count} reels. Browser closed. 24h safety lockout activated.")
        
        # Save to channel's hunted pool DB
        db = ChannelDatabase(config["runtime"]["db_path"])
        conn = db.get_connection()
        c = conn.cursor()
        for r in reels:
            sc = r.get("shortcode")
            cr = r.get("creator", "creator")
            try:
                c.execute(
                    "INSERT OR IGNORE INTO hunted_reels (shortcode, source_query, views_text, has_comment_cta, sent_to_raj, creator) VALUES (?, ?, ?, ?, ?, ?)",
                    (sc, "daily_24h_dm", "Chat 24h Approved", 1, 1, f"@{cr}")
                )
            except Exception:
                pass
        conn.commit()
        conn.close()
    else:
        print(f"ℹ️ No fresh reels found in chat for {display_name}.")
        
    return reels

if __name__ == "__main__":
    ch = sys.argv[1] if len(sys.argv) > 1 else "healthy_diet"
    cnt = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    harvest_daily_30_from_chat(ch, cnt, force=True)
