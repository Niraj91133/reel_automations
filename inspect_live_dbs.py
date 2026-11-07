import sqlite3
import os
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')
print(f"Current System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

dbs = [
    ("Startup Road (@startup_road)", "databases/startup_road_history.db"),
    ("Trading Road (@trading_road_)", "databases/trading_pulse_history.db"),
    ("Gudtree (@gudtree_)", "databases/healthy_diet_history.db"),
    ("Trending Road (@trending_road)", "databases/viral_finds_history.db")
]

for name, db_path in dbs:
    print("\n" + "=" * 65)
    print(f"📊 {name}")
    print(f"Path: {db_path}")
    print("=" * 65)

    if not os.path.exists(db_path):
        print("  ❌ DB Not Found!")
        continue

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Find tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print(f"Tables: {tables}")

    for t in tables:
        c.execute(f"PRAGMA table_info({t})")
        cols = [r[1] for r in c.fetchall()]
        
        # Check rows for today
        date_col = next((col for col in cols if 'date' in col.lower() or 'time' in col.lower() or 'created' in col.lower() or 'posted' in col.lower()), None)
        
        if date_col:
            c.execute(f"SELECT * FROM {t} WHERE {date_col} LIKE ? ORDER BY id DESC", (f"{today}%",))
            today_rows = c.fetchall()
            c.execute(f"SELECT COUNT(*) FROM {t}")
            total_rows = c.fetchone()[0]
            print(f"\n  📁 Table '{t}' (Total: {total_rows} | Today: {len(today_rows)}):")
            print(f"     Columns: {cols}")
            for row in today_rows[:8]:
                print(f"     -> {row}")
        else:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            total_rows = c.fetchone()[0]
            print(f"\n  📁 Table '{t}' (Total: {total_rows}):")
            print(f"     Columns: {cols}")

    conn.close()

