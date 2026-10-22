import os
import sys
import time
import requests
from datetime import datetime
from db import init_db, is_reel_processed
from dm_scraper import get_shared_reels_from_chat
from scraper import download_reel_video
from main_pipeline import process_single_reel
from telegram_sender import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

sys.stdout.reconfigure(encoding='utf-8')

def send_daily_batch_start_message(day_name, date_str, total_found):
    """Sends a clear header message in Telegram before sending the daily reels."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    text = (
        f"☀️ <b>GOOD MORNING! TODAY'S REEL AUTOMATION BATCH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Day:</b> {day_name}\n"
        f"🗓️ <b>Date:</b> {date_str}\n"
        f"🎯 <b>Found:</b> {total_found} new shared reels ready to process!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Processing and sending 10 ready-to-post reels below 👇</i>"
    )
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except:
        pass

def run_chat_automation(max_reels=10, target_chat_id=None, notify_callback=None):
    from telegram_sender import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    chat_id = target_chat_id or TELEGRAM_CHAT_ID
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%d-%b-%Y")

    print("========================================================")
    print(f"   STARTING AUTOMATION: {day_name.upper()} ({date_str})    ")
    print("========================================================")
    init_db()

    if notify_callback:
        notify_callback(f"🔍 <b>Startup:</b> Instagram DM (@im_raaaj_) se reels fetch kar rha hu...")

    # Fetch candidate reels from im_raaaj_ chat
    reels = get_shared_reels_from_chat(max_count=25)
    if not reels:
        print("No shared reels found in @im_raaaj_ chat.")
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "⚠️ <b>Startup Update:</b> @im_raaaj_ chat me koi reels nahi mili!",
                    "parse_mode": "HTML"
                },
                timeout=10
            )
        except:
            pass
        return 0

    # Filter only unprocessed reels
    unprocessed_reels = [r for r in reels if not is_reel_processed(r["shortcode"])]
    print(f"Total fresh unprocessed reels found: {len(unprocessed_reels)}")

    if not unprocessed_reels:
        print("No new reels found today. Everything is already up-to-date!")
        msg_text = "ℹ️ <b>Startup Update:</b> @im_raaaj_ chat me sabhi reels already processed hain! Chat me nayi reels share karein fir run karein."
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"},
                timeout=10
            )
        except:
            pass
        if notify_callback:
            notify_callback(msg_text)
        return 0

    target_reels = unprocessed_reels[:max_reels]
    total_today = len(target_reels)

    # 1. Send Day Header announcement in Telegram
    send_daily_batch_start_message(day_name, date_str, total_today)

    processed_count = 0
    for idx, item in enumerate(target_reels, start=1):
        shortcode = item["shortcode"]
        reel_url = item["url"]
        creator = item["creator"]

        if notify_callback:
            notify_callback(f"📥 <b>[Startup {idx}/{total_today}]</b> Downloading reel from @{creator}...")

        temp_video = f"temp_{shortcode}.mp4"
        print(f"\n📥 Downloading Reel ({idx}/{total_today}): {reel_url}...")
        downloaded = download_reel_video(reel_url, temp_video)

        if downloaded and os.path.exists(downloaded):
            try:
                if notify_callback:
                    notify_callback(f"🧠 <b>[Startup {idx}/{total_today}]</b> Gemini AI audio sun rha hai aur Studio video render kar rha hai...")
                success = process_single_reel(
                    video_file_path=downloaded,
                    reel_id=shortcode,
                    username=creator,
                    reel_index=idx,
                    total_reels=total_today
                )
                if success:
                    processed_count += 1
                    if notify_callback:
                        notify_callback(f"🚀 <b>[Startup {idx}/{total_today}]</b> Delivered to Startup Channel! ✅")
            except Exception as e:
                print(f"Error processing reel {shortcode}:", e)
                if notify_callback:
                    notify_callback(f"⚠️ Error in reel {shortcode}: {e}")
            finally:
                if os.path.exists(temp_video):
                    os.remove(temp_video)
        else:
            print(f"Could not download reel {shortcode}")

    print(f"\n🎉 Finished {day_name} batch! Delivered {processed_count} reels to Telegram!")
    return processed_count

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_chat_automation(limit)
