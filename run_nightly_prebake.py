import sys, os, time
from datetime import datetime

# Set up paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
nested = os.path.join(BASE_DIR, "reel_automations-main")
if nested not in sys.path:
    sys.path.insert(0, nested)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from prebake_autopilot_channels import prebake_all_channels

if __name__ == '__main__':
    print("==================================================")
    print(f"🌙 [NIGHTLY PRE-BAKING DAEMON STARTED: {datetime.now()}]")
    print("Goal: Lock exactly 30 Ultra-HD Branded Reels for ALL 5 channels")
    print("==================================================")
    
    try:
        summary = prebake_all_channels(count=30)
        print("\n==================================================")
        print(f"🎉 ALL CHANNELS PRE-BAKING COMPLETE: {summary}")
        print("==================================================")
    except Exception as e:
        print(f"❌ Error during nightly prebake: {e}")

