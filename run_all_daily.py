import os
import sys
import time
from datetime import datetime
import requests

from run_dm_automation import run_chat_automation
from telegram_controller import STARTUP_BOT_TOKEN, STARTUP_CHAT_ID, send_telegram_msg

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

def run_daily_startup_batch(limit=5):
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%d-%b-%Y")
    
    print(f"==================================================", flush=True)
    print(f"   STARTUP ROAD BATCH: {day_name} ({date_str})", flush=True)
    print(f"==================================================", flush=True)
    
    send_telegram_msg(
        STARTUP_BOT_TOKEN,
        STARTUP_CHAT_ID,
        f"🌙 <b>STARTUP ROAD AUTOMATION TRIGGERED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Date:</b> {date_str} ({day_name})\n"
        f"🎯 <b>Target:</b> {limit} fresh reels (@im_raaaj_ ➔ @startup_road)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Videos deliver aur auto-publish hona shuru ho jayengi 👇"
    )
    
    def notify(msg):
        print(f"[STARTUP ROAD] {msg}", flush=True)
        send_telegram_msg(STARTUP_BOT_TOKEN, STARTUP_CHAT_ID, msg)

    print("\n▶️ Starting Startup Road Batch...", flush=True)
    c1 = 0
    try:
        c1 = run_chat_automation(max_reels=limit, target_chat_id=STARTUP_CHAT_ID, notify_callback=notify)
    except Exception as e:
        print("Startup batch error:", e, flush=True)
        notify(f"⚠️ Startup batch error: {e}")

    summary = (
        f"🏆 <b>STARTUP ROAD BATCH COMPLETED!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Videos Processed & Published: <b>{c1}</b>\n"
        f"Instagram @startup_road par videos live ho chuki hain! 🚀"
    )
    notify(summary)
    print("\n" + summary, flush=True)

if __name__ == '__main__':
    limit = 5
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        limit = int(sys.argv[1])
    run_daily_startup_batch(limit=limit)
