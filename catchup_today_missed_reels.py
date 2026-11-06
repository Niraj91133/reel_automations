import os
import sys
import time
import glob
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase

CHANNELS = [
    ("startup_road", "💼 Startup Road", "@startup_road"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_"),
    ("healthy_diet", "🥗 Gudtree", "@gudtree_"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road")
]

def catchup_channel(channel_id, display_name, handle):
    config = get_channel_config(channel_id)
    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))
    db = ChannelDatabase(config["runtime"]["db_path"])

    queue_dir = os.path.join(config["runtime"]["workspace_dir"], "tomorrow_reels")
    vid_files = sorted(glob.glob(os.path.join(queue_dir, "ready_*.mp4")))

    print(f"\n========================================================")
    print(f"🚀 CATCHING UP MISSED REELS TODAY FOR: {display_name}")
    print(f"Total Pre-Baked Files Available: {len(vid_files)}")
    print(f"========================================================")

    posted_count = 0
    for vid_file in vid_files:
        stem = Path(vid_file).stem # e.g. ready_15_Dd6VUwCPILX
        meta_file = os.path.join(queue_dir, f"{stem}.json")

        if not os.path.exists(meta_file):
            continue

        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        shortcode = meta.get("shortcode")
        title = meta.get("title", "Viral Reel")
        caption = meta.get("caption", f"Insights from {handle}")
        creator = meta.get("creator", "creator")

        # Skip if already processed in database
        if db.is_reel_processed(shortcode):
            continue

        # Strictly respect 30 reels per day target
        today_count = db.get_today_count()
        if today_count >= 30:
            print(f"🎯 [{display_name}] Daily quota reached: {today_count}/30! Stopping catch-up for this channel.")
            break

        print(f"\n▶ [{display_name}] Catch-up posting: {shortcode} - {title[:35]}...")

        try:
            sent, cdn_url = hub.send_video_with_cdn_url(vid_file, f"<b>[{display_name}]</b>\n\n{caption}")
            if sent and cdn_url and publisher.is_configured():
                first_comment = config.get("content_settings", {}).get("first_comment_template")
                pub_res = publisher.publish_reel(
                    public_video_url=cdn_url,
                    caption=caption,
                    creator_username=creator,
                    first_comment=first_comment
                )
                if pub_res and "permalink" in pub_res:
                    link = pub_res["permalink"]
                    print(f"🎉 SUCCESS! [{display_name}] LIVE: {link}")
                    hub.send_message(
                        f"🎉 <b>[{display_name}] Catch-Up Reel LIVE!</b>\n\n"
                        f"🎬 <b>Title:</b> {title}\n"
                        f"🔗 <b>Watch Reel:</b> {link}"
                    )
                    db.mark_reel_processed(shortcode, creator, title, link)
                    posted_count += 1
                else:
                    err = pub_res.get("error", "Failed") if pub_res else "No response"
                    print(f"⚠️ [{display_name}] Meta API error: {err}")
                    # If Meta daily quota hit, break safely
                    if "limit" in str(err).lower() or "quota" in str(err).lower():
                        print(f"🛑 Meta daily API limit reached for {display_name}. Stopping catch-up.")
                        break
            else:
                print(f"⚠️ [{display_name}] Could not send video to Telegram / CDN for {shortcode}.")

            # 20s spacing between posts to avoid Instagram spam block
            time.sleep(20)

        except Exception as e:
            print(f"❌ Error during catch-up for {shortcode}: {e}")

    print(f"✅ [{display_name}] Caught up {posted_count} missed reels!")
    return posted_count

def run_catchup_all():
    summary = {}
    for ch_id, name, handle in CHANNELS:
        count = catchup_channel(ch_id, name, handle)
        summary[name] = count
        time.sleep(15)
    print("\n========================================================")
    print(f"🏁 ALL CHANNELS CATCH-UP COMPLETE: {summary}")
    print("========================================================")

if __name__ == '__main__':
    run_catchup_all()
