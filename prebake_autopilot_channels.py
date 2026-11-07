import os
import sys
import time
import json
import glob
import shutil
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from core.compliance_guard import is_reel_compliant
from scraper import download_reel_video

AUTOPILOT_CHANNELS = [
    ("startup_road", "💼 Startup Road", "@startup_road"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_"),
    ("healthy_diet", "🥗 Gudtree", "@gudtree_"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road"),
    ("trading_road24", "📈 Trading Road 24", "@trading_road24")
]

def prebake_channel_reels(channel_id, count=30):
    """
    Nightly Pre-Baking Engine (10:00 PM Window):
    Prepares exactly 30 high-converting, 100% Meta-compliant reels for tomorrow's dispatch.
    
    Guarantees:
    1. Language: Strictly Hindi audio.
    2. Speech: Clear human voice (No music-only / beats-only).
    3. Gatekeeper Security: Meta Iron Shield checks (no get-rich-quick, no SEBI violation).
    4. Auto-Refill Loop: If any video is rejected, continuously hunts/refills until EXACTLY 30 reels are ready.
    5. Deduplication: Never reuses already processed, hunted, or rejected reels.
    """
    config = get_channel_config(channel_id)
    display_name = config.get("display_name", channel_id)
    workspace_dir = config["runtime"]["workspace_dir"]
    db = ChannelDatabase(config["runtime"]["db_path"])
    queue_dir = os.path.join(workspace_dir, "tomorrow_reels")
    os.makedirs(queue_dir, exist_ok=True)

    print(f"\n========================================================")
    print(f"🌙 [10:00 PM NIGHTLY PRE-BAKING ENGINE] [{display_name}]")
    print(f"Target: Exactly {count} Compliant Reels for Tomorrow's Schedule")
    print(f"========================================================")

    # 1. Audit already baked reels in tomorrow_reels folder
    baked = []
    seen_shortcodes = set()

    for idx in range(1, count + 1):
        vid_p = os.path.join(queue_dir, f"ready_{idx:02d}_*.mp4")
        meta_p = os.path.join(queue_dir, f"ready_{idx:02d}_*.json")
        vids = glob.glob(vid_p)
        metas = glob.glob(meta_p)
        if vids and metas and os.path.getsize(vids[0]) > 100_000:
            try:
                with open(metas[0], "r", encoding="utf-8") as f:
                    m = json.load(f)
                sc = m.get("shortcode")
                if sc and not db.is_reel_rejected(sc) and not db.is_reel_processed(sc):
                    # Check Gatekeeper compliance
                    is_safe, _ = is_reel_compliant(m.get("title", ""), m.get("hook_pill", ""), m.get("caption", ""))
                    if is_safe:
                        baked.append((idx, sc, m.get("creator", "creator"), m.get("title", "")))
                        seen_shortcodes.add(sc)
            except Exception:
                pass

    print(f"📦 Pre-existing Valid Baked Reels: {len(baked)}/{count}")
    if len(baked) >= count:
        print(f"🎉 Channel [{display_name}] ALREADY HAS {len(baked)}/{count} READY REELS FOR TOMORROW!")
        return baked

    # 2. Candidate Sourcing:
    candidates = []

    if channel_id == "startup_road":
        # Check chat with @im_raaaj_
        now = datetime.now()
        is_past_deadline = (now.hour >= 22 or now.hour < 5) # 10 PM onwards
        print(f"📥 Checking Raj's Chat (@im_raaaj_)... (Current Time: {now.strftime('%H:%M:%S')})")

        try:
            from core.niche_hunter import fetch_approved_reels_from_raj
            approved = fetch_approved_reels_from_raj(config, max_count=count)
            for r in approved:
                sc = r.get("shortcode")
                if sc and sc not in seen_shortcodes and not db.is_reel_rejected(sc):
                    candidates.append((sc, r.get("creator", "approved_creator"), "Raj Approved"))
                    seen_shortcodes.add(sc)
            print(f"🎯 Extracted {len(candidates)} reels from Raj's chat.")
        except Exception as e:
            print(f"Note on Raj chat reading: {e}")

        # Auto-Fallback if Raj didn't finalize 30 before 10 PM:
        if len(candidates) < count:
            remaining = count - len(candidates)
            reason = "10 PM Deadline Passed" if is_past_deadline else "Chat has fewer than 30 reels"
            print(f"ℹ️ [{reason}] Auto-finalizing remaining {remaining} reels from high-engagement hunted pool in DB...")
            pool = db.get_unprocessed_hunted_reels(limit=remaining * 3)
            for sc, cr, vw in pool:
                if sc not in seen_shortcodes and not db.is_reel_rejected(sc):
                    candidates.append((sc, cr, vw))
                    seen_shortcodes.add(sc)
                if len(candidates) >= count:
                    break
    else:
        # Autopilot Channels (Gudtree, Trading, Trending): 100% Autonomous (NO CHAT MESSAGES)
        print(f"🤖 Fetching best viral candidates from DB pool for [{display_name}]...")
        pool = db.get_unprocessed_hunted_reels(limit=count * 3)
        for sc, cr, vw in pool:
            if sc not in seen_shortcodes and not db.is_reel_rejected(sc):
                candidates.append((sc, cr, vw))
                seen_shortcodes.add(sc)

    # 3. Continuous Auto-Refill Loop until EXACTLY 'count' (30) Reels are Ready!
    max_refill_attempts = 100
    refill_attempts = 0

    while len(baked) < count and refill_attempts < max_refill_attempts:
        refill_attempts += 1
        
        # If candidate pool exhausted, trigger live hunt to replenish
        if not candidates:
            print(f"🏹 [Auto-Refill] Replenishing candidate pool for [{display_name}] via live hunt...")
            try:
                from core.niche_hunter import hunt_niche_reels
                fresh_hunted = hunt_niche_reels(config, target_count=15, headless=True)
                for item in fresh_hunted:
                    sc = item.get("shortcode")
                    if sc and sc not in seen_shortcodes and not db.is_reel_rejected(sc):
                        candidates.append((sc, "creator", item.get("views_text", "Viral")))
                        seen_shortcodes.add(sc)
            except Exception as e:
                print(f"⚠️ Live hunt error during auto-refill: {e}")
                time.sleep(3)

        if not candidates:
            print(f"⚠️ Unable to find more candidates for {display_name} right now. Pausing 10s...")
            time.sleep(10)
            continue

        shortcode, creator, views_text = candidates.pop(0)
        slot_num = len(baked) + 1

        out_file = os.path.join(queue_dir, f"ready_{slot_num:02d}_{shortcode}.mp4")
        meta_file = os.path.join(queue_dir, f"ready_{slot_num:02d}_{shortcode}.json")

        print(f"\n▶ [{slot_num}/{count}] Processing {shortcode} (by @{creator}, {views_text})...")

        # Download raw video
        temp_dl = os.path.join(queue_dir, f"raw_{shortcode}.mp4")
        cookie_file = os.path.join(BASE_DIR, f"cookies/{channel_id}_cookies.txt")
        if not os.path.exists(cookie_file):
            cookie_file = os.path.join(BASE_DIR, "cookies.txt")

        reel_url = f"https://www.instagram.com/reel/{shortcode}/"
        raw_video = download_reel_video(reel_url, temp_dl, cookie_file=cookie_file)

        if not raw_video or not os.path.exists(raw_video):
            print(f"⚠️ Failed download for {shortcode}. Skipping to next.")
            continue

        try:
            # Step A: AI Analysis (Enforces Hindi & Human Voice)
            ai_data = analyze_reel_for_channel(raw_video, config, creator)

            # Check if rejected by Language or Speech Guard
            if ai_data.get("rejected"):
                rej_reason = ai_data.get("reason", "audio_or_language_guard")
                print(f"🛑 [Gatekeeper Security REJECTED] {shortcode}: {rej_reason}")
                db.mark_reel_rejected(shortcode, rej_reason)
                continue

            hook_pill = ai_data.get("hook_pill", "KEY TAKEAWAY")
            main_title = ai_data.get("main_title", "VIRAL INSIGHT")
            sub_quote = ai_data.get("sub_quote", "")
            
            # Guarantee rich, multi-paragraph, engaging caption "pehle jaisa"
            from core.caption_engine import generate_rich_caption
            caption = ai_data.get("caption", "")
            if not caption or len(caption.splitlines()) <= 3 or len(caption) < 150 or "valuable insights" in caption.lower() or "strategic insights for modern" in caption.lower():
                caption = generate_rich_caption(channel_id, main_title, hook_pill, creator)

            # Step B: Gatekeeper Security Compliance Check (Meta Iron Shield)
            is_safe, reason = is_reel_compliant(main_title, hook_pill, caption)
            if not is_safe:
                print(f"🛑 [Gatekeeper Security REJECTED] {shortcode}: {reason}")
                db.mark_reel_rejected(shortcode, reason)
                continue

            # Step C: GPU FFmpeg Branded Video Rendering
            print(f"🎬 Rendering branded 9:16 video for slot #{slot_num}...")
            rendered_temp, _ = render_channel_video(
                input_video_path=raw_video,
                channel_config=config,
                hook_pill=hook_pill,
                main_title=main_title,
                sub_quote=sub_quote
            )

            shutil.move(rendered_temp, out_file)

            # Step D: Save Metadata
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "shortcode": shortcode,
                    "creator": creator,
                    "title": main_title,
                    "caption": caption,
                    "hook_pill": hook_pill
                }, f, indent=2, ensure_ascii=False)

            baked.append((slot_num, shortcode, creator, main_title))
            print(f"✅ Slot #{slot_num}/{count} Pre-baked successfully: '{main_title.splitlines()[0]}'")

        except Exception as e:
            print(f"❌ Error during rendering slot #{slot_num}: {e}")
        finally:
            if os.path.exists(temp_dl):
                try: os.remove(temp_dl)
                except: pass

    print("\n========================================================")
    print(f"🎯 PRE-BAKING COMPLETE: {len(baked)}/{count} Reels Ready in {queue_dir}")
    print("========================================================\n")
    return baked

def prebake_all_channels(count=30):
    summary = {}
    for ch_id, name, handle in AUTOPILOT_CHANNELS:
        res = prebake_channel_reels(ch_id, count=count)
        summary[name] = len(res)
        time.sleep(3)
    return summary

if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        target_ch = args[0]
        cnt = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30
        prebake_channel_reels(target_ch, count=cnt)
    else:
        prebake_all_channels(count=30)
