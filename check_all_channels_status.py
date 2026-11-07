import sqlite3
import os
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"Current System Time: {now_str}\n")

channels = [
    {"name": "Startup Road (@startup_road)", "db": "databases/startup_road_history.db"},
    {"name": "Trading Road (@trading_road_)", "db": "databases/trading_pulse_history.db"},
    {"name": "Gudtree (@gudtree_)", "db": "databases/healthy_diet_history.db"},
    {"name": "Trending Road (@trending_road)", "db": "databases/viral_finds_history.db"}
]

for ch in channels:
    name = ch["name"]
    db_path = ch["db"]
    print("=" * 65)
    print(f"📌 {name}")
    print("=" * 65)

    if not os.path.exists(db_path):
        print(f"  ❌ DB file missing: {db_path}")
        continue

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Reels
    c.execute(
        "SELECT id, shortcode, title, permalink, created_at FROM processed_reels WHERE created_at LIKE ? ORDER BY id ASC",
        (f"{today}%",)
    )
    reels = c.fetchall()
    print(f"  🎬 REELS POSTED TODAY ({today}): {len(reels)} / 30 slots")
    if reels:
        for idx, r in enumerate(reels, 1):
            title = (r[2] or "No Title").replace('\n', ' ')[:40]
            time_part = r[4].split()[1] if " " in str(r[4]) else r[4]
            # convert UTC to IST roughly (+5:30)
            try:
                utc_dt = datetime.strptime(r[4], "%Y-%m-%d %H:%M:%S")
                ist_dt = utc_dt + datetime.timedelta(hours=5, minutes=30)
                ist_time_str = ist_dt.strftime("%I:%M %p")
            except:
                ist_time_str = time_part
            print(f"     Slot #{idx:02d} | IST: {ist_time_str} | Title: {title} | Link: {r[3]}")
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
                try:
                    utc_dt = datetime.strptime(s[3], "%Y-%m-%d %H:%M:%S")
                    ist_dt = utc_dt + datetime.timedelta(hours=5, minutes=30)
                    ist_time_str = ist_dt.strftime("%I:%M %p")
                except:
                    ist_time_str = s[3]
                print(f"     Story #{s[0]:02d} | IST: {ist_time_str} | Title: {s_title}")
        else:
            print("     (No stories posted today yet)")
    except Exception as e:
        print(f"     Story query notice: {e}")

    conn.close()
    print()
