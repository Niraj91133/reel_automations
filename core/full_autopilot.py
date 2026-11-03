import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config, list_available_channels
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.niche_scout import NICHE_DISCOVERY_PROFILES, parse_cookie_file, COOKIE_FILE, is_shortcode_scouted, parse_views_count
from scraper import download_reel_video
from playwright.sync_api import sync_playwright

def scout_single_viral_reel_for_channel(channel_id):
    """Scouts 1 fresh high-view viral reel for a specific channel."""
    niche_key = channel_id
    if niche_key not in NICHE_DISCOVERY_PROFILES:
        return None

    profile = NICHE_DISCOVERY_PROFILES[niche_key]
    creators = list(profile["creators"])
    import random
    random.shuffle(creators)

    cookies = parse_cookie_file(COOKIE_FILE)
    chromium_args = [
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--renderer-process-limit=2",
        "--blink-settings=imagesEnabled=false",
        "--mute-audio"
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=chromium_args)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        # Block images/media/fonts to reduce RAM by 85%
        def block_heavy(route):
            if route.request.resource_type in ["image", "media", "font"]:
                route.abort()
            else:
                route.continue_()
        page.route("**/*", block_heavy)

        candidate = None
        for creator in creators:
            try:
                url = f"https://www.instagram.com/{creator}/reels/"
                page.goto(url, timeout=25000, wait_until='domcontentloaded')
                time.sleep(2)

                links = page.query_selector_all('a[href*="/reel/"]')
                for link in links[:8]:
                    href = link.get_attribute("href")
                    if not href or "/reel/" not in href:
                        continue

                    code = href.split("/reel/")[1].split("/")[0].strip()
                    if not code or is_shortcode_scouted(code):
                        continue

                    card_text = link.inner_text().strip().replace('\n', ' ')
                    views_num = parse_views_count(card_text)

                    # Viral filter: >= 25k views or 'M'
                    if 'M' in card_text.upper() or views_num >= 25_000 or not card_text:
                        candidate = {
                            "shortcode": code,
                            "creator": creator,
                            "url": f"https://www.instagram.com/reel/{code}/",
                            "views": card_text or "Viral"
                        }
                        break
                if candidate:
                    break
            except:
                pass

        browser.close()
        return candidate

def run_channel_autopilot(channel_id):
    """
    100% Hands-Off Autopilot for a Single Channel:
    1. AI Scout researches viral reel
    2. Downloads raw video
    3. Gemini AI writes hook & caption
    4. FFmpeg renders Ultra-HD branded reel
    5. Official Meta Graph API publishes directly to live Instagram feed
    6. Telegram receives confirmation & permalink
    """
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", channel_id)
    username = config.get("instagram_username", channel_id)
    workspace_dir = config["runtime"]["workspace_dir"]
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

    print(f"\n========================================================")
    print(f"🤖 FULL AUTOPILOT RUN: [{display_name}] (@{username})")
    print(f"========================================================")

    # 1. AI Scout
    print(f"🔍 Searching viral content for {display_name}...")
    candidate = scout_single_viral_reel_for_channel(channel_id)
    if not candidate:
        print(f"⚠️ No fresh candidate found for {display_name}.")
        return False

    shortcode = candidate["shortcode"]
    creator = candidate["creator"]
    reel_url = candidate["url"]
    print(f"🎯 Discovered Viral Reel: {reel_url} by @{creator} (Views: {candidate['views']})")

    # 2. Download
    download_dir = os.path.join(workspace_dir, "downloads")
    download_file_path = os.path.join(download_dir, f"{shortcode}.mp4")
    raw_video = download_reel_video(reel_url, download_file_path)
    if not raw_video or not os.path.exists(raw_video):
        print(f"❌ Failed to download {shortcode}")
        return False

    try:
        # 3. AI Hook Synthesis
        print(f"🤖 Calling dedicated Gemini AI for [{display_name}]...")
        ai_data = analyze_reel_for_channel(
            video_file_path=raw_video,
            channel_config=config,
            creator_username=creator
        )

        hook_pill = ai_data.get("hook_pill", "VIRAL LESSON")
        main_title = ai_data.get("main_title", "KEY TAKEAWAY")
        sub_quote = ai_data.get("sub_quote", "")
        caption = ai_data.get("caption", f"Insights from @{creator}")

        # 4. Branded Video Render
        print(f"🎨 Rendering branded video with {display_name} theme...")
        rendered_video, job_id = render_channel_video(
            input_video_path=raw_video,
            channel_config=config,
            hook_pill=hook_pill,
            main_title=main_title,
            sub_quote=sub_quote
        )

        # 5. Telegram CDN Upload
        print(f"📤 Uploading to Telegram CDN...")
        caption_formatted = f"<b>[{display_name}]</b>\n\n{caption}"
        sent, cdn_url = hub.send_video_with_cdn_url(rendered_video, caption_formatted)

        # 6. Official Meta Graph API Direct Auto-Post
        live_permalink = None
        if sent and cdn_url and publisher.is_configured():
            print(f"🚀 [Meta Graph API] AUTO-PUBLISHING directly to @{username} feed...")
            pub_res = publisher.publish_reel(cdn_url, caption, creator_username=creator)
            if pub_res and "permalink" in pub_res:
                live_permalink = pub_res["permalink"]
                print(f"🏆 SUCCESS! Reel is LIVE on Instagram: {live_permalink}")
                hub.send_message(
                    f"🎉 <b>Reel LIVE on Instagram!</b>\n\n"
                    f"👤 <b>Account:</b> @{username}\n"
                    f"🎬 <b>Title:</b> {main_title}\n"
                    f"🔗 <b>Watch Reel:</b> {live_permalink}"
                )

        # 7. Record in Database
        db.mark_reel_processed(shortcode, creator, main_title, live_permalink)
        print(f"✅ [{display_name}] Autopilot run complete!")
        return True

    except Exception as e:
        print(f"❌ Autopilot error for {channel_id}: {e}")
        return False
    finally:
        if raw_video and os.path.exists(raw_video):
            try: os.remove(raw_video)
            except: pass

def run_channel_batch(channel_id, count=1):
    """Processes multiple reels for a single channel sequentially with cooldown."""
    import gc
    success_count = 0
    for r_idx in range(1, count + 1):
        print(f"\n🎬 Reel [{r_idx}/{count}] for {channel_id}...")
        ok = run_channel_autopilot(channel_id)
        if ok:
            success_count += 1
        gc.collect()
        if r_idx < count:
            print(f"⏳ Pausing 5s before next reel...")
            time.sleep(5)
    return success_count

def run_all_autopilot(reels_per_channel=1):
    """Runs autopilot across all channels sequentially with cooldown."""
    import gc
    channels = list_available_channels()
    for idx, ch in enumerate(channels, 1):
        print(f"\n========================================================")
        print(f"▶ [{idx}/{len(channels)}] Channel Autopilot: {ch} (Target: {reels_per_channel} reels)")
        print(f"========================================================")
        run_channel_batch(ch, count=reels_per_channel)
        gc.collect()
        if idx < len(channels):
            print("\n❄️ Pausing 15s to let CPU & RAM cool down before next channel...")
            time.sleep(15)

if __name__ == '__main__':
    args = sys.argv[1:]
    target = "all"
    count = 1

    for a in args:
        if a.isdigit():
            count = int(a)
        elif a in ["all", "startup_road", "healthy_diet", "trading_pulse", "viral_finds"]:
            target = a

    if target == "all":
        run_all_autopilot(reels_per_channel=count)
    else:
        run_channel_batch(target, count=count)
