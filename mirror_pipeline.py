import os
import sys
import time
import json
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "databases"
DB_DIR.mkdir(parents=True, exist_ok=True)
MIRROR_DB = DB_DIR / "the_startuproad_mirror.db"

# Source Account: @startup_road
SOURCE_IG_ID = "17841464149880503"
SOURCE_TOKEN = "EAAhE6xjRCjsBTNz2mziqyJPDy00YjyyLCJ8tRpCbHxG7DbdqdpPW0VEEU91zggi9ZBdfwCwEbrxFSagcMc9AWdm00DM6fkxSbLHifYBJKPyHZBsiVgzoWXeBeQrS5i4fZAwYTXxzQrP1XJKhJ9kbZCdWrHu57xGZAZB09xn6PNiZBlT4EbBFUfQMzlmyaRku2ODh3WA"

# Target Account: @the_startuproad
TARGET_IG_ID = "17841454990348896"
TARGET_TOKEN = "EAAhE6xjRCjsBTPbZBNuseVGdaDSJq2Ttq67GiAZBaftY9LsuinTwAZBgswtVyqSmqYBNLk5g5ZBANmCZCWXHQMGkIthjmUUcjwJOBLOyPhNCpZCN3kjQIEB9h0NR9qhpTlwycDOupQ0gKZCkmzRAZAEyTr4QiNA7bGfHmXZADihMydOq9WWNHxcsPGZBAdXjXIyVNTa3xH"

TELEGRAM_BOT_TOKEN = "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A"
TELEGRAM_CHAT_ID = "711598335"

def init_mirror_db():
    conn = sqlite3.connect(MIRROR_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mirror_queue (
            queue_index INTEGER PRIMARY KEY AUTOINCREMENT,
            source_media_id TEXT UNIQUE,
            permalink TEXT,
            caption TEXT,
            source_timestamp TEXT,
            status TEXT DEFAULT 'PENDING',
            target_media_id TEXT,
            published_at TIMESTAMP,
            error_msg TEXT
        )
    """)
    conn.commit()
    conn.close()

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[Telegram Error] {e}")

def sync_queue_from_source():
    """
    Fetches all historical media from @startup_road,
    sorts them OLDEST FIRST (bottom of profile),
    and populates mirror_queue with status='PENDING'.
    """
    init_mirror_db()
    conn = sqlite3.connect(MIRROR_DB)
    c = conn.cursor()

    print("🔄 Fetching historical reels from @startup_road...")
    url = f"https://graph.facebook.com/v21.0/{SOURCE_IG_ID}/media?fields=id,caption,media_type,media_product_type,permalink,timestamp&limit=100&access_token={SOURCE_TOKEN}"

    all_items = []
    page = 1
    while url:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("data", [])
                all_items.extend(items)
                print(f"   Page {page}: Retrieved {len(items)} items (Total: {len(all_items)})")
                url = data.get("paging", {}).get("next")
                page += 1
        except Exception as e:
            print(f"   [Error fetching page {page}]: {e}")
            break

    # Filter only videos/reels
    video_reels = [m for m in all_items if m.get("media_type") == "VIDEO" or m.get("media_product_type") == "REELS"]
    
    # Sort chronologically OLDEST FIRST
    sorted_reels = sorted(video_reels, key=lambda x: x.get("timestamp", ""))

    inserted_count = 0
    for r in sorted_reels:
        try:
            c.execute("""
                INSERT OR IGNORE INTO mirror_queue 
                (source_media_id, permalink, caption, source_timestamp, status)
                VALUES (?, ?, ?, ?, 'PENDING')
            """, (r.get("id"), r.get("permalink"), r.get("caption") or "", r.get("timestamp")))
            if c.rowcount > 0:
                inserted_count += 1
        except Exception as e:
            pass

    conn.commit()
    conn.close()
    print(f"✅ Sync Complete: {inserted_count} new reels added to queue. Total: {len(sorted_reels)} reels in catalog.")
    return len(sorted_reels)

def get_queue_status():
    init_mirror_db()
    conn = sqlite3.connect(MIRROR_DB)
    c = conn.cursor()
    c.execute("SELECT count(*) FROM mirror_queue")
    total = c.fetchone()[0]
    c.execute("SELECT count(*) FROM mirror_queue WHERE status = 'PUBLISHED'")
    published = c.fetchone()[0]
    c.execute("SELECT count(*) FROM mirror_queue WHERE status = 'PENDING'")
    pending = c.fetchone()[0]
    c.execute("SELECT queue_index, permalink, caption, source_timestamp FROM mirror_queue WHERE status = 'PENDING' ORDER BY queue_index ASC LIMIT 5")
    next_up = c.fetchall()
    conn.close()
    return {
        "total": total,
        "published": published,
        "pending": pending,
        "next_up": next_up
    }

def publish_single_reel(queue_index):
    """
    Publishes a single queued reel from @startup_road to @the_startuproad.
    """
    init_mirror_db()
    conn = sqlite3.connect(MIRROR_DB)
    c = conn.cursor()
    c.execute("SELECT source_media_id, caption, permalink FROM mirror_queue WHERE queue_index = ?", (queue_index,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "Queue item not found"

    source_id, caption, permalink = row

    print(f"\n🚀 [Queue #{queue_index}] Publishing to @the_startuproad...")
    print(f"   Source Permalink: {permalink}")

    # Step 1: Get fresh direct video media_url from source
    fetch_url = f"https://graph.facebook.com/v21.0/{source_id}?fields=media_url&access_token={SOURCE_TOKEN}"
    try:
        with urllib.request.urlopen(fetch_url, timeout=15) as resp:
            media_data = json.loads(resp.read().decode("utf-8"))
            video_url = media_data.get("media_url")
    except Exception as e:
        err = f"Failed to get video_url: {e}"
        print(f"❌ {err}")
        c.execute("UPDATE mirror_queue SET status='FAILED', error_msg=? WHERE queue_index=?", (err, queue_index))
        conn.commit()
        conn.close()
        return False, err

    if not video_url:
        err = "media_url is empty"
        print(f"❌ {err}")
        c.execute("UPDATE mirror_queue SET status='FAILED', error_msg=? WHERE queue_index=?", (err, queue_index))
        conn.commit()
        conn.close()
        return False, err

    # Step 2: Create Reel Container on target @the_startuproad
    create_url = f"https://graph.facebook.com/v21.0/{TARGET_IG_ID}/media"
    payload = urllib.parse.urlencode({
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": TARGET_TOKEN
    }).encode("utf-8")

    try:
        req = urllib.request.Request(create_url, data=payload)
        with urllib.request.urlopen(req, timeout=20) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            container_id = res_data.get("id")
            print(f"   Created Reel Container ID: {container_id}")
    except Exception as e:
        err = f"Container creation failed: {e}"
        print(f"❌ {err}")
        c.execute("UPDATE mirror_queue SET status='FAILED', error_msg=? WHERE queue_index=?", (err, queue_index))
        conn.commit()
        conn.close()
        return False, err

    # Step 3: Poll Meta until video is FINISHED processing
    status_url = f"https://graph.facebook.com/v21.0/{container_id}?fields=status_code&access_token={TARGET_TOKEN}"
    ready = False
    for attempt in range(12):
        time.sleep(5)
        try:
            with urllib.request.urlopen(status_url, timeout=10) as resp:
                s_data = json.loads(resp.read().decode("utf-8"))
                code = s_data.get("status_code")
                print(f"   Processing status: {code} (attempt {attempt+1}/12)")
                if code == "FINISHED":
                    ready = True
                    break
                elif code == "ERROR":
                    err = f"Meta video processing returned ERROR"
                    c.execute("UPDATE mirror_queue SET status='FAILED', error_msg=? WHERE queue_index=?", (err, queue_index))
                    conn.commit()
                    conn.close()
                    return False, err
        except Exception as e:
            print(f"   Status check error: {e}")

    if not ready:
        err = "Container processing timed out"
        c.execute("UPDATE mirror_queue SET status='FAILED', error_msg=? WHERE queue_index=?", (err, queue_index))
        conn.commit()
        conn.close()
        return False, err

    # Step 4: Publish Container
    pub_url = f"https://graph.facebook.com/v21.0/{TARGET_IG_ID}/media_publish"
    pub_payload = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": TARGET_TOKEN
    }).encode("utf-8")

    try:
        req = urllib.request.Request(pub_url, data=pub_payload)
        with urllib.request.urlopen(req, timeout=20) as resp:
            pub_data = json.loads(resp.read().decode("utf-8"))
            target_media_id = pub_data.get("id")
            print(f"🎉 PUBLISHED SUCCESSFULLY! Target Media ID: {target_media_id}")
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                UPDATE mirror_queue 
                SET status='PUBLISHED', target_media_id=?, published_at=?, error_msg=NULL 
                WHERE queue_index=?
            """, (target_media_id, now_str, queue_index))
            conn.commit()
            conn.close()
            return True, target_media_id
    except Exception as e:
        err = f"Publish endpoint error: {e}"
        print(f"❌ {err}")
        c.execute("UPDATE mirror_queue SET status='FAILED', error_msg=? WHERE queue_index=?", (err, queue_index))
        conn.commit()
        conn.close()
        return False, err

def run_daily_batch(limit=30, delay_between=45):
    """
    Executes a batch of N reels sequentially.
    """
    status = get_queue_status()
    if status["total"] == 0:
        sync_queue_from_source()
        status = get_queue_status()

    conn = sqlite3.connect(MIRROR_DB)
    c = conn.cursor()
    c.execute("SELECT queue_index, caption, permalink FROM mirror_queue WHERE status = 'PENDING' ORDER BY queue_index ASC LIMIT ?", (limit,))
    reels_to_post = c.fetchall()
    conn.close()

    if not reels_to_post:
        print("ℹ️ No pending reels in queue!")
        return 0

    print("=" * 60)
    print(f"🎬 STARTING MIRROR BATCH: {len(reels_to_post)} REELS")
    print(f"   Source: @startup_road  ➔  Destination: @the_startuproad")
    print("=" * 60)

    send_telegram(
        f"🚀 <b>STARTUP ROAD MIRROR BATCH STARTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Batch Target: {len(reels_to_post)} Reels\n"
        f"📥 Source: @startup_road (Chronological Oldest)\n"
        f"📤 Target: @the_startuproad\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )

    success_count = 0
    for idx, (q_idx, caption, permalink) in enumerate(reels_to_post, 1):
        cap_title = (caption or "No Caption").replace("\n", " ")[:35]
        print(f"\n--- [Batch #{idx}/{len(reels_to_post)}] Queue #{q_idx}: {cap_title}... ---")
        ok, res = publish_single_reel(q_idx)
        if ok:
            success_count += 1
            print(f"✅ Slot #{idx} Published! Target Media ID: {res}")
            send_telegram(
                f"✅ <b>[Post #{idx}/{len(reels_to_post)}] Live on @the_startuproad!</b>\n"
                f"• Title: {cap_title}...\n"
                f"• Source Reel: {permalink}"
            )
        else:
            print(f"⚠️ Slot #{idx} Failed: {res}")
            send_telegram(f"⚠️ [Post #{idx}] Error: {res}")

        if idx < len(reels_to_post):
            print(f"⏳ Waiting {delay_between}s before next reel...")
            time.sleep(delay_between)

    send_telegram(
        f"🏆 <b>MIRROR BATCH COMPLETED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Successfully Published: {success_count}/{len(reels_to_post)}\n"
        f"• Total Published So Far: {status['published'] + success_count}/{status['total']}\n"
        f"Destination: Instagram @the_startuproad 🚀"
    )
    return success_count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync", action="store_true", help="Sync all reels from @startup_road")
    parser.add_argument("--status", action="store_true", help="View current queue status")
    parser.add_argument("--post-one", action="store_true", help="Post only 1 next reel as test")
    parser.add_argument("--batch", type=int, default=0, help="Run batch of N reels (e.g. 30)")
    args = parser.parse_args()

    if args.sync:
        sync_queue_from_source()
    elif args.status:
        st = get_queue_status()
        print(f"Total in Queue: {st['total']}")
        print(f"Published: {st['published']}")
        print(f"Pending: {st['pending']}")
        print("\nNext 5 in Line:")
        for r in st["next_up"]:
            print(f"  #{r[0]} | Date: {r[3]} | Link: {r[1]}")
    elif args.post_one:
        st = get_queue_status()
        if st["total"] == 0:
            sync_queue_from_source()
            st = get_queue_status()
        if st["next_up"]:
            next_id = st["next_up"][0][0]
            publish_single_reel(next_id)
        else:
            print("No pending reels to post.")
    elif args.batch > 0:
        run_daily_batch(limit=args.batch)
    else:
        # Default behavior: show status
        st = get_queue_status()
        if st["total"] == 0:
            sync_queue_from_source()
            st = get_queue_status()
        print(f"Total: {st['total']} | Published: {st['published']} | Pending: {st['pending']}")
