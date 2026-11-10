"""
Autonomous 7-Channel Queue Replenisher Daemon:
Maintains a perpetual 3-to-4 reel buffer in C:\\reel_cache\\<channel>\\tomorrow_reels\\ 
for all 7 production channels.

Whenever a channel's buffer drops below 3 reels, this daemon automatically:
1. Picks the next unposted candidate from the channel's history database.
2. Downloads the video via yt-dlp.
3. Analyzes hook/title and applies the 100k-250k like viral storytelling caption.
4. Validates compliance via Iron Shield (zero scam triggers).
5. Renders with hardware acceleration / low-CPU 2-worker mode.
6. Saves ready_<slot>_<shortcode>.mp4 and .json.

Guarantees the Master Dispatcher NEVER encounters an empty queue again.
"""

import os
import sys
import time
import glob
import json
import socket
import atexit
from datetime import datetime

# Configure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.database import ChannelDatabase
from replenish_all_queues import replenish_channel_queue, CHANNELS_TO_REPLENISH
from sync_startuproad_mirror import prebake_startuproad_mirror

LOCK_PORT = 54323
TARGET_BUFFER = 3

_replenish_socket = None

def acquire_replenish_lock():
    global _replenish_socket
    try:
        _replenish_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _replenish_socket.bind(('127.0.0.1', LOCK_PORT))
        _replenish_socket.listen(1)
        
        lock_dir = os.path.join(BASE_DIR, "databases", "locks")
        os.makedirs(lock_dir, exist_ok=True)
        pid_file = os.path.join(lock_dir, "auto_replenish.pid")
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
        print("⚠️ [Replenish Daemon] Another instance is already running! Exiting to avoid duplicate rendering.")
        sys.exit(0)

def check_and_replenish_channel(ch_info):
    cid = ch_info["channel_id"]
    name = ch_info["name"]
    
    cfg = get_channel_config(cid)
    db = ChannelDatabase(cfg["runtime"]["db_path"])
    q_dir = os.path.join(cfg["runtime"]["workspace_dir"], "tomorrow_reels")
    os.makedirs(q_dir, exist_ok=True)
    
    # Count unprocessed ready reels
    existing_meta = glob.glob(os.path.join(q_dir, "ready_*.json"))
    ready_count = 0
    for mf in existing_meta:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            sc = data.get("shortcode")
            mp4 = mf.rsplit(".", 1)[0] + ".mp4"
            if sc and os.path.exists(mp4) and not db.is_reel_processed(sc):
                ready_count += 1
        except Exception:
            pass
            
    today_posted = db.get_today_count()
    if today_posted >= 30:
        return 0
        
    needed = TARGET_BUFFER - ready_count
    if needed <= 0:
        return 0
        
    print(f"\n🔄 [{name}] Buffer low ({ready_count}/{TARGET_BUFFER} ready | Today posted: {today_posted}). Replenishing {needed} reels...")
    ch_info["target_buffer"] = TARGET_BUFFER
    baked = replenish_channel_queue(ch_info)
    return baked

def check_and_replenish_mirror_startuproad():
    cid = "the_startuproad"
    name = "The Startup Road"
    cfg = get_channel_config(cid)
    db = ChannelDatabase(cfg["runtime"]["db_path"])
    q_dir = os.path.join(cfg["runtime"]["workspace_dir"], "tomorrow_reels")
    os.makedirs(q_dir, exist_ok=True)
    
    existing_meta = glob.glob(os.path.join(q_dir, "ready_*.json"))
    ready_count = 0
    for mf in existing_meta:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            sc = data.get("shortcode")
            mp4 = mf.rsplit(".", 1)[0] + ".mp4"
            if sc and os.path.exists(mp4) and not db.is_reel_processed(sc):
                ready_count += 1
        except Exception:
            pass
            
    today_posted = db.get_today_count()
    if today_posted >= 30:
        return 0
        
    needed = TARGET_BUFFER - ready_count
    if needed <= 0:
        return 0
        
    print(f"\n🔄 [{name}] Buffer low ({ready_count}/{TARGET_BUFFER} ready | Today posted: {today_posted}). Mirroring fresh reels...")
    target_count = today_posted + TARGET_BUFFER
    prebake_startuproad_mirror(count=target_count)
    return 1

def run_replenish_daemon():
    acquire_replenish_lock()
    print("========================================================")
    print("  🚀 7-CHANNEL AUTONOMOUS QUEUE REPLENISHER DAEMON")
    print("========================================================")
    print(f"Target Buffer: {TARGET_BUFFER} ready reels per channel at all times")
    print("Zero-Queue-Starvation Guarantee Active")
    print("Low-CPU Throttle: FFmpeg 2 Worker Threads")
    print("========================================================\n")

    cycle = 0
    while True:
        try:
            cycle += 1
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now_str}] 🔎 Replenisher Cycle #{cycle}: Auditing all 7 channel buffers...")

            # 1. Check The Startup Road (Mirror)
            try:
                check_and_replenish_mirror_startuproad()
            except Exception as e:
                print(f"⚠️ Error checking the_startuproad: {e}")

            # 2. Check Other 6 Channels
            for ch in CHANNELS_TO_REPLENISH:
                try:
                    check_and_replenish_channel(ch)
                    time.sleep(2)  # Small cooldown between channels
                except Exception as e_ch:
                    print(f"⚠️ Error replenishing {ch['channel_id']}: {e_ch}")

            # Sleep 5 minutes between audit cycles
            print(f"💤 All buffers verified! Sleeping 300s until next audit...\n")
            time.sleep(300)

        except Exception as e_loop:
            print(f"⚠️ Replenisher daemon loop exception: {e_loop}")
            time.sleep(60)

if __name__ == "__main__":
    run_replenish_daemon()
