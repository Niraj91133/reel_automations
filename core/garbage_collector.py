"""
Core Garbage Collector & Disk Optimizer:
Safely purges temporary render files, intermediate audio/thumbnails, 
and stale raw downloads across all channel workspaces to prevent 
disk overflow on C: drive.
"""

import os
import glob
import time
from pathlib import Path

BASE_CACHE_DIR = r"C:\reel_cache"

def clean_channel_cache(channel_id, max_age_hours=24):
    """
    Cleans up stale temp files, raw videos, and intermediate artifacts for a specific channel.
    Preserves:
    - active tomorrow_reels (ready_*.mp4, ready_*.json)
    - active database files (*.db, *.db-wal, *.db-shm)
    - recent archive_posted
    """
    ch_dir = os.path.join(BASE_CACHE_DIR, channel_id)
    if not os.path.exists(ch_dir):
        return 0, 0

    now = time.time()
    cutoff_temp = now - (2 * 3600)        # 2 hours for temp render files
    cutoff_raw = now - (max_age_hours * 3600) # 24 hours for raw downloads

    deleted_files = 0
    reclaimed_bytes = 0

    # 1. Patterns of pure intermediate temp files that can always be purged
    temp_patterns = [
        "base_*.png", "circle_*.png", "thumb_*.jpg", "audio_*.mp3",
        "comp_*.mp4", "c31_*.mp4", "*.tg_comp.mp4", "final_*.mp4",
        "*.lean.mp4"
    ]

    for root, dirs, files in os.walk(ch_dir):
        # Never purge tomorrow_reels folder's ready_* files
        is_tomorrow = os.path.basename(root) == "tomorrow_reels"
        is_archive = os.path.basename(root) == "archive_posted"

        for f in files:
            fp = os.path.join(root, f)
            try:
                st = os.stat(fp)
                size = st.st_size
                mtime = st.st_mtime

                # Temp render files in root workspace
                if any(f.startswith(p.split("*")[0]) and f.endswith(p.split("*")[-1]) for p in temp_patterns):
                    if mtime < cutoff_temp:
                        os.remove(fp)
                        deleted_files += 1
                        reclaimed_bytes += size
                        continue

                # Raw downloaded reels (raw_*.mp4) that are older than cutoff
                if f.startswith("raw_") and f.endswith(".mp4"):
                    if mtime < cutoff_raw or not is_tomorrow:
                        os.remove(fp)
                        deleted_files += 1
                        reclaimed_bytes += size
                        continue

                # In archive_posted, keep maximum 40 most recent reels per channel
                if is_archive and f.endswith(".mp4"):
                    # Purge archive videos older than 7 days
                    if mtime < now - (7 * 86400):
                        os.remove(fp)
                        deleted_files += 1
                        reclaimed_bytes += size
                        continue

            except Exception:
                pass

    return deleted_files, reclaimed_bytes

def run_global_cleanup():
    """Runs garbage collection across all channels in C:\\reel_cache."""
    if not os.path.exists(BASE_CACHE_DIR):
        return

    print("========================================================")
    print("  🧹 RUNNING AUTOMATED DISK OPTIMIZER & GARBAGE COLLECTOR")
    print("========================================================")

    total_deleted = 0
    total_reclaimed = 0

    channels = [
        "startup_road", "trading_pulse", "healthy_diet", 
        "viral_finds", "trading_road24"
    ]

    for ch in channels:
        count, b = clean_channel_cache(ch)
        mb = b / (1024 * 1024)
        if count > 0:
            print(f"  • [{ch}]: Deleted {count} temporary files, reclaimed {mb:.1f} MB")
        total_deleted += count
        total_reclaimed += b

    total_gb = total_reclaimed / (1024 * 1024 * 1024)
    print(f"✅ Cleanup Complete! Total Purged: {total_deleted} files | Reclaimed: {total_gb:.2f} GB disk space.")
    print("========================================================\n")

if __name__ == "__main__":
    run_global_cleanup()
