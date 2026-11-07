import os
import sys
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.niche_hunter import hunt_niche_reels

cfg = get_channel_config("startup_road")
print("🚀 Starting Live Hunt for 10 Reels (Pure Scraping - NO DM / NO CHAT)...")
candidates = hunt_niche_reels(cfg, target_count=10, headless=True)

print(f"\n🎯 Total Candidates Discovered: {len(candidates)}")
print(json.dumps(candidates, indent=2))
