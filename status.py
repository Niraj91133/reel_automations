import os
import sys
import glob
import json
import sqlite3
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

CHANNELS = [
    ("thestartup_street", "Startup Road", "@startup_road"),
    ("healthy_diet", "Gud Tree", "@gudtree_"),
    ("trading_road24", "Trading Knowledge", "@trading_road24"),
    ("theloan_road", "The Loan Road", "@the_loan_road"),
    ("marketing_road24", "Marketing Road", "@marketing_road24"),
    ("viral_finds", "Trending Road", "@trending_road")
]

print("==========================================================================================")
print(f"📊 LIVE PIPELINE STATUS DASHBOARD | Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("==========================================================================================")
print(f"{'Channel':<20} | {'Today Posts':<12} | {'Unposted Buffer':<16} | {'Hunted Pool':<12} | {'Latest Post Time'}")
print("-" * 90)

for ch_id, name, handle in CHANNELS:
    db_path = f"databases/{ch_id}_history.db"
    today_posts = 0
    last_post_time = "Never"
    hunted_pending = 0
    unposted_buffer = 0

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            today_prefix = datetime.now().strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM processed_reels WHERE created_at LIKE ?", (f"{today_prefix}%",))
            today_posts = c.fetchone()[0]

            c.execute("SELECT created_at FROM processed_reels ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            if row and row[0]:
                try:
                    utc_dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                    ist_dt = utc_dt + timedelta(hours=5, minutes=30)
                    last_post_time = ist_dt.strftime("%H:%M:%S") + " IST"
                except:
                    last_post_time = row[0].split()[1] if " " in row[0] else row[0]

            c.execute("SELECT COUNT(*) FROM hunted_reels WHERE shortcode NOT IN (SELECT shortcode FROM processed_reels)")
            hunted_pending = c.fetchone()[0]

            c.execute("SELECT shortcode FROM processed_reels")
            processed_codes = {r[0] for r in c.fetchall()}
            conn.close()

            queue_dir = f"C:/reel_cache/{ch_id}/tomorrow_reels"
            for mf in glob.glob(f"{queue_dir}/ready_*.json"):
                try:
                    with open(mf, 'r', encoding='utf-8') as jf:
                        sc = json.load(jf).get("shortcode")
                    if sc and sc not in processed_codes:
                        unposted_buffer += 1
                except:
                    pass
        except Exception as e:
            pass

    status_icon = "🟢" if unposted_buffer >= 2 else ("🟡" if unposted_buffer == 1 else "🔴")
    print(f"{status_icon} {name:<18} | {today_posts:>2} / 30 posts | {unposted_buffer:>2} ready reels   | {hunted_pending:>3} in pool   | {last_post_time}")

print("==========================================================================================")
print("💡 Tip: Ye script 0 AI tokens use karti hai. Status dekhne ke liye: 'python status.py'")
print("==========================================================================================")
