import sys
import os
import requests
import json
import time

sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase

def run():
    channel_id = "trading_road24"
    config = get_channel_config(channel_id)
    print(f"Target Channel: {config['display_name']} (@{config['instagram_username']})", flush=True)

    creds = config["credentials"]
    ig_id = creds["instagram_account_id"]
    token = creds["page_access_token"]
    bot_token = creds["telegram_bot_token"]
    chat_id = creds["telegram_chat_id"]

    print(f"IG ID: {ig_id}", flush=True)

    hub = TelegramHub(bot_token, chat_id)
    publisher = InstagramPublisher(ig_id, token)
    db = ChannelDatabase(config["runtime"]["db_path"])

    video_path = r"C:\reel_cache\trading_pulse\archive_posted\ready_07_DeJ7IivThdz.mp4"
    meta_path = r"C:\reel_cache\trading_pulse\archive_posted\ready_07_DeJ7IivThdz.json"

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    title = meta.get("title", "Price Action Rule")
    caption = meta.get("caption", "Trading insights from @trading_road24")
    shortcode = meta.get("shortcode", "DeJ7IivThdz")
    first_comment = config.get("content_settings", {}).get("first_comment_template", "What chart pattern do you trust the most? 📊")

    print(f"\n🚀 Publishing Reel: {title}", flush=True)
    print(f"Video File: {video_path} ({os.path.getsize(video_path)} bytes)", flush=True)

    print("\n[Step 1] Uploading to Telegram for Meta Public CDN URL...", flush=True)
    sent, cdn_url = hub.send_video_with_cdn_url(video_path, f"<b>[@trading_road24]</b>\n\n{caption}")
    print(f"Telegram Sent: {sent}", flush=True)
    print(f"CDN URL: {cdn_url}", flush=True)

    if not sent or not cdn_url:
        print("❌ Failed to get CDN URL from Telegram.", flush=True)
        return

    print("\n[Step 2] Sending Container Creation to Meta Graph API...", flush=True)
    pub_res = publisher.publish_reel(
        public_video_url=cdn_url,
        caption=caption,
        first_comment=first_comment
    )

    print(f"Meta Publish Response: {pub_res}", flush=True)

    if pub_res and "permalink" in pub_res:
        permalink = pub_res["permalink"]
        print(f"\n🎉 SUCCESS! Reel is LIVE on @trading_road24: {permalink}", flush=True)
        db.mark_reel_processed(shortcode, "trading_road24", title, permalink)
    else:
        print(f"❌ Failed to publish reel to Meta API.", flush=True)

if __name__ == '__main__':
    run()

