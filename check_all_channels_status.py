import sqlite3
import os
from datetime import datetime, timedelta

today = datetime.now().strftime('%Y-%m-%d')
now_str = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
print(f"Current System Time: {now_str}\n")

channels = [
    {"name": "🚀 Startup Road (@startup_road)", "db": "databases/thestartup_street_history.db"},
    {"name": "📱 Marketing Road (@marketing_road24)", "db": "databases/marketing_road24_history.db"},
    {"name": "📈 Trading Road (@trading_road_)", "db": "databases/trading_pulse_history.db"},
    {"name": "🥗 Gud Tree (@gudtree_)", "db": "databases/healthy_diet_history.db"},
    {"name": "🛍️ Trending Road (@trending_road)", "db": "databases/viral_finds_history.db"},
    {"name": "💳 The Loan Road (@the_loan_road)", "db": "databases/theloan_road_history.db"},
    {"name": "📊 Trading Road 24 (@trading_road24)", "db": "databases/trading_road24_history.db"}
]

total_posted_today = 0

for ch in channels:
    name = ch["name"]
    db_path = ch["db"]
    is_mirror = ch.get("is_mirror", False)
    print("=" * 65)
    print(f"📌 {name}")
    print("=" * 65)

    if not os.path.exists(db_path):
        print(f"  ❌ DB file missing: {db_path}")
        continue

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Reels
    if is_mirror:
        c.execute(
            "SELECT queue_index, source_media_id, caption, permalink, published_at FROM mirror_queue WHERE published_at LIKE ? ORDER BY published_at ASC",
            (f"{today}%",)
        )
        reels = c.fetchall()
    else:
        c.execute(
            "SELECT id, shortcode, title, permalink, created_at FROM processed_reels WHERE created_at LIKE ? ORDER BY id ASC",
            (f"{today}%",)
        )
        reels = c.fetchall()
    total_posted_today += len(reels)
    print(f"  🎬 REELS POSTED TODAY ({today}): {len(reels)} / 30 slots")
    if reels:
        for idx, r in enumerate(reels, 1):
            title = (r[2] or "No Title").replace('\n', ' ')[:45]
            time_part = r[4].split()[1] if " " in str(r[4]) else r[4]
            try:
                utc_dt = datetime.strptime(r[4], "%Y-%m-%d %H:%M:%S")
                ist_dt = utc_dt + timedelta(hours=5, minutes=30)
                ist_time_str = ist_dt.strftime("%I:%M %p")
            except:
                ist_time_str = time_part
            print(f"     Slot #{idx:02d} | Time: {ist_time_str} | Title: {title} | Link: {r[3]}")
    else:
        print("     (No reels posted today yet)")

    # 2. Stories
    try:
        c.execute(
            "SELECT slot_index, title, media_id, created_at FROM processed_stories WHERE date_str = ? OR created_at LIKE ? ORDER BY slot_index ASC",
            (today, f"{today}%")
        )
        stories = c.fetchall()
        print(f"\n  📸 STORIES POSTED TODAY ({today}): {len(stories)} / 20 slots")
        if stories:
            for s in stories:
                s_title = (s[1] or "Reel Story Card").replace('\n', ' ')[:40]
                print(f"     Story #{s[0]:02d} | Time: {s[3]} | Title: {s_title}")
        else:
            print("     (No stories posted today yet)")
    except Exception as e:
        print(f"     Story query notice: {e}")

    conn.close()
    print()

print(f"📊 SUMMARY: {total_posted_today} Reels live across all channels today.")
