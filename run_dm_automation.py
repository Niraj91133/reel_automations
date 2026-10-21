import os
import sys
import time
from db import init_db, is_reel_processed
from dm_scraper import get_shared_reels_from_chat
from scraper import download_reel_video
from main_pipeline import process_single_reel

sys.stdout.reconfigure(encoding='utf-8')

def run_chat_automation(max_reels=10):
    print("========================================================")
    print("   STARTING AUTOMATION: @im_raaaj_ CHAT SHARED REELS    ")
    print("========================================================")
    init_db()

    # Fetch all recent reels from im_raaaj_ chat
    reels = get_shared_reels_from_chat(max_count=20)
    if not reels:
        print("No shared reels found in chat.")
        return

    processed_count = 0
    for item in reels:
        if processed_count >= max_reels:
            print(f"🎯 Target limit of {max_reels} reels delivered!")
            break

        shortcode = item["shortcode"]
        reel_url = item["url"]
        creator = item["creator"]

        # Duplicate check: skip if already sent before
        if is_reel_processed(shortcode):
            print(f"⏩ [Skip] Reel {shortcode} already processed in past. Skipping.")
            continue

        temp_video = f"temp_{shortcode}.mp4"
        print(f"\n📥 Downloading New Shared Reel ({processed_count + 1}/{max_reels}): {reel_url}...")
        downloaded = download_reel_video(reel_url, temp_video)

        if downloaded and os.path.exists(downloaded):
            try:
                # Process with Gemini AI, Upgraded Big Font Red Template + 5s animated circle
                success = process_single_reel(downloaded, shortcode, username=creator)
                if success:
                    processed_count += 1
            except Exception as e:
                print(f"Error processing reel {shortcode}:", e)
            finally:
                if os.path.exists(temp_video):
                    os.remove(temp_video)
        else:
            print(f"Could not download reel {shortcode}")

    print(f"\n🎉 Automation finished! Delivered {processed_count} new reels from @im_raaaj_ chat to Telegram!")

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_chat_automation(limit)
