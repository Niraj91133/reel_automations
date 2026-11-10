import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Support optional date argument (default today)
target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"Current System Time (IST): {now_str}")
print(f"Report Target Date: {target_date}\n")

channels = [
    {"name": "Startup Road (@startup_road)", "db": "databases/startup_road_history.db"},
    {"name": "Trading Road (@trading_road_)", "db": "databases/trading_pulse_history.db"},
    {"name": "Gudtree (@gudtree_)", "db": "databases/healthy_diet_history.db"},
    {"name": "Trending Road (@trending_road)", "db": "databases/viral_finds_history.db"},
    {"name": "Trading Road 24 (@trading_road24)", "db": "databases/trading_road24_history.db"},
    {"name": "The Loan Road (@the_loan_road)", "db": "databases/the_loan_road_history.db"},
    {"name": "The Startup Road (@the_startuproad)", "db": "databases/the_startuproad_history.db"}
]

for ch in channels:
    name = ch["name"]
    db_path = ch["db"]
    print("=" * 65)
    print(f"📌 {name}")
    print("=" * 65)

    if not os.path.exists(db_path):
        print(f"  ❌ DB file missing: {db_path}\n")
        continue

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Reels
    c.execute(
        "SELECT id, shortcode, title, permalink, created_at FROM processed_reels WHERE created_at LIKE ? ORDER BY id ASC",
        (f"{target_date}%",)
    )
    reels = c.fetchall()
    print(f"  🎬 REELS POSTED ({target_date}): {len(reels)} / 30 slots")
    if reels:
        for idx, r in enumerate(reels, 1):
            title = (r[2] or "No Title").replace('\n', ' ')[:40]
            raw_time = str(r[4])
            time_part = raw_time.split()[1] if " " in raw_time else raw_time
            try:
                utc_dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                ist_dt = utc_dt + timedelta(hours=5, minutes=30)
                ist_time_str = ist_dt.strftime("%I:%M %p")
            except Exception:
                ist_time_str = f"{time_part} (raw)"
            print(f"     Slot #{idx:02d} | IST: {ist_time_str} | Title: {title} | Link: {r[3]}")
    else:
        print("     (No reels posted for this date yet)")

    # 2. Stories
    try:
        c.execute(
            "SELECT slot_index, title, media_id, created_at FROM processed_stories WHERE date_str = ? OR created_at LIKE ? ORDER BY slot_index ASC",
            (target_date, f"{target_date}%")
        )
        stories = c.fetchall()
        print(f"\n  📸 STORIES POSTED ({target_date}): {len(stories)} / 20 slots")
        if stories:
            for s in stories:
                s_title = (s[1] or "Reel Story Card").replace('\n', ' ')[:40]
                raw_time = str(s[3])
                try:
                    utc_dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                    ist_dt = utc_dt + timedelta(hours=5, minutes=30)
                    ist_time_str = ist_dt.strftime("%I:%M %p")
                except Exception:
                    ist_time_str = raw_time
                print(f"     Story #{s[0]:02d} | IST: {ist_time_str} | Title: {s_title}")
        else:
            print("     (No stories posted for this date yet)")
    except Exception as e:
        print(f"     Story query notice: {e}")

    conn.close()
    print()
