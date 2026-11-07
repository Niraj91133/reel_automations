import os
import sys
import json
import sqlite3
import shutil
import glob
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASES_DIR = os.path.join(BASE_DIR, "databases")
TP_DB = os.path.join(DATABASES_DIR, "trading_pulse_history.db")
TR24_DB = os.path.join(DATABASES_DIR, "trading_road24_history.db")

TR24_ARCHIVE = r"C:\reel_cache\trading_road24\archive_posted"
TP_ARCHIVE = r"C:\reel_cache\trading_pulse\archive_posted"
TP_TOMORROW = r"C:\reel_cache\trading_pulse\tomorrow_reels"

os.makedirs(TR24_ARCHIVE, exist_ok=True)

def sync_all_trading_reels():
    print("========================================================")
    print("  🔄 SYNCING ALL 31 TRADING REELS FOR @trading_road24")
    print("========================================================")

    # 1. Fetch all trading_pulse reels
    conn_tp = sqlite3.connect(TP_DB)
    c_tp = conn_tp.cursor()
    c_tp.execute("SELECT id, shortcode, username, title, permalink FROM processed_reels ORDER BY id ASC")
    tp_reels = c_tp.fetchall()
    conn_tp.close()

    # 2. Fetch already posted on trading_road24
    conn_24 = sqlite3.connect(TR24_DB)
    c_24 = conn_24.cursor()
    c_24.execute("SELECT shortcode FROM processed_reels")
    posted_tr24 = set(r[0] for r in c_24.fetchall())
    conn_24.close()

    print(f"Total Trading Pulse Reels: {len(tp_reels)}")
    print(f"Already Posted on @trading_road24: {len(posted_tr24)}")
    print(f"Pending to Backfill: {len(tp_reels) - len(posted_tr24)}\n")

    # Map existing files in TP archive and tomorrow
    tp_archive_json = glob.glob(os.path.join(TP_ARCHIVE, "ready_*.json"))
    tp_archive_map = {}
    for jf in tp_archive_json:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                d = json.load(f)
                sc = d.get("shortcode")
                if sc:
                    tp_archive_map[sc] = (jf, jf.replace(".json", ".mp4"))
        except:
            pass

    tp_tomorrow_json = glob.glob(os.path.join(TP_TOMORROW, "ready_*.json"))
    for jf in tp_tomorrow_json:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                d = json.load(f)
                sc = d.get("shortcode")
                if sc:
                    tp_archive_map[sc] = (jf, jf.replace(".json", ".mp4"))
        except:
            pass

    synced_count = 0
    downloaded_count = 0

    import yt_dlp

    for idx, sc, creator, title, permalink in tp_reels:
        status = "ALREADY_POSTED" if sc in posted_tr24 else "PENDING"
        dest_vid = os.path.join(TR24_ARCHIVE, f"ready_{idx:02d}_{sc}.mp4")
        dest_json = os.path.join(TR24_ARCHIVE, f"ready_{idx:02d}_{sc}.json")

        if os.path.exists(dest_vid) and os.path.exists(dest_json):
            print(f"[{idx:02d}/31] {sc} -> Ready on disk ({status}): {title.splitlines()[0]}")
            synced_count += 1
            continue

        # Check if available in TP archives
        if sc in tp_archive_map and os.path.exists(tp_archive_map[sc][1]):
            src_json, src_vid = tp_archive_map[sc]
            shutil.copy2(src_vid, dest_vid)
            shutil.copy2(src_json, dest_json)
            print(f"[{idx:02d}/31] {sc} -> Copied from Trading Pulse archive ({status}): {title.splitlines()[0]}")
            synced_count += 1
            continue

        # Download from live Instagram permalink
        if permalink and permalink.startswith("http"):
            print(f"[{idx:02d}/31] {sc} -> Downloading via yt_dlp from {permalink}...")
            ydl_opts = {
                'outtmpl': dest_vid,
                'quiet': True,
                'no_warnings': True,
                'format': 'mp4/best'
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(permalink, download=True)
                    caption = info.get('description', f"Insights from @{creator}\n\n⚠️ Disclaimer: For educational purposes only. Not financial or SEBI advice.")
                    meta = {
                        "shortcode": sc,
                        "creator": creator or "creator",
                        "title": title,
                        "caption": caption,
                        "hook_pill": "TRADING EDUCATION"
                    }
                    with open(dest_json, "w", encoding="utf-8") as jf:
                        json.dump(meta, jf, indent=2, ensure_ascii=False)
                    print(f"  ✅ Downloaded & metadata saved successfully ({os.path.getsize(dest_vid)/(1024*1024):.2f} MB)")
                    downloaded_count += 1
                    synced_count += 1
            except Exception as e:
                print(f"  ❌ Error downloading {sc}: {e}")
        else:
            print(f"[{idx:02d}/31] {sc} -> No permalink available to download.")

    print("\n========================================================")
    print(f"🎯 SYNC COMPLETE: {synced_count}/31 Reels Ready in {TR24_ARCHIVE}")
    print(f"📥 Downloaded from Instagram: {downloaded_count}")
    print("========================================================")

if __name__ == "__main__":
    sync_all_trading_reels()

