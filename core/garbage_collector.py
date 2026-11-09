"""
Core Garbage Collector & Disk Optimizer (Zero-Bloat Engine):
Guarantees C:\\reel_cache stays permanently lean:
1. Instantly purges any 'archive_posted' or old archive directories.
2. Cross-references database: Deletes ANY file in 'tomorrow_reels' that is already posted.
3. Purges all intermediate ffmpeg render artifacts, audio, and raw downloads.
Only unposted, upcoming reels are ever preserved on disk!
"""

import os
import glob
import time
import shutil
import sqlite3
import json
from pathlib import Path

BASE_CACHE_DIR = r"C:\reel_cache"

def clean_channel_cache(channel_id):
    """
    Cleans up stale temp files, raw videos, and intermediate artifacts for a specific channel.
    Rules:
    - Never keeps already-posted reels (instantly deletes archive_posted and posted tomorrow_reels).
    - Preserves ONLY unposted, upcoming ready_*.mp4 and ready_*.json.
    """
    ch_dir = os.path.join(BASE_CACHE_DIR, channel_id)
    if not os.path.exists(ch_dir):
        return 0, 0

    deleted_files = 0
    reclaimed_bytes = 0

    # 1. Completely destroy archive_posted and any archive_* folders
    for arch_name in ['archive_posted', 'archive_old_generic', 'archive_temp', 'downloads']:
        arch_dir = os.path.join(ch_dir, arch_name)
        if os.path.exists(arch_dir):
            for root, dirs, files in os.walk(arch_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        deleted_files += 1
                        reclaimed_bytes += sz
                    except: pass
            try:
                shutil.rmtree(arch_dir, ignore_errors=True)
            except: pass

    # 2. Check Database: Purge any reel in tomorrow_reels that is ALREADY PROCESSED!
    db_paths = [
        os.path.join("reel_automations-main", "databases", f"{channel_id}_history.db"),
        os.path.join("databases", f"{channel_id}_history.db"),
        os.path.join(r"C:\Users\DHEERAJ\OneDrive\Desktop\Bittu Bhaiya\reel_automations-main\reel_automations-main\databases", f"{channel_id}_history.db")
    ]
    processed_codes = set()
    for db_p in db_paths:
        if os.path.exists(db_p):
            try:
                conn = sqlite3.connect(db_p)
                c = conn.cursor()
                c.execute("SELECT shortcode FROM processed_reels")
                processed_codes.update(r[0] for r in c.fetchall() if r[0])
                conn.close()
                break
            except: pass

    q_dir = os.path.join(ch_dir, "tomorrow_reels")
    if os.path.exists(q_dir):
        for jf in glob.glob(os.path.join(q_dir, "ready_*.json")):
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                sc = meta.get("shortcode")
                if sc and sc in processed_codes:
                    stem = os.path.splitext(jf)[0]
                    for comp in glob.glob(stem + "*"):
                        try:
                            sz = os.path.getsize(comp)
                            os.remove(comp)
                            deleted_files += 1
                            reclaimed_bytes += sz
                        except: pass
            except: pass

        # Purge any leftover raw_*.mp4 files in tomorrow_reels
        for raw in glob.glob(os.path.join(q_dir, "raw_*.mp4")):
            try:
                sz = os.path.getsize(raw)
                os.remove(raw)
                deleted_files += 1
                reclaimed_bytes += sz
            except: pass

    # 3. Purge intermediate temp files in channel root
    for root, dirs, files in os.walk(ch_dir):
        if os.path.basename(root) != "tomorrow_reels":
            for f in files:
                if f.endswith('.mp4') or f.endswith('.png') or f.endswith('.jpg') or f.endswith('.mp3'):
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        os.remove(fp)
                        deleted_files += 1
                        reclaimed_bytes += sz
                    except: pass

    return deleted_files, reclaimed_bytes

def run_global_cleanup():
    """Runs garbage collection across all channels in C:\\reel_cache."""
    if not os.path.exists(BASE_CACHE_DIR):
        return

    print("========================================================")
    print("  🧹 ZERO-BLOAT DISK OPTIMIZER & PERMANENT PURGE ENGINE")
    print("========================================================")

    total_deleted = 0
    total_reclaimed = 0

    channels = [
        "startup_road", "trading_pulse", "healthy_diet", 
        "viral_finds", "trading_road24", "the_loan_road"
    ]

    for ch in channels:
        count, b = clean_channel_cache(ch)
        mb = b / (1024 * 1024)
        if count > 0:
            print(f"  • [{ch}]: Purged {count} posted/temp files, reclaimed {mb:.1f} MB")
        total_deleted += count
        total_reclaimed += b

    total_gb = total_reclaimed / (1024 * 1024 * 1024)
    print(f"✅ Zero-Bloat Complete! Total Purged: {total_deleted} files | Reclaimed: {total_gb:.2f} GB disk space.")
    print("========================================================\n")

if __name__ == "__main__":
    run_global_cleanup()
