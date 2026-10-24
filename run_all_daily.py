import os
import sys
import time
from datetime import datetime
import requests

from run_dm_automation import run_chat_automation
from run_politics_automation import run_politics_daily_automation
from telegram_controller import STARTUP_BOT_TOKEN, STARTUP_CHAT_ID, POLITICS_BOT_TOKEN, POLITICS_CHAT_ID, send_telegram_msg

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def run_daily_mega_batch(limit=10):
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%d-%b-%Y")
    
    print(f"==================================================", flush=True)
    print(f"   10:00 PM SCHEDULED MEGA BATCH: {day_name} ({date_str})", flush=True)
    print(f"==================================================", flush=True)
    
    send_telegram_msg(
        STARTUP_BOT_TOKEN,
        STARTUP_CHAT_ID,
        f"🌙 <b>DAILY 10:00 PM AUTOMATION TRIGGERED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Date:</b> {date_str} ({day_name})\n"
        f"⏰ Raat ke 10:00 baj chuke hain! Daily 10 reels automation shuru ho rha hai...\n"
        f"1️⃣ <b>Startup:</b> 10 reels (@im_raaaj_)\n"
        f"2️⃣ <b>Politics:</b> 10 reels (@baatleaderki)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Videos deliver hona shuru ho jayengi 👇"
    )
    
    # Live callback
    def notify(msg):
        print(f"[DAILY 10PM] {msg}", flush=True)
        send_telegram_msg(STARTUP_BOT_TOKEN, STARTUP_CHAT_ID, msg)

    # 1. Startup Batch
    print("\n▶️ Starting Startup Batch...", flush=True)
    c1 = 0
    try:
        c1 = run_chat_automation(max_reels=limit, target_chat_id=STARTUP_CHAT_ID, notify_callback=notify)
    except Exception as e:
        print("Startup batch error:", e, flush=True)
        notify(f"⚠️ Startup batch error: {e}")

    time.sleep(3)

    # 2. Politics Batch
    print("\n▶️ Starting Politics Batch...", flush=True)
    c2 = 0
    try:
        c2 = run_politics_daily_automation(max_reels=limit, target_chat_id=POLITICS_CHAT_ID, notify_callback=notify)
    except Exception as e:
        print("Politics batch error:", e, flush=True)
        notify(f"⚠️ Politics batch error: {e}")

    summary = (
        f"🏆 <b>DAILY 10:00 PM BATCH COMPLETED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Startup Videos Delivered: <b>{c1}</b>\n"
        f"• Politics Videos Delivered: <b>{c2}</b>\n"
        f"Dono Telegram channels par videos deliver ho chuki hain! 🚀"
    )
    notify(summary)
    print("\n" + summary, flush=True)

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10
    run_daily_mega_batch(limit=limit)
