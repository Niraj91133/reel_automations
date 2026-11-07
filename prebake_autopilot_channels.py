import os
import sys
import time
import json
import shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from scraper import download_reel_video

AUTOPILOT_CHANNELS = [
    ("startup_road", "💼 Startup Road", "@startup_road"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_"),
    ("healthy_diet", "🥗 Gudtree", "@gudtree_"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road")
]

def prebake_channel_reels(channel_id, count=30):
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", channel_id)
    workspace_dir = config["runtime"]["workspace_dir"]
    db = ChannelDatabase(config["runtime"]["db_path"])
    queue_dir = os.path.join(workspace_dir, "tomorrow_reels")
    os.makedirs(queue_dir, exist_ok=True)

    print(f"\n========================================================")
    print(f"🌙 [10 PM - 02 AM EDITING WINDOW] Pre-baking {count} Reels for: {display_name}")
    print(f"========================================================")

    # 1. Candidate Sourcing:
    candidates = []
    if channel_id == "startup_road":
        # Check if Raj approved any reels in DM
        try:
            from core.niche_hunter import fetch_approved_reels_from_raj
            approved = fetch_approved_reels_from_raj(config, max_count=count)
            approved_codes = {r["shortcode"] for r in approved}
            for r in approved:
                candidates.append((r["shortcode"], r.get("creator", "approved_creator"), "Raj Approved"))
        except Exception as e:
            approved_codes = set()
            print(f"Note on Raj DM fetch: {e}")

        # Auto-Fallback: If Raj/User didn't finalize 30 reels before 10 PM, auto-fill from viral pool!
        if len(candidates) < count:
            remaining = count - len(candidates)
            print(f"ℹ️ [Startup Road 10 PM Auto-Fallback] Raj approved {len(candidates)}/{count}. Auto-filling {remaining} best viral reels from DB pool!")
            pool_candidates = db.get_unprocessed_hunted_reels(limit=remaining * 2)
            for sc, cr, vw in pool_candidates:
                if sc not in approved_codes:
                    candidates.append((sc, cr, vw))
                    approved_codes.add(sc)
                if len(candidates) >= count:
                    break
    else:
        # Autopilot Channels: Fetch 30 unprocessed viral candidates from hunted pool
        candidates = db.get_unprocessed_hunted_reels(limit=count * 2)
        if not candidates:
            print(f"⚠️ No hunted candidates in pool for {display_name}. Trying live scout...")
            from core.full_autopilot import scout_single_viral_reel_for_channel
            for _ in range(count):
                c = scout_single_viral_reel_for_channel(channel_id)
                if c:
                    candidates.append((c["shortcode"], c["creator"], c.get("views", "Viral")))
                    time.sleep(2)

    baked = []
    idx = 1
    for shortcode, creator, views_text in candidates:
        if idx > count:
            break

        out_file = os.path.join(queue_dir, f"ready_{idx:02d}_{shortcode}.mp4")
        meta_file = os.path.join(queue_dir, f"ready_{idx:02d}_{shortcode}.json")

        if os.path.exists(out_file) and os.path.getsize(out_file) > 100_000 and os.path.exists(meta_file):
            print(f"[{idx}/{count}] Already pre-baked: {out_file}")
            baked.append((idx, shortcode, creator, "Already Baked"))
            idx += 1
            continue

        reel_url = f"https://www.instagram.com/reel/{shortcode}/"
        print(f"\n▶ [{idx}/{count}] Pre-baking {shortcode} (by @{creator}, {views_text})...")

        # Download
        temp_dl = os.path.join(queue_dir, f"raw_{shortcode}.mp4")
        cookie_file = os.path.join(BASE_DIR, f"cookies/{channel_id}_cookies.txt")
        raw_video = download_reel_video(reel_url, temp_dl, cookie_file=cookie_file)

        if not raw_video or not os.path.exists(raw_video):
            print(f"⚠️ Failed download for {shortcode}. Trying next candidate.")
            continue

        try:
            # AI synthesis
            ai_data = analyze_reel_for_channel(raw_video, config, creator)
            hook_pill = ai_data.get("hook_pill", "KEY TAKEAWAY")
            main_title = ai_data.get("main_title", "VIRAL INSIGHT")
            sub_quote = ai_data.get("sub_quote", "")
            caption = ai_data.get("caption", f"Insights from @{creator}")

            # Meta Policy Pre-Render Compliance Check
            from core.compliance_guard import is_reel_compliant
            is_safe, reason = is_reel_compliant(main_title, hook_pill, caption)
            if not is_safe:
                print(f"🛑 [Compliance Guard SKIPPED] Reel {shortcode} rejected: {reason}")
                continue

            # GPU FFmpeg render
            rendered_temp, _ = render_channel_video(
                input_video_path=raw_video,
                channel_config=config,
                hook_pill=hook_pill,
                main_title=main_title,
                sub_quote=sub_quote
            )

            shutil.move(rendered_temp, out_file)

            # Metadata JSON
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "shortcode": shortcode,
                    "creator": creator,
                    "title": main_title,
                    "caption": caption,
                    "hook_pill": hook_pill
                }, f, indent=2)

            baked.append((idx, shortcode, creator, main_title))
            print(f"✅ [{idx}/{count}] Successfully pre-baked: {main_title}")
            idx += 1

        except Exception as e:
            print(f"❌ Error pre-baking {shortcode}: {e}")
        finally:
            if os.path.exists(temp_dl):
                try: os.remove(temp_dl)
                except: pass

    print(f"🎉 Completed pre-baking {len(baked)}/{count} reels for {display_name}!")
    return baked

def prebake_all_4_channels():
    summary = {}
    for ch_id, name, handle in AUTOPILOT_CHANNELS:
        res = prebake_channel_reels(ch_id, count=30)
        summary[name] = res
        time.sleep(3)
    return summary

if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        count = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30
        prebake_channel_reels(args[0], count=count)
    else:
        prebake_all_4_channels()

