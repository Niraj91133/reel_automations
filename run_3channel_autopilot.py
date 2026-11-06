import os
import sys
import time
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath('reel_automations-main')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.full_autopilot import run_channel_autopilot, run_3_channels_autopilot_cycle

AUTOPILOT_CHANNELS = [
    ("trading_pulse", "📈 Trading Road", "@trading_road_"),
    ("healthy_diet", "🥗 Gudtree", "@gudtree_"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road")
]

# Daily slots for the 3 autopilot accounts (4 posts/day per account)
DEFAULT_POST_SLOTS = [
    (9, 30),   # 09:30 AM (Morning Peak)
    (13, 30),  # 01:30 PM (Lunch Break Peak)
    (17, 30),  # 05:30 PM (Evening Commute Peak)
    (20, 30)   # 08:30 PM (Prime Time Night Peak)
]

def run_now_for_all_3():
    """Immediately runs 1 full hunt-edit-post cycle across the 3 autopilot accounts."""
    print("========================================================")
    print("  🚀 TRIGGERING INSTANT AUTOPILOT CYCLE (3 CHANNELS)")
    print("========================================================")
    print("Target Accounts: @trading_road_, @gudtree_, @trending_road")
    print("Exclusion: @startup_road is strictly kept in manual/curated mode")
    print("========================================================\n")

    results = {}
    for ch_id, display_name, handle in AUTOPILOT_CHANNELS:
        print(f"\n▶ Starting Autopilot for {display_name} ({handle})...")
        success = run_channel_autopilot(ch_id)
        results[ch_id] = success
        print(f"Status for {display_name}: {'✅ LIVE' if success else '⚠️ RETRY LATER'}")
        time.sleep(15)

    print("\n========================================================")
    print(f"🏁 Instant Cycle Complete at {datetime.now().strftime('%I:%M %p')}!")
    print(f"Results: {results}")
    print("========================================================")
    return results

def run_continuous_daemon():
    """
    24/7 Standing Background Daemon for the 3 Autopilot Channels.
    Automatically hunts, edits, and posts live reels at scheduled peak times every single day.
    """
    print("========================================================")
    print("  🤖 24/7 AUTOPILOT DAEMON STARTED (3 CHANNELS ONLY)")
    print("========================================================")
    print("Target Channels:")
    for ch_id, name, handle in AUTOPILOT_CHANNELS:
        print(f"  • {name} ({handle}) ➔ 100% Autopilot (Hunt + Edit + Post)")
    print("\nExcluded Channel:")
    print("  • 💼 Startup Road (@startup_road) ➔ Strictly Manual / Curated")
    print("\nDaily Schedule Slots:")
    for h, m in DEFAULT_POST_SLOTS:
        print(f"  ⏰ {h:02d}:{m:02d} {'AM' if h < 12 else 'PM'}")
    print("========================================================\n")

    executed_slots_today = set()

    while True:
        now = datetime.now()
        today_date = now.strftime('%Y-%m-%d')
        current_time_str = now.strftime('%H:%M')

        # Clear yesterday's record at midnight
        if now.hour == 0 and now.minute == 0:
            executed_slots_today.clear()

        # Check if current time matches any slot
        for hour, minute in DEFAULT_POST_SLOTS:
            slot_key = f"{today_date}_{hour:02d}:{minute:02d}"
            if now.hour == hour and now.minute == minute and slot_key not in executed_slots_today:
                print(f"\n⏰ [SLOT TRIGGERED: {now.strftime('%I:%M %p')}] Starting 3-Channel Autopilot Cycle...")
                executed_slots_today.add(slot_key)
                run_now_for_all_3()
                break

        time.sleep(30)

if __name__ == '__main__':
    args = sys.argv[1:]
    if "--now" in args or "now" in args:
        run_now_for_all_3()
    elif "--channel" in args:
        idx = args.index("--channel") + 1
        if idx < len(args):
            run_channel_autopilot(args[idx])
    else:
        run_continuous_daemon()

