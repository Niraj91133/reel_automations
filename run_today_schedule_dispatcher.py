import os
import sys
import time
import glob
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = os.path.abspath('reel_automations-main')
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase
import google.genai as genai

TITLES = {
    1: "START THIS BUSINESS WITH JUST ₹50,000 INVESTMENT",
    2: "ZERO COMPETITION BUSINESS: 200% TO 500% MARGIN",
    3: "GOVERNMENT WANTS YOU TO START THIS BUSINESS",
    4: "SUGARCANE JUICE BUSINESS TRUTH (₹1.5L/MO)",
    5: "PETROL PUMP HACK: START WITHOUT CRORES",
    6: "5 BUSINESS IDEAS TO PRINT MONEY",
    7: "Rs. 700/Kg खरीदो, Rs. 2500/kg बेचो (Makhana Goldmine)",
    8: "WHY NOBODY TALKS ABOUT THE CEMENT BUSINESS",
    9: "₹1.2L PROFIT IN 1 MONTH WITHOUT SELLING PRODUCTS",
    10: "HOW FOUNDERS BUILD SCALABLE EMPIRES",
    11: "BORING BUSINESS HACK: STEEL SCRAP ARBITRAGE",
    12: "4 BUSINESSES THAT NEVER FAIL IN ANY ECONOMY",
    13: "3 HIGH-INCOME SKILLS TO QUIT YOUR 9-TO-5"
}

def generate_slots(start_hour=10, start_min=30, end_hour=21, count=13):
    now = datetime.now()
    start_dt = datetime(now.year, now.month, now.day, start_hour, start_min, 0)
    if start_dt < now + timedelta(minutes=5):
        start_dt = now + timedelta(minutes=5)
    end_dt = datetime(now.year, now.month, now.day, end_hour, 30, 0)
    
    total_secs = (end_dt - start_dt).total_seconds()
    step_secs = total_secs / max(1, count - 1)
    
    slots = []
    for i in range(count):
        slot_dt = start_dt + timedelta(seconds=i * step_secs)
        slots.append({
            "index": i + 1,
            "dt": slot_dt,
            "time_str": slot_dt.strftime("%I:%M %p"),
            "title": TITLES.get(i + 1, f"Startup Playbook #{i+1}")
        })
    return slots

def run_schedule_loop():
    config = get_channel_config("startup_road")
    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))
    db = ChannelDatabase(config["runtime"]["db_path"])

    qdir = 'reel_automations-main/workspaces/startup_road/ready_queue'
    queue_files = sorted(glob.glob(f'{qdir}/*.mp4'))
    
    if not queue_files:
        print("❌ No videos found in ready_queue!")
        return

    slots = generate_slots(start_hour=10, start_min=30, end_hour=21, count=len(queue_files))

    print("========================================================")
    print("  STARTUP ROAD AUTOMATED DAILY DISPATCHER (05 NOV)")
    print("========================================================")
    print(f"Total Videos Queued: {len(queue_files)}")
    print(f"Interval: ~{(slots[1]['dt'] - slots[0]['dt']).total_seconds()/60:.0f} minutes apart")
    print("Schedule Timeline:")
    for s in slots:
        print(f"  [{s['index']:02d}] {s['time_str']} ➔ {s['title']}")
    print("========================================================\n")

    # Send initial schedule roadmap to Telegram
    road_text = [
        "📅 <b>TODAY'S POSTING SCHEDULE (STARTUP ROAD)</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🎯 <b>Total Videos Ready:</b> {len(queue_files)} Reels",
        f"⏰ <b>Timing Gap:</b> Every ~{(slots[1]['dt'] - slots[0]['dt']).total_seconds()/60:.0f} mins (10:30 AM to 09:30 PM)",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]
    for s in slots:
        road_text.append(f"• <b>{s['time_str']}:</b> {s['title']}")
    road_text.append("\n🚀 <i>Har slot time par bot automatically video post karega aur yahan live link aayega!</i>")
    hub.send_message("\n".join(road_text))

    for idx, (vid_path, slot) in enumerate(zip(queue_files, slots)):
        target_time = slot["dt"]
        slot_str = slot["time_str"]
        title = slot["title"]

        now = datetime.now()
        wait_seconds = (target_time - now).total_seconds()

        if wait_seconds > 0:
            print(f"⏳ Waiting {wait_seconds/60:.1f} minutes until {slot_str} for: {title}...")
            time.sleep(wait_seconds)

        print(f"\n🚀 [Triggered {slot_str}] Publishing Reel #{idx+1}: {title}...")

        caption = (
            f"📌 {title} 💸👇\n\n"
            f"The Founder Breakdown:\n"
            f"• High Utility Asset: Essential demand always outperforms speculative trends.\n"
            f"• Unit Economics: Optimized payload-to-expense ratios generate consistent monthly profits.\n"
            f"• Strategic Advantage: Focus on unsexy, boring businesses where competition is lowest.\n\n"
            f"💡 Golden Takeaway: Cash flow is king. Build assets that solve real physical problems.\n\n"
            f"👇 Want the complete step-by-step PDF roadmap & resources?\n"
            f"Comment \"STARTUP\" below and I'll DM you the breakdown instantly! 📩\n\n"
            f"Follow @startup_road for daily founder playbooks & business insights.\n\n"
            f"#StartupRoad #FounderMindset #BusinessIdeas #WealthBuilding #Entrepreneurship #StartupIndia"
        )

        caption_tg = f"🚀 <b>[POSTING LIVE NOW ({slot_str})]</b>\n\n{caption}"
        sent, cdn_url = hub.send_video_with_cdn_url(vid_path, caption_tg)

        if sent and cdn_url:
            pub_res = publisher.publish_reel(
                public_video_url=cdn_url,
                caption=caption,
                first_comment='Comment "STARTUP" and I will DM you the complete PDF case study roadmap!'
            )
            if pub_res and pub_res.get("permalink"):
                link = pub_res["permalink"]
                print(f"🎉 SUCCESS! Reel #{idx+1} LIVE: {link}")
                db.mark_reel_processed(f"pub_{slot_str}", "startup_road", title, link)
                hub.send_message(
                    f"🎉 <b>Reel LIVE on Instagram (@startup_road)!</b>\n\n"
                    f"📌 <b>Title:</b> {title}\n"
                    f"⏰ <b>Scheduled Slot:</b> {slot_str}\n"
                    f"🔗 <b>Watch here:</b> {link}"
                )
            else:
                print(f"❌ Failed to publish to Instagram for Reel #{idx+1}")
        else:
            print(f"❌ Failed to deliver to Telegram CDN for Reel #{idx+1}")

        time.sleep(10)

    print("\n🎉 ALL 13 REELS SUCCESSFULLY POSTED FOR TODAY!")
    hub.send_message("🏆 <b>TODAY'S BATCH FINISHED!</b> All 13 reels have been successfully posted across the day to @startup_road feed! 🚀")

if __name__ == '__main__':
    run_schedule_loop()

