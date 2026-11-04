import os
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = str(Path(__file__).resolve().parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import list_available_channels, get_channel_config, load_master_config
from core.niche_hunter import hunt_niche_reels, send_hunted_reels_to_raj_chat
from core.telegram_hub import TelegramHub

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def run_5_reels_test_all_channels(gap_minutes=5, target_reels_per_channel=5):
    """
    Hunts 5 fresh reels for each channel and sends them to @im_raaaj_ DM chat.
    Pauses with a configurable gap (default 5 minutes) between channels.
    """
    master_cfg = load_master_config()
    hub = TelegramHub(
        bot_token=master_cfg.get("master_bot_token", "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A"),
        default_chat_id=master_cfg.get("admin_chat_id", "711598335")
    )

    channels = list_available_channels()

    print("========================================================")
    print("🚀 STARTING 5-REELS MULTI-ACCOUNT VERIFICATION TEST")
    print(f"Channels: {', '.join(channels)}")
    print(f"Reels per channel: {target_reels_per_channel} | Gap between channels: {gap_minutes} mins")
    print("========================================================\n")

    hub.send_message(
        f"🧪 <b>Starting 5-Reels Verification Test!</b>\n"
        f"• Total Channels: {len(channels)}\n"
        f"• Reels per Channel: {target_reels_per_channel}\n"
        f"• Interval Gap: {gap_minutes} minutes"
    )

    for idx, ch_id in enumerate(channels, 1):
        cfg = get_channel_config(ch_id)
        display_name = cfg.get("display_name", ch_id)

        print(f"\n[{idx}/{len(channels)}] ▶ Channel: {display_name} ({ch_id})")
        hub.send_message(f"🏹 <b>[{idx}/{len(channels)}] Hunting {target_reels_per_channel} reels for {display_name}...</b>")

        # 1. Hunt 5 reels
        candidates = hunt_niche_reels(cfg, target_count=target_reels_per_channel)

        # 2. Send 5 reels to Raj
        if candidates:
            sent_count = send_hunted_reels_to_raj_chat(cfg, candidates, max_to_send=target_reels_per_channel)
            hub.send_message(
                f"✅ <b>[{display_name}] Complete!</b>\n"
                f"Sent {sent_count} reels directly to Raj (@im_raaaj_) DM for review."
            )
        else:
            hub.send_message(f"⚠️ No candidates found for {display_name}.")

        # 3. Gap pause if there are remaining channels
        if idx < len(channels):
            wait_seconds = gap_minutes * 60
            print(f"\n⏳ Pausing {gap_minutes} minutes ({wait_seconds}s) before next channel...")
            hub.send_message(f"⏳ <i>Pausing {gap_minutes} minutes cooldown before next channel...</i>")

            # Countdown with second updates every 30s
            for remaining in range(wait_seconds, 0, -30):
                mins, secs = divmod(remaining, 60)
                print(f"   Cooldown remaining: {mins:02d}:{secs:02d}...", flush=True)
                time.sleep(min(30, remaining))

    print("\n🎉 ALL 4 CHANNELS PROCESSED SUCCESSFULLY!")
    hub.send_message("🎉 <b>5-Reels Verification Test Finished!</b>\nCheck your Instagram DMs on @im_raaaj_.")

if __name__ == "__main__":
    # Check if arguments provided
    reels = 5
    gap = 5
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        reels = int(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        gap = int(sys.argv[2])

    run_5_reels_test_all_channels(gap_minutes=gap, target_reels_per_channel=reels)

