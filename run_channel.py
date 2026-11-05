import os
import sys
import argparse
import time
import glob
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

from core.config_manager import get_channel_config, list_available_channels
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from dm_scraper import get_shared_reels_from_chat
from scraper import download_reel_video

def get_channel_candidate_reels(channel_config, max_count=5):
    """
    Finds candidate reels for a channel:
    1. Checks if raw video files are placed in workspaces/{channel_id}/inbox/
    2. Otherwise, scrapes from the channel's target Instagram DM chat (e.g. im_raaaj_)
    """
    channel_id = channel_config["channel_id"]
    workspace_dir = channel_config["runtime"]["workspace_dir"]
    inbox_dir = os.path.join(workspace_dir, "inbox")
    os.makedirs(inbox_dir, exist_ok=True)

    # Check local inbox directory first (both in active cache and project workspace)
    local_videos = []
    for idir in [inbox_dir, os.path.join(str(Path(__file__).resolve().parent), "workspaces", channel_id, "inbox")]:
        if os.path.exists(idir):
            local_videos.extend(glob.glob(os.path.join(idir, "*.mp4")))
    # Deduplicate by stem
    seen_stems = set()
    unique_local = []
    for vid in local_videos:
        stem = Path(vid).stem
        if stem not in seen_stems:
            seen_stems.add(stem)
            unique_local.append(vid)
    local_videos = unique_local
    candidates = []

    for vid in local_videos[:max_count]:
        shortcode = Path(vid).stem
        candidates.append({
            "shortcode": shortcode,
            "video_path": vid,
            "creator": "creator",
            "is_local": True
        })

    if candidates:
        return candidates

    # If no local inbox video, fetch Raj-approved reels from chat
    dm_target = channel_config.get("hunting_settings", {}).get("dm_target_chat") or channel_config.get("content_settings", {}).get("dm_target_chat", "im_raaaj_")
    print(f"[{channel_config['display_name']}] Checking Raj-approved reels from chat: @{dm_target}...")
    try:
        from core.niche_hunter import fetch_approved_reels_from_raj
        shared = fetch_approved_reels_from_raj(channel_config, max_count=max_count)
        if not shared:
            shared = get_shared_reels_from_chat(max_count=max_count)
        for item in shared:
            candidates.append({
                "shortcode": item.get("shortcode"),
                "url": item.get("url"),
                "creator": item.get("creator", "creator"),
                "is_local": False
            })
    except Exception as e:
        print(f"Note on DM fetching for {channel_id}: {e}")

    return candidates

def process_channel_pipeline(channel_id, max_reels=1, dry_run=False):
    """
    Executes the end-to-end pipeline for a single channel in full isolation.
    """
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", channel_id)
    print(f"\n========================================================")
    print(f"🚀 STARTING PIPELINE: {display_name.upper()} (ID: {channel_id})")
    print(f"========================================================")

    db = ChannelDatabase(config["runtime"]["db_path"])
    creds = config.get("credentials", {})
    
    hub = TelegramHub(
        bot_token=creds.get("telegram_bot_token"),
        default_chat_id=creds.get("telegram_chat_id")
    )
    
    publisher = InstagramPublisher(
        instagram_account_id=creds.get("instagram_account_id"),
        page_access_token=creds.get("page_access_token")
    )

    candidates = get_channel_candidate_reels(config, max_count=max(max_reels * 2, 4))
    if not candidates:
        msg = f"ℹ️ <b>[{display_name}]</b> Koi naye reels nahi mile inbox/DM me."
        print(msg)
        hub.send_message(msg)
        return 0

    processed_count = 0
    workspace_dir = config["runtime"]["workspace_dir"]

    for item in candidates:
        if processed_count >= max_reels:
            break

        shortcode = item.get("shortcode")
        creator = item.get("creator", "creator")
        if not shortcode:
            continue

        if db.is_reel_processed(shortcode):
            print(f"[{display_name}] Reel {shortcode} already processed. Skipping.")
            continue

        print(f"\n🎬 [{display_name}] Processing candidate: {shortcode} (by @{creator})")

        # 1. Download or locate video
        raw_video_path = None
        if item.get("is_local"):
            raw_video_path = item["video_path"]
        else:
            download_dir = os.path.join(workspace_dir, "downloads")
            os.makedirs(download_dir, exist_ok=True)
            dest_file = os.path.join(download_dir, f"{shortcode}.mp4")
            raw_video_path = download_reel_video(item.get("url"), dest_file)

        if not raw_video_path or not os.path.exists(raw_video_path):
            print(f"❌ Failed to obtain raw video for {shortcode}")
            continue

        try:
            # 2. AI Hook & Synthesis with channel's Gemini Key
            print(f"🤖 Calling Gemini AI for [{display_name}] content synthesis...")
            ai_data = analyze_reel_for_channel(
                video_file_path=raw_video_path,
                channel_config=config,
                creator_username=creator
            )

            hook_pill = ai_data.get("hook_pill", "KEY TAKEAWAY")
            main_title = ai_data.get("main_title", "IMPORTANT LESSON")
            sub_quote = ai_data.get("sub_quote", "")
            caption = ai_data.get("caption", f"Insights from @{creator}")

            print(f"🎯 Pill: {hook_pill}")
            print(f"🎯 Title: {main_title}")

            # 3. Isolated Render with channel's visual template
            print(f"🎨 Rendering branded video...")
            rendered_video_path, job_id = render_channel_video(
                input_video_path=raw_video_path,
                channel_config=config,
                hook_pill=hook_pill,
                main_title=main_title,
                sub_quote=sub_quote
            )

            # 4. Telegram Delivery & CDN URL extraction
            print(f"📤 Sending preview to Telegram channel...")
            caption_with_tag = f"<b>[{display_name}]</b>\n\n{caption}"
            sent, public_cdn_url = hub.send_video_with_cdn_url(rendered_video_path, caption_with_tag)

            # 5. Instagram Auto-Publishing (Official Meta Graph API)
            live_permalink = None
            first_comment = config.get("content_settings", {}).get("first_comment_template")
            if sent and public_cdn_url and not dry_run:
                if publisher.is_configured():
                    print(f"🚀 Publishing to Instagram feed...")
                    pub_res = publisher.publish_reel(
                        public_video_url=public_cdn_url,
                        caption=caption,
                        creator_username=creator,
                        first_comment=first_comment
                    )
                    if pub_res and "permalink" in pub_res:
                        live_permalink = pub_res["permalink"]
                        print(f"🏆 Reel LIVE on Instagram: {live_permalink}")
                        first_cm_note = f"\n💬 <b>First Comment:</b> {first_comment}" if first_comment else ""
                        hub.send_message(
                            f"🎉 <b>Reel LIVE on Instagram [{display_name}]!</b>\n\n🔗 <b>Watch:</b> {live_permalink}{first_cm_note}"
                        )
                else:
                    print(f"ℹ️ Instagram not configured for {channel_id}. Saved to Telegram approval queue.")

            # 6. Mark processed in isolated DB
            db.mark_reel_processed(shortcode, creator, main_title, live_permalink)
            processed_count += 1
            print(f"✅ [{display_name}] Reel {shortcode} successfully completed!")

            # Cleanup rendered file if not dry run
            if rendered_video_path and os.path.exists(rendered_video_path):
                try: os.remove(rendered_video_path)
                except: pass

        except Exception as e:
            print(f"❌ Error processing reel {shortcode} for {channel_id}: {e}")
        finally:
            # Cleanup raw video if downloaded
            if not item.get("is_local") and raw_video_path and os.path.exists(raw_video_path):
                try: os.remove(raw_video_path)
                except: pass

    print(f"\n✨ [{display_name}] Pipeline finished. Processed {processed_count} reel(s).")
    return processed_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Channel Reel Pipeline Runner")
    parser.add_argument("--channel", type=str, default="startup_road", help="Channel ID (startup_road, healthy_diet, trading_pulse, viral_finds)")
    parser.add_argument("--limit", type=int, default=1, help="Max reels to process in this run")
    parser.add_argument("--dry-run", action="store_true", help="Render & send to Telegram without posting to Instagram")
    args = parser.parse_args()

    process_channel_pipeline(channel_id=args.channel, max_reels=args.limit, dry_run=args.dry_run)
