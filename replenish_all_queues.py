import os
import sys
import glob
import json
import time
import shutil

sys.path.insert(0, 'reel_automations-main')

from core.config_manager import get_channel_config
from core.database import ChannelDatabase
from core.ai_service import analyze_reel_for_channel
from core.video_engine import render_channel_video
from core.compliance_guard import is_reel_compliant
from scraper import download_reel_video

CHANNELS_TO_REPLENISH = [
    {
        "channel_id": "healthy_diet",
        "name": "Healthy Diet",
        "cookie_file": "reel_automations-main/cookies/healthy_diet_cookies.txt",
        "target_buffer": 5
    },
    {
        "channel_id": "viral_finds",
        "name": "Viral Finds",
        "cookie_file": "reel_automations-main/cookies/viral_finds_cookies.txt",
        "target_buffer": 5
    },
    {
        "channel_id": "trading_pulse",
        "name": "Trading Pulse",
        "cookie_file": "reel_automations-main/cookies/trading_pulse_cookies.txt",
        "target_buffer": 5
    },
    {
        "channel_id": "startup_road",
        "name": "Startup Road",
        "cookie_file": "reel_automations-main/cookies/startup_road_cookies.txt",
        "target_buffer": 5
    },
    {
        "channel_id": "trading_road24",
        "name": "Trading Road 24",
        "cookie_file": "reel_automations-main/cookies/trading_road24_cookies.txt",
        "target_buffer": 5
    },
    {
        "channel_id": "the_loan_road",
        "name": "The Loan Road",
        "cookie_file": "reel_automations-main/cookies/the_loan_road_cookies.txt",
        "target_buffer": 5
    }
]

def replenish_channel_queue(ch_info):
    cid = ch_info["channel_id"]
    name = ch_info["name"]
    cfile = ch_info["cookie_file"]
    target_buf = ch_info["target_buffer"]
    
    cfg = get_channel_config(cid)
    db = ChannelDatabase(cfg["runtime"]["db_path"])
    q_dir = os.path.join(cfg["runtime"]["workspace_dir"], "tomorrow_reels")
    os.makedirs(q_dir, exist_ok=True)
    
    # 1. Inspect existing queue
    existing_meta = glob.glob(os.path.join(q_dir, "ready_*.json"))
    unprocessed_in_queue = []
    used_slots = set()
    
    for mf in existing_meta:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            sc = data.get("shortcode")
            base = os.path.basename(mf)
            # Parse slot number e.g. ready_13_...
            parts = base.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                used_slots.add(int(parts[1]))
                
            if sc and not db.is_reel_processed(sc):
                unprocessed_in_queue.append((sc, mf))
        except:
            pass
            
    today_posted = db.get_today_count()
    print(f"\n[{name}] Posted today: {today_posted}. Unprocessed ready in queue: {len(unprocessed_in_queue)}.")
    
    needed = target_buf - len(unprocessed_in_queue)
    if needed <= 0:
        print(f"[{name}] Queue is well-stocked ({len(unprocessed_in_queue)} ready). No need to bake now.")
        return 0
        
    print(f"[{name}] Replenishing {needed} fresh reels...")
    
    # Fetch candidates from DB pool
    candidates = db.get_unprocessed_hunted_reels(limit=needed * 4)
    if not candidates:
        print(f"[{name}] No unprocessed candidates found in DB pool!")
        return 0
        
    baked_count = 0
    next_slot = max(used_slots | {today_posted}) + 1
    
    for sc, cr, vw in candidates:
        if baked_count >= needed:
            break
            
        # Verify candidate not already processed
        if db.is_reel_processed(sc):
            continue
            
        print(f"[{name}] Baking candidate {sc} (Slot #{next_slot})...")
        temp_dl = os.path.join(q_dir, f"temp_dl_{sc}.mp4")
        reel_url = f"https://www.instagram.com/reel/{sc}/"
        
        raw = download_reel_video(reel_url, temp_dl, cookie_file=cfile)
        if not raw or not os.path.exists(raw):
            print(f"  ❌ Failed to download {sc}, trying next...")
            continue
            
        try:
            ai = analyze_reel_for_channel(raw, cfg, cr or "creator")
            hp = ai.get("hook_pill", "VIRAL INSIGHT")
            title = ai.get("main_title", "MUST WATCH")
            sub = ai.get("sub_quote", "")
            cap = ai.get("caption", "")
            
            # Guarantee rich, multi-paragraph, engaging caption "pehle jaisa"
            from core.caption_engine import generate_rich_caption
            if not cap or len(cap.splitlines()) <= 3 or len(cap) < 150 or "valuable insights" in cap.lower() or "strategic insights for modern" in cap.lower():
                cap = generate_rich_caption(cid, title, hp, cr or "creator")
            
            # Compliance guard
            safe, reason = is_reel_compliant(title, hp, cap)
            if not safe:
                print(f"  🛑 Non-compliant ({reason}), skipping {sc}")
                continue
                
            out_mp4 = os.path.join(q_dir, f"ready_{next_slot:02d}_{sc}.mp4")
            out_json = os.path.join(q_dir, f"ready_{next_slot:02d}_{sc}.json")
            
            rend, jid = render_channel_video(raw, cfg, hp, title, sub)
            shutil.move(rend, out_mp4)
            
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump({
                    "shortcode": sc,
                    "creator": cr or "creator",
                    "title": title,
                    "caption": cap,
                    "hook_pill": hp
                }, f, indent=2)
                
            print(f"  ✅ Successfully baked Slot #{next_slot}: {title}")
            baked_count += 1
            used_slots.add(next_slot)
            next_slot += 1
        except Exception as e:
            print(f"  ❌ Error baking {sc}: {e}")
        finally:
            if os.path.exists(temp_dl):
                try: os.remove(temp_dl)
                except: pass
                
    return baked_count

if __name__ == "__main__":
    print("=== STARTING MULTI-CHANNEL QUEUE REPLENISHMENT ===")
    total_baked = 0
    for ch in CHANNELS_TO_REPLENISH:
        total_baked += replenish_channel_queue(ch)
    print(f"\n🎉 ALL QUEUES REPLENISHED! Total freshly baked: {total_baked}")

