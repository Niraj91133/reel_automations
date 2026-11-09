import os
import sys
import time
import random
import re
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
from core.niche_scout import NICHE_DISCOVERY_PROFILES, parse_views_count
from core.niche_hunter import get_channel_cookies
from scraper import download_reel_video
from playwright.sync_api import sync_playwright

def scout_single_viral_reel_for_channel(channel_id):
    """
    Scouts 1 fresh high-view viral reel for a specific channel.
    Checks top niche creators and fallback hashtags.
    Guarantees the reel was never processed or published before.
    """
    config = get_channel_config(channel_id)
    db = ChannelDatabase(config["runtime"]["db_path"])

    profile = NICHE_DISCOVERY_PROFILES.get(channel_id, {})
    creators = list(profile.get("creators", []))
    random.shuffle(creators)

    cookies = get_channel_cookies(channel_id)
    chromium_args = [
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--renderer-process-limit=2",
        "--mute-audio"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=chromium_args)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        candidate = None

        # 1. Search top creators
        for creator in creators[:6]:
            try:
                url = f"https://www.instagram.com/{creator}/reels/"
                page.goto(url, timeout=25000, wait_until='domcontentloaded')
                page.wait_for_timeout(3500)
                page.evaluate("window.scrollBy(0, 800)")
                page.wait_for_timeout(1500)

                links = page.query_selector_all('a[href*="/reel/"]')
                for link in links[:12]:
                    href = link.get_attribute("href") or ""
                    m = re.search(r'/reel/([^/?]+)', href)
                    if not m:
                        continue
                    code = m.group(1).strip()
                    if db.is_reel_processed(code):
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
            except Exception:
                pass

        # 2. Fallback to Hashtags if creators didn't return
        if not candidate:
            hashtags = list(config.get("hunting_settings", {}).get("hashtags", []))
            random.shuffle(hashtags)
            for tag in hashtags[:4]:
                clean_tag = tag.replace('#', '').strip()
                try:
                    url = f"https://www.instagram.com/explore/tags/{clean_tag}/"
                    page.goto(url, timeout=25000, wait_until='domcontentloaded')
                    page.wait_for_timeout(3500)
                    page.evaluate("window.scrollBy(0, 800)")
                    page.wait_for_timeout(1500)

                    links = page.query_selector_all('a[href*="/reel/"], a[href*="/p/"]')
                    for link in links[:10]:
                        href = link.get_attribute("href") or ""
                        m = re.search(r'/(?:reel|p)/([^/?]+)', href)
                        if not m:
                            continue
                        code = m.group(1).strip()
                        if db.is_reel_processed(code):
                            continue

                        card_text = link.inner_text().strip().replace('\n', ' ')
                        candidate = {
                            "shortcode": code,
                            "creator": f"#{clean_tag}",
                            "url": f"https://www.instagram.com/reel/{code}/",
                            "views": card_text or "Trending"
                        }
                        break
                    if candidate:
                        break
                except Exception:
                    pass

        browser.close()
        return candidate

def run_channel_autopilot(channel_id):
    """
    100% Hands-Off Autopilot for a Single Channel:
    1. AI Scout discovers viral reel
    2. Downloads raw video to local cache
    3. Gemini AI writes hook & caption
    4. Hardware FFmpeg renders 9:16 branded reel in ~5 seconds
    5. Official Meta Graph API publishes directly to live Instagram feed
    6. Telegram receives confirmation & live permalink
    """
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", channel_id)
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
    print(f"🤖 FULL AUTOPILOT PIPELINE: [{display_name}]")
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
    os.makedirs(download_dir, exist_ok=True)
    download_file_path = os.path.join(download_dir, f"{shortcode}.mp4")
    
    cookie_file = os.path.join(BASE_DIR, f"cookies/{channel_id}_cookies.txt")
    raw_video = download_reel_video(reel_url, download_file_path, cookie_file=cookie_file)
    if not raw_video or not os.path.exists(raw_video):
        print(f"❌ Failed to download {shortcode}")
        return False

    try:
        # 3. AI Hook Synthesis
        print(f"🤖 Calling Gemini AI for [{display_name}] content synthesis...")
        ai_data = analyze_reel_for_channel(
            video_file_path=raw_video,
            channel_config=config,
            creator_username=creator
        )
        if ai_data.get("rejected"):
            print(f"⚠️ Skipping candidate {shortcode} for {display_name}: {ai_data.get('reason')}")
            return False

        hook_pill = ai_data.get("hook_pill", "VIRAL LESSON")
        main_title = ai_data.get("main_title", "KEY TAKEAWAY")
        sub_quote = ai_data.get("sub_quote", "")
        
        # Guarantee rich, multi-paragraph, engaging caption "pehle jaisa"
        from core.caption_engine import generate_rich_caption
        caption = ai_data.get("caption", "")
        if not caption or len(caption.splitlines()) <= 3 or len(caption) < 150 or "valuable insights" in caption.lower() or "strategic insights for modern" in caption.lower():
            caption = generate_rich_caption(channel_id, main_title, hook_pill, creator)

        # 4. Branded Video Render (GPU Hardware Accelerated)
        print(f"🎨 Rendering branded video with {display_name} theme (GPU)...")
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

        # 6. Official Meta Graph API Direct Auto-Post + First Comment
        live_permalink = None
        first_comment = config.get("content_settings", {}).get("first_comment_template")
        if sent and cdn_url and publisher.is_configured():
            print(f"🚀 [Meta Graph API] AUTO-PUBLISHING directly to live feed...")
            pub_res = publisher.publish_reel(
                public_video_url=cdn_url,
                caption=caption,
                creator_username=creator,
                first_comment=first_comment
            )
            if pub_res and "permalink" in pub_res:
                live_permalink = pub_res["permalink"]
                print(f"🏆 SUCCESS! Reel is LIVE on Instagram: {live_permalink}")
                first_cm_note = f"\n💬 <b>First Comment:</b> {first_comment}" if first_comment else ""
                hub.send_message(
                    f"🎉 <b>Autopilot Reel LIVE on Instagram!</b>\n\n"
                    f"📺 <b>Channel:</b> {display_name}\n"
                    f"🎬 <b>Title:</b> {main_title}\n"
                    f"🔗 <b>Watch Reel:</b> {live_permalink}{first_cm_note}"
                )

        # 7. Record in Database
        db.mark_reel_processed(shortcode, creator, main_title, live_permalink)
        print(f"✅ [{display_name}] Autopilot run complete!\n")
        return True

    except Exception as e:
        print(f"❌ Autopilot error for {channel_id}: {e}")
        return False
    finally:
        if raw_video and os.path.exists(raw_video):
            try: os.remove(raw_video)
            except: pass

def run_3_channels_autopilot_cycle():
    """
    Runs 1 complete autopilot cycle across the 3 selected channels:
    - Trading Road (trading_pulse)
    - Gudtree (healthy_diet)
    - Trending Road (viral_finds)
    Excludes Startup Road completely!
    """
    AUTOPILOT_CHANNELS = ["trading_pulse", "healthy_diet", "viral_finds"]
    results = {}
    for ch in AUTOPILOT_CHANNELS:
        success = run_channel_autopilot(ch)
        results[ch] = success
        time.sleep(10)
    return results

if __name__ == '__main__':
    args = sys.argv[1:]
    target = args[0] if args else "3_channels"

    if target in ["3_channels", "all_3", "autopilot"]:
        run_3_channels_autopilot_cycle()
    elif target in ["trading_pulse", "healthy_diet", "viral_finds"]:
        run_channel_autopilot(target)
    else:
        print(f"Usage: python core/full_autopilot.py [3_channels | trading_pulse | healthy_diet | viral_finds]")
