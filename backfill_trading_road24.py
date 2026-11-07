import os
import sys
import time
import json
import glob
import argparse
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase
from core.iron_shield import CircuitBreaker

CHANNEL_ID = "trading_road24"
ARCHIVE_DIR = r"C:\reel_cache\trading_road24\archive_posted"

def check_publishing_quota(account_id, access_token):
    """Checks the official Meta content publishing limit."""
    import requests
    url = f"https://graph.facebook.com/v21.0/{account_id}/content_publishing_limit"
    params = {"access_token": access_token, "fields": "quota_usage,config"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [{}])[0]
            usage = data.get("quota_usage", 0)
            total = data.get("config", {}).get("quota_total", 100)
            return usage, total
    except Exception as e:
        print(f"⚠️ Error checking Meta quota: {e}")
    return 0, 100

def publish_next_backfill_reel(interactive=False):
    """
    Finds the next unposted reel in TR24 archive and publishes it via Meta Graph API.
    Returns: (bool success, str shortcode, str permalink)
    """
    config = get_channel_config(CHANNEL_ID)
    creds = config.get("credentials", {})
    ig_id = creds.get("instagram_account_id")
    token = creds.get("page_access_token")

    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(ig_id, token)
    db = ChannelDatabase(config["runtime"]["db_path"])

    # 1. Check Circuit Breaker
    is_locked, reason = CircuitBreaker.is_channel_locked(CHANNEL_ID)
    if is_locked:
        print(f"🛑 [Circuit Breaker Lock] Channel is locked: {reason}")
        return False, None, None

    # 2. Check Meta Graph API Quota
    usage, total = check_publishing_quota(ig_id, token)
    print(f"📊 Meta API Quota: {usage}/{total} used today.")
    if usage >= total - 2:
        print("🛑 Meta publishing quota near maximum for today. Sleeping to prevent rate limits.")
        return False, None, None

    # 3. Find candidate videos
    all_jsons = sorted(glob.glob(os.path.join(ARCHIVE_DIR, "ready_*.json")))
    if not all_jsons:
        print("⚠️ No reels found in archive directory.")
        return False, None, None

    target_json = None
    target_vid = None
    target_meta = None

    for jf in all_jsons:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                meta = json.load(f)
            sc = meta.get("shortcode")
            if sc and not db.is_reel_processed(sc) and not db.is_reel_rejected(sc):
                vf = jf.rsplit(".", 1)[0] + ".mp4"
                if os.path.exists(vf):
                    # Gatekeeper Security Pre-Flight Check
                    from core.compliance_guard import is_reel_compliant
                    is_safe, reason = is_reel_compliant(meta.get("title", ""), meta.get("hook_pill", ""), meta.get("caption", ""))
                    if not is_safe:
                        print(f"🛑 [Gatekeeper Security REJECTED] Reel {sc} rejected: {reason}. Marking in rejected DB.")
                        db.mark_reel_rejected(sc, reason)
                        continue
                    target_json = jf
                    target_vid = vf
                    target_meta = meta
                    break
        except Exception:
            continue

    if not target_vid:
        print("🎉 ALL HISTORICAL REELS HAVE BEEN POSTED ON @trading_road24! Nothing left to backfill.")
        return False, None, "ALL_COMPLETED"

    sc = target_meta.get("shortcode")
    title = target_meta.get("title", "Trading Lesson")
    creator = target_meta.get("creator", "creator")
    caption = target_meta.get("caption", f"Insights from @{creator}")

    print(f"\n🚀 [Meta API Dispatch] Publishing Next Backfill Reel: {sc} -> {title.splitlines()[0]}...")
    print(f"📁 Video: {os.path.basename(target_vid)} ({os.path.getsize(target_vid)/(1024*1024):.2f} MB)")

    try:
        # Step A: Telegram CDN Upload
        sent, cdn_url = hub.send_video_with_cdn_url(
            target_vid, 
            caption=f"<b>[📈 Trading Road 24 - Backfill]</b>\n\n<b>Title:</b> {title}\n\n{caption[:300]}..."
        )
        if not sent or not cdn_url:
            print("❌ Failed to obtain Telegram CDN URL.")
            return False, sc, None

        # Step B: Meta Graph API Publishing
        first_comment = config.get("content_settings", {}).get("first_comment_template")
        res = publisher.publish_reel(
            public_video_url=cdn_url,
            caption=caption,
            creator_username=creator,
            first_comment=first_comment
        )

        if res and "permalink" in res:
            link = res["permalink"]
            print(f"🎉 100% SUCCESS! Reel LIVE on Instagram: {link}")
            db.mark_reel_processed(sc, creator, title, link)
            hub.send_message(
                f"🎉 <b>@trading_road24 Reel LIVE!</b>\n\n"
                f"🎬 <b>Title:</b> {title}\n"
                f"🔗 <b>Watch Reel:</b> {link}\n"
                f"📊 <b>Quota Usage:</b> {usage + 1}/{total}"
            )
            return True, sc, link
        else:
            err = res.get("error", "Unknown error") if res else "No response"
            print(f"⚠️ Meta API Error: {err}")
    except Exception as e:
        print(f"❌ Exception during backfill publish: {e}")

    return False, sc, None

def run_paced_backfill(interval_seconds=300, max_posts=None):
    """
    Paced Backfill Daemon:
    Publishes remaining reels with a safe anti-spam interval (default: 5 minutes / 300 seconds)
    to strictly adhere to Meta velocity regulations and prevent account flagging.
    """
    print("========================================================")
    print("  🚀 PACED BACKFILL DAEMON FOR @trading_road24")
    print("========================================================")
    print(f"Safety Interval: {interval_seconds} seconds ({interval_seconds/60:.1f} minutes) between reels")
    print(f"Target Max Posts: {max_posts if max_posts else 'All Pending'}")
    print("Meta API Compliance: 100% Graph API with Container Polling")
    print("========================================================\n")

    count = 0
    while True:
        success, sc, link = publish_next_backfill_reel()
        if link == "ALL_COMPLETED":
            print("🏆 All historical reels have been successfully backfilled!")
            break

        if success:
            count += 1
            print(f"✅ Post #{count} completed ({sc}).")
            if max_posts and count >= max_posts:
                print(f"🏁 Reached target batch limit of {max_posts} reels. Exiting.")
                break

            print(f"⏳ Sleeping {interval_seconds}s for Meta anti-spam safety pacing before next reel...")
            time.sleep(interval_seconds)
        else:
            print("⚠️ Dispatch failed or rate limit hit. Backing off 3 minutes...")
            time.sleep(180)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paced Backfill for @trading_road24")
    parser.add_argument("--once", action="store_true", help="Publish exactly one pending reel and exit")
    parser.add_argument("--interval", type=int, default=300, help="Interval between reels in seconds (default: 300)")
    parser.add_argument("--batch", type=int, default=None, help="Maximum number of reels to post in this run")
    args = parser.parse_args()

    if args.once:
        publish_next_backfill_reel(interactive=True)
    else:
        run_paced_backfill(interval_seconds=args.interval, max_posts=args.batch)

