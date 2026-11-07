"""
================================================================================
🌟 4-CHANNEL 20 STORIES/DAY AUTOMATED DISPATCHER
================================================================================
Dedicated 24x7 Daemon for Instagram Stories across all 4 channels:
- 💼 Startup Road: @startup_road (20 Stories / Day)
- 📈 Trading Road: @trading_road_ (20 Stories / Day)
- 🥗 Gudtree: @gudtree_ (20 Stories / Day)
- 🛍️ Trending Road: @trending_road (20 Stories / Day)

Total Output: Exactly 80 Stories / Day
Active Hours: 08:00 AM - 10:00 PM (Every ~43 minutes)
State: SQLite ChannelDatabase (Idempotent, Zero Duplicates)
Safety: Meta Iron Shield Zero-Tolerance Compliance
================================================================================
"""

import os
import sys
import time
import random
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.story_engine import (
    publish_single_channel_story,
    STORY_SLOTS,
    CHANNEL_THEMES
)
from core.database import ChannelDatabase
from core.config_manager import get_channel_config

CHANNELS = [
    ("startup_road", "💼 Startup Road", "@startup_road"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_"),
    ("healthy_diet", "🥗 Gudtree", "@gudtree_"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road")
]

def run_story_dispatcher():
    print("========================================================")
    print("  🌟 4-CHANNEL 20 STORIES/DAY AUTOMATED DISPATCHER")
    print("========================================================")
    print("Channels:")
    for ch_id, name, handle in CHANNELS:
        print(f"  • {name} ({handle}) ➔ 20 Stories / Day")
    print(f"\nTotal Stories per Day: {len(CHANNELS) * 20} Stories")
    print("Time Window: 08:00 AM - 10:00 PM (~Every 43 minutes)")
    print("========================================================\n")

    current_day = None

    while True:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        if current_day != today_str:
            current_day = today_str
            print(f"\n📅 [New Day Activated] {today_str} - Story slots reset.\n")

        # Night Sleep Protocol: Stories only run between 08:00 AM and 10:00 PM
        if now.hour < 8 or now.hour >= 22:
            time.sleep(60)
            continue

        # Check each of the 20 slots
        for slot_num, slot_hour, slot_min in STORY_SLOTS:
            slot_time_passed = (now.hour > slot_hour) or (now.hour == slot_hour and now.minute >= slot_min)
            if slot_time_passed:
                # Dispatch for each channel if not already posted
                for ch_id, name, handle in CHANNELS:
                    config = get_channel_config(ch_id)
                    db = ChannelDatabase(config["runtime"]["db_path"])
                    if not db.is_story_processed(slot_num, today_str):
                        try:
                            success = publish_single_channel_story(ch_id, story_index=slot_num, today_str=today_str)
                            if success:
                                # Stagger between channels (10-15s anti-bot jitter)
                                time.sleep(random.uniform(10, 15))
                        except Exception as e:
                            print(f"❌ Error dispatching story slot #{slot_num} for {ch_id}: {e}")

        # Sleep between checks
        time.sleep(30)

if __name__ == '__main__':
    run_story_dispatcher()

