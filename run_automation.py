import os
import sys
import time
from db import init_db, is_reel_processed
from scraper import get_latest_reels_from_profile, download_reel_video
from main_pipeline import process_single_reel

TARGET_USERNAME = "uxwithraaj"
MAX_DAILY_REELS = 10

def run_daily_automation(target_user=TARGET_USERNAME, limit=MAX_DAILY_REELS):
    print(f"🚀 Starting Instagram Reel Automation for @{target_user}...")
    init_db()

    # 1. Fetch latest reels from profile
    reels = get_latest_reels_from_profile(target_user, max_count=limit * 2)
    if not reels:
        print("❌ No reels found or profile is restricted.")
        return

    processed_count = 0
    for item in reels:
        if processed_count >= limit:
            print(f"🎯 Daily limit of {limit} reels reached!")
            break

        shortcode = item["shortcode"]
        reel_url = item["url"]

        # Check duplicate
        if is_reel_processed(shortcode):
            print(f"⏩ [Skip] Reel {shortcode} already in database.")
            continue

        print(f"\nProcessing new reel ({processed_count + 1}/{limit}): {reel_url}")
        
        # Download
        temp_video = f"temp_{shortcode}.mp4"
        downloaded = download_reel_video(reel_url, temp_video)
        
        if downloaded and os.path.exists(downloaded):
            try:
                success = process_single_reel(downloaded, shortcode, username=target_user)
                if success:
                    processed_count += 1
            except Exception as e:
                print(f"Error processing reel {shortcode}:", e)
            finally:
                if os.path.exists(temp_video):
                    os.remove(temp_video)
        else:
            print(f"Could not download reel {shortcode}")

    print(f"\n🎉 Automation finished! Processed and delivered {processed_count} reels to Telegram.")

if __name__ == '__main__':
    user = sys.argv[1] if len(sys.argv) > 1 else TARGET_USERNAME
    run_daily_automation(target_user=user)
