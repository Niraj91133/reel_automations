import os
import sys
import time
import requests
import threading
from datetime import datetime

# Import pipelines
from run_dm_automation import run_chat_automation
from run_politics_automation import run_politics_daily_automation

sys.stdout.reconfigure(encoding='utf-8')

# Bot 1: Startup Bot
STARTUP_BOT_TOKEN = "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A"
STARTUP_CHAT_ID = "711598335"

# Bot 2: Politics Bot
POLITICS_BOT_TOKEN = "8997893199:AAEUxCeRiVupFV9KElzdsni2kTre7klWteM"
POLITICS_CHAT_ID = "5903254012"

# Track if a job is actively running to prevent overlapping
is_processing = False
lock = threading.Lock()

def send_telegram_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Failed to send Telegram msg: {e}")

def run_job(pipeline_type, token, chat_id, limit=10):
    global is_processing
    with lock:
        if is_processing:
            send_telegram_msg(token, chat_id, "⚠️ Ek process pehle se chal rha hai! Kripya thoda wait karein.")
            return
        is_processing = True

    try:
        if pipeline_type == "startup":
            send_telegram_msg(token, chat_id, f"🚀 <b>STARTUP Automation Triggered!</b>\nInstagram DM se up to {limit} reels extract karke video banana start kar rha hu...\n⏱️ Thoda time lagega (Rendering + AI), wait karein!")
            run_chat_automation(max_reels=limit)
            send_telegram_msg(token, chat_id, "✅ <b>Startup Reels Batch Finished & Delivered!</b>")

        elif pipeline_type == "politics":
            send_telegram_msg(token, chat_id, f"🇮🇳 <b>POLITICS Automation Triggered!</b>\n@baatleaderki chat se up to {limit} reels extract karke Bhagwa template videos banana start ho gaya hai...\n⏱️ Rendering chal rahi hai, wait karein!")
            count = run_politics_daily_automation(max_reels=limit, target_chat_id=chat_id)
            if count and count > 0:
                send_telegram_msg(token, chat_id, f"✅ <b>Politics Reels Batch Finished!</b> {count} videos delivered!")

        elif pipeline_type == "all":
            send_telegram_msg(token, chat_id, f"⚡ <b>ALL BATCH Triggered!</b>\nPehle Startup fir Politics ke reels process honge...")
            run_chat_automation(max_reels=limit)
            count = run_politics_daily_automation(max_reels=limit, target_chat_id=chat_id)
            send_telegram_msg(token, chat_id, "🎉 <b>Both Batches Delivered Successfully!</b>")

    except Exception as e:
        print(f"Error in job {pipeline_type}: {e}")
        send_telegram_msg(token, chat_id, f"❌ Error during processing: {str(e)}")
    finally:
        with lock:
            is_processing = False

def poll_bot(token, bot_name, default_type):
    offset = None
    print(f"🤖 Listening for commands on {bot_name}...")
    
    # Send online message with keyboard instructions
    welcome = (
        f"🤖 <b>{bot_name} Automation Controller Online!</b>\n\n"
        f"Jab bhi aapka man ho, niche diye gaye command ya text bhejein:\n"
        f"👉 <code>/run</code> ya <code>make</code> ➔ 10 reels banakar bhej dega\n"
        f"👉 <code>/startup</code> ➔ Startup videos banayega\n"
        f"👉 <code>/politics</code> ➔ Politics videos banayega\n"
        f"👉 <code>/all</code> ➔ Dono categories banayega"
    )
    # Target chat
    target_chat = STARTUP_CHAT_ID if default_type == "startup" else POLITICS_CHAT_ID
    send_telegram_msg(token, target_chat, welcome)

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {"timeout": 25}
            if offset:
                params["offset"] = offset

            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    chat = msg.get("chat", {})
                    chat_id = str(chat.get("id"))
                    text = (msg.get("text") or "").strip().lower()

                    if not text:
                        continue

                    print(f"[{bot_name}] Received message: '{text}' from chat {chat_id}")

                    # Determine command
                    pipeline = None
                    limit = 10

                    # Check custom number in command e.g. "make 5" or "/run 10"
                    parts = text.split()
                    raw_cmd = parts[0]
                    # Strip @botname if user sent /politics@my_reel_news_bot
                    cmd = raw_cmd.split("@")[0]
                    if len(parts) > 1 and parts[1].isdigit():
                        limit = int(parts[1])

                    if cmd in ["/run", "run", "make", "banao", "start", "/start", "create", "generate"]:
                        pipeline = default_type
                    elif cmd in ["/politics", "politics", "bharat"]:
                        pipeline = "politics"
                    elif cmd in ["/startup", "startup"]:
                        pipeline = "startup"
                    elif cmd in ["/all", "all", "dono"]:
                        pipeline = "all"
                    elif cmd in ["/help", "help", "hi", "hello"]:
                        help_text = (
                            f"👋 <b>Automation Bot Help:</b>\n\n"
                            f"Bas ye likh kar bhejiye:\n"
                            f"• <b>/run</b> ➔ 10 videos banakar deliver karega\n"
                            f"• <b>run 5</b> ➔ 5 videos banayega\n"
                            f"• <b>/politics</b> ➔ Politics videos banayega\n"
                            f"• <b>/startup</b> ➔ Startup videos banayega\n"
                            f"• <b>/all</b> ➔ Dono channels process karega"
                        )
                        send_telegram_msg(token, chat_id, help_text)
                        continue

                    if pipeline:
                        # Launch job in background thread so Telegram doesn't freeze or timeout
                        t = threading.Thread(target=run_job, args=(pipeline, token, chat_id, limit), daemon=True)
                        t.start()

            time.sleep(1)
        except Exception as e:
            # print("Polling error:", e)
            time.sleep(3)

if __name__ == '__main__':
    print("==================================================")
    print("    TELEGRAM COMMAND TRIGGER CONTROLLER           ")
    print("==================================================")
    
    # Start thread for Startup Bot listener
    t1 = threading.Thread(target=poll_bot, args=(STARTUP_BOT_TOKEN, "Startup Bot (@my_reel_auto_bot)", "startup"), daemon=True)
    t1.start()

    # Start thread for Politics Bot listener
    t2 = threading.Thread(target=poll_bot, args=(POLITICS_BOT_TOKEN, "Politics Bot (@my_reel_news_bot)", "politics"), daemon=True)
    t2.start()

    print("\n✅ Dono Telegram bots ab active hain aur aapke messages ka wait kar rahe hain!")
    print("Aap Telegram par '/run' ya 'make' likh kar kabhi bhi trigger kar sakte hain.\n")

    # Keep main alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping controller...")
