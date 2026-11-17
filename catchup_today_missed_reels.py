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
    ("thestartup_street", "🚀 Startup Road", "@startup_road"),
    ("the_startuproad", "🔄 The Startup Road [Mirror]", "@the_startuproad"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_"),
    ("healthy_diet", "🥗 Gud Tree", "@gudtree_"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road"),
    ("theloan_road", "💳 The Loan Road", "@the_loan_road"),
    ("trading_road24", "📊 Trading Knowledge", "@trading_road24")
]

def catchup_channel(channel_id, display_name, handle, target_slots_to_catch=5):
    config = get_channel_config(channel_id)
    db = ChannelDatabase(config["runtime"]["db_path"])
    today_count = db.get_today_count()

    print(f"\n========================================================")
    print(f"🚀 CATCHING UP MISSED REELS TODAY FOR: {display_name}")
    print(f"Already Posted Today: {today_count}/30")
    print(f"========================================================")

    if today_count >= 30:
        print(f"🎯 [{display_name}] Daily quota already fulfilled ({today_count}/30)!")
        return 0

    # Special handling for Mirror Channel
    if channel_id == "the_startuproad":
        from mirror_pipeline import get_queue_status, publish_single_reel
        st = get_queue_status()
        posted = 0
        while posted < target_slots_to_catch and (today_count + posted) < 30:
            st = get_queue_status()
            if not st["next_up"]:
                break
            next_idx = st["next_up"][0][0]
            print(f"\n🔄 [{display_name}] Catch-up Mirror Reel #{next_idx}...")
            ok, res = publish_single_reel(next_idx)
            if ok:
                posted += 1
                time.sleep(20)
            else:
                break
        return posted

    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))

    queue_dir = os.path.join(config["runtime"]["workspace_dir"], "tomorrow_reels")
    vid_files = sorted(glob.glob(os.path.join(queue_dir, "ready_*.mp4")))

    # If buffer is low or empty, auto-replenish
    if len(vid_files) < target_slots_to_catch:
        print(f"🔄 [{display_name}] Buffer low ({len(vid_files)}). Replenishing queue...")
        try:
            from replenish_all_queues import replenish_channel_queue, CHANNELS_TO_REPLENISH
            ch_info = next((c for c in CHANNELS_TO_REPLENISH if c["channel_id"] == channel_id), None)
            if ch_info:
                ch_copy = dict(ch_info)
                ch_copy["target_buffer"] = target_slots_to_catch
                replenish_channel_queue(ch_copy)
                vid_files = sorted(glob.glob(os.path.join(queue_dir, "ready_*.mp4")))
        except Exception as e:
            print(f"Replenish notice: {e}")

    posted_count = 0
    for vid_file in vid_files:
        if posted_count >= target_slots_to_catch:
            break

        stem = Path(vid_file).stem
        meta_file = os.path.join(queue_dir, f"{stem}.json")

        if not os.path.exists(meta_file):
            continue

        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        shortcode = meta.get("shortcode")
        title = meta.get("title", "Viral Reel")
        caption = meta.get("caption", f"Insights from {handle}")
        creator = meta.get("creator", "creator")

        if db.is_reel_processed(shortcode):
            continue

        if db.get_today_count() >= 30:
            print(f"🎯 [{display_name}] Daily quota reached (30/30).")
            break

        print(f"\n▶ [{display_name}] Catch-up publishing: {shortcode} - {title[:35]}...")

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
                    if "limit" in str(err).lower() or "quota" in str(err).lower():
                        break
            else:
                print(f"⚠️ [{display_name}] Could not send video to Telegram CDN.")

            time.sleep(20)

        except Exception as e:
            print(f"❌ Error during catch-up for {channel_id}: {e}")

    return posted_count

def run_all_catchup():
    print("========================================================")
    print("  🚀 MULTI-CHANNEL CATCH-UP RUNNER (ALL 7 CHANNELS)")
    print("========================================================")
    for ch_id, name, handle in CHANNELS:
        catchup_channel(ch_id, name, handle, target_slots_to_catch=2)
        time.sleep(10)

if __name__ == '__main__':
    run_all_catchup()
