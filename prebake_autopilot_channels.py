import os
import sys
import time
import json
import shutil
import glob
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
    ("thestartup_street", "🚀 Startup Road", "@startup_road"),
    ("theloan_road", "💳 The Loan Road", "@the_loan_road"),
    ("trading_road24", "📊 Trading Knowledge", "@trading_road24"),
    ("healthy_diet", "🥗 Gud Tree", "@gudtree_"),
    ("marketing_road24", "📱 Marketing Road 24", "@marketing_road24"),
    ("viral_finds", "🛍️ Trending Road", "@trending_road"),
    ("trading_pulse", "📈 Trading Road", "@trading_road_")
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

    # 0. Clean up / archive any already-processed reels from queue_dir
    arch_dir = os.path.join(queue_dir, "archive")
    os.makedirs(arch_dir, exist_ok=True)
    for vf in glob.glob(os.path.join(queue_dir, "ready_*.mp4")):
        mf = vf.rsplit(".", 1)[0] + ".json"
        if os.path.exists(mf):
            try:
                with open(mf, 'r', encoding='utf-8') as jf:
                    sc = json.load(jf).get("shortcode")
                if sc and db.is_reel_processed(sc):
                    shutil.move(vf, os.path.join(arch_dir, os.path.basename(vf)))
                    shutil.move(mf, os.path.join(arch_dir, os.path.basename(mf)))
            except:
                pass

    # 1. BRUTAL 4-TIER REEL SOURCING PIPELINE (Applies to ALL Channels)
    candidates = []
    approved_codes = set()
    target_pool = max(count * 3, count + 20)

    # TIER 0: GOOGLE SHEET REEL HUB (Top Priority - Direct Sheet Integration)
    try:
        from core.google_sheet_source import get_pending_reels_from_sheet
        sheet_reels = get_pending_reels_from_sheet(channel_id, limit=count * 2)
        for r in sheet_reels:
            sc = r.get("shortcode")
            if sc and sc not in approved_codes and not db.is_reel_processed(sc):
                candidates.append((sc, r.get("creator", "sheet_creator"), f"Sheet:{r.get('source_tab', 'Tab')}"))
                approved_codes.add(sc)
        if sheet_reels:
            print(f"📊 [{display_name}] Loaded {len(candidates)} curated reels directly from Google Sheet!")
    except Exception as e_sheet:
        print(f"Note on Google Sheet fetch for {display_name}: {e_sheet}")

    # TIER 1: Check if Raj approved/shared any reels in DM chat for this channel (Marketing & Startup)
    if len(candidates) < count and channel_id in ("marketing_road24", "thestartup_street"):
        dm_target = config.get("hunting_settings", {}).get("dm_target_chat") or config.get("content_settings", {}).get("dm_target_chat", "im_raaaj_")
        print(f"📥 [Tier 1: Raj DM Check] Checking @{dm_target} chat for [{display_name}]...")
        try:
            from core.niche_hunter import fetch_approved_reels_from_raj
            approved = fetch_approved_reels_from_raj(config, max_count=count)
            if approved:
                for r in approved:
                    sc = r.get("shortcode")
                    if sc and sc not in approved_codes and not db.is_reel_processed(sc):
                        candidates.append((sc, r.get("creator", "approved_creator"), "Raj Approved"))
                        approved_codes.add(sc)
                print(f"🎯 [{display_name}] Raj approved {len(candidates)} reels from chat!")
        except Exception as e:
            print(f"Note on Raj DM fetch for {display_name}: {e}")

    # TIER 2: 10 PM AUTO-FALLBACK: Auto-fill deficit from channel's local hunted_reels DB pool!
    if len(candidates) < target_pool:
        deficit = target_pool - len(candidates)
        print(f"ℹ️ [{display_name} 10 PM Auto-Fallback] Pool: {len(candidates)}/{target_pool}. Pulling up to {deficit} reels from DB hunted pool...")
        pool_candidates = db.get_unprocessed_hunted_reels(limit=deficit * 2)
        for sc, cr, vw in pool_candidates:
            if sc not in approved_codes and not db.is_reel_processed(sc):
                candidates.append((sc, cr, vw))
                approved_codes.add(sc)
            if len(candidates) >= target_pool:
                break

    # TIER 3: LIVE NICHE CREATOR SCOUT (If DB pool runs low)
    if len(candidates) < count:
        needed = count - len(candidates)
        print(f"⚡ [{display_name} Tier 3 Live Scout] Pool has deficit of {needed}. Triggering Live Niche Scout...")
        try:
            from core.full_autopilot import scout_single_viral_reel_for_channel
            scout_attempts = 0
            while len(candidates) < count and scout_attempts < (needed * 2 + 5):
                scout_attempts += 1
                c = scout_single_viral_reel_for_channel(channel_id)
                if c:
                    sc = c.get("shortcode")
                    if sc and sc not in approved_codes and not db.is_reel_processed(sc):
                        candidates.append((sc, c.get("creator", "creator"), c.get("views", "Viral Live Scout")))
                        approved_codes.add(sc)
                        print(f"   + Live Scouted for {display_name}: {sc} (by @{c.get('creator')})")
                time.sleep(1.5)
        except Exception as e:
            print(f"Tier 3 Scout notice for {display_name}: {e}")

    # TIER 4: EMERGENCY ARCHIVE FALLBACK (Guarantees count never drops below target)
    if len(candidates) < count:
        print(f"🚨 [{display_name} Tier 4 Emergency] Borrowing from general viral archive...")
        try:
            import sqlite3
            conn_general = sqlite3.connect("reels_history.db")
            cg = conn_general.cursor()
            cg.execute("SELECT shortcode, creator, views_str FROM scouted_reels ORDER BY scouted_at DESC LIMIT 80")
            for sc, cr, vw in cg.fetchall():
                if sc not in approved_codes and not db.is_reel_processed(sc):
                    candidates.append((sc, cr, vw or "Viral Archive"))
                    approved_codes.add(sc)
                if len(candidates) >= count:
                    break
            conn_general.close()
        except Exception as e:
            print(f"Tier 4 Emergency notice: {e}")

    print(f"🔒 [FINAL GUARANTEE] {len(candidates)} Candidates Queued for {display_name} (Target: {count} Baked)!")

    # Identify which slots (1..count) are already filled with unposted videos
    existing_slots = {}
    for f in glob.glob(os.path.join(queue_dir, "ready_*.mp4")):
        b = os.path.basename(f)
        parts = b.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            existing_slots[int(parts[1])] = f

    missing_slots = [s for s in range(1, count + 1) if s not in existing_slots]
    baked = []
    print(f"📦 [{display_name}] {len(existing_slots)}/{count} slots already ready. {len(missing_slots)} slots needed.")
    if not missing_slots:
        print(f"🎉 [{display_name}] All {count} slots are already 100% pre-baked and ready!")
        return [(s, 'ready', 'system', 'Already Baked') for s in existing_slots]

    for shortcode, creator, views_text in candidates:
        if not missing_slots:
            break

        slot_idx = missing_slots[0]
        out_file = os.path.join(queue_dir, f"ready_{slot_idx:02d}_{shortcode}.mp4")
        meta_file = os.path.join(queue_dir, f"ready_{slot_idx:02d}_{shortcode}.json")

        if os.path.exists(out_file) and os.path.getsize(out_file) > 100_000 and os.path.exists(meta_file):
            print(f"Already pre-baked: {out_file}")
            baked.append((slot_idx, shortcode, creator, "Already Baked"))
            missing_slots.pop(0)
            continue

        reel_url = f"https://www.instagram.com/reel/{shortcode}/"
        curr_num = len(baked) + 1
        print(f"\n▶ [{curr_num}/{count}] Pre-baking {shortcode} (by @{creator}, {views_text})...")

        # Download with metadata
        temp_dl = os.path.join(queue_dir, f"raw_{shortcode}.mp4")
        cookie_file = os.path.join(BASE_DIR, f"cookies/{channel_id}_cookies.txt")
        raw_video, dl_meta = download_reel_video(reel_url, temp_dl, return_meta=True, cookie_file=cookie_file)

        if not raw_video or not os.path.exists(raw_video):
            print(f"⚠️ Failed download for {shortcode}. Trying next candidate.")
            continue

        # 🎯 BALANCED COMMENT ENGAGEMENT & AUTO-DM GUARD
        dl_comments = dl_meta.get("comment_count", 0) or 0
        dl_views = dl_meta.get("view_count", 0) or dl_meta.get("play_count", 0) or 0
        dl_desc = dl_meta.get("description", "") or ""
        dl_title = dl_meta.get("title", "") or ""
        dl_cta_present = any(sig in dl_desc.lower() for sig in [
            "comment", "dm", "link in bio", "bhejo", "comment karo",
            "type ", "drop a", "share karunga", "link dunga", "list chahiye",
            "pdf chahiye", "guide", "strategy", "free", "setup", "rules", "ebook"
        ])

        # Reject reels only if engagement is truly near-zero (< 5 comments) AND not viral (< 25K views) AND lacks comment CTA
        if (0 < dl_comments < 5) and (dl_views < 25000) and not dl_cta_present:
            print(f"🛑 [Comment Guard REJECTED] Reel {shortcode} has only {dl_comments} comments and lacks comment CTA. Discarding...")
            try:
                if os.path.exists(raw_video):
                    os.remove(raw_video)
            except:
                pass
            continue

        try:
            # AI synthesis with original context
            ai_data = analyze_reel_for_channel(
                raw_video,
                config,
                creator,
                original_description=dl_desc,
                original_title=dl_title
            )
            if ai_data.get("rejected"):
                print(f"🛑 [AI Filter Rejected] Reel {shortcode}: {ai_data.get('reason')}. Trying next candidate...")
                continue

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

            baked.append((slot_idx, shortcode, creator, main_title))
            print(f"✅ [{curr_num}/{count}] Successfully pre-baked: {main_title} -> {out_file}")
            missing_slots.pop(0)

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

