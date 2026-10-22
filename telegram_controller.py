import os
import sys
import time
import requests
import threading
from datetime import datetime

# Import pipelines
from run_dm_automation import run_chat_automation
from run_politics_automation import run_politics_daily_automation

# Line buffering ensures logs flush immediately to disk/pipe
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# Bot 1: Startup Bot
STARTUP_BOT_TOKEN = "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A"
STARTUP_CHAT_ID = "711598335"

# Bot 2: Politics Bot
POLITICS_BOT_TOKEN = "8997893199:AAEUxCeRiVupFV9KElzdsni2kTre7klWteM"
POLITICS_CHAT_ID = "5903254012"

# Track if a job is actively running to prevent overlapping
is_processing = False
current_job_name = ""
lock = threading.Lock()

def send_telegram_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram msg: {e}", flush=True)
        return False

def run_job(pipeline_type, token, chat_id, limit=2):
    global is_processing, current_job_name
    with lock:
        if is_processing:
            send_telegram_msg(token, chat_id, f"⚠️ <b>Ek task pehle se chal rha hai ({current_job_name})!</b>\nKripya thoda wait karein ya <code>/status</code> check karein.")
            return
        is_processing = True
        current_job_name = f"{pipeline_type.upper()} ({limit} reels)"

    # Live callback function to notify user of every step
    def notify(msg):
        print(f"[{pipeline_type.upper()}] {msg}", flush=True)
        send_telegram_msg(token, chat_id, msg)

    try:
        if pipeline_type == "startup":
            notify(f"🚀 <b>STARTUP BATCH TRIGGERED!</b>\nTarget: up to {limit} reels (@im_raaaj_)\nHar step ka live status yahan milega 👇")
            count = run_chat_automation(max_reels=limit, target_chat_id=STARTUP_CHAT_ID, notify_callback=notify)
            notify(f"🎉 <b>Startup Reels Batch Finished!</b> {count} videos delivered successfully!")

        elif pipeline_type == "politics":
            notify(f"🇮🇳 <b>POLITICS BATCH TRIGGERED!</b>\nTarget: up to {limit} reels (@baatleaderki)\nHar step ka live status yahan milega 👇")
            count = run_politics_daily_automation(max_reels=limit, target_chat_id=POLITICS_CHAT_ID, notify_callback=notify)
            notify(f"🎉 <b>Politics Reels Batch Finished!</b> {count} videos delivered successfully!")

        elif pipeline_type == "all":
            notify(
                f"⚡ <b>MEGA BATCH TRIGGERED!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"1️⃣ <b>Startup:</b> {limit} reels (@im_raaaj_ se) ➔ Startup Bot\n"
                f"2️⃣ <b>Politics:</b> {limit} reels (@baatleaderki se) ➔ Politics Bot\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ Live progress yahan update hogi, please wait..."
            )
            
            # Step 1: Startup batch
            notify("▶️ <b>[Step 1/2] Startup Reels processing shuru ho rhi hai...</b>")
            c1 = 0
            try:
                c1 = run_chat_automation(max_reels=limit, target_chat_id=STARTUP_CHAT_ID, notify_callback=notify)
                notify(f"✅ <b>Startup Complete:</b> {c1} reels delivered!")
            except Exception as e_start:
                print("Error in startup batch:", e_start, flush=True)
                notify(f"⚠️ Startup error: {e_start}")

            time.sleep(3)

            # Step 2: Politics batch
            notify("▶️ <b>[Step 2/2] Politics Reels (@baatleaderki) processing shuru ho rhi hai...</b>")
            c2 = 0
            try:
                c2 = run_politics_daily_automation(max_reels=limit, target_chat_id=POLITICS_CHAT_ID, notify_callback=notify)
                notify(f"✅ <b>Politics Complete:</b> {c2} reels delivered!")
            except Exception as e_pol:
                print("Error in politics batch:", e_pol, flush=True)
                notify(f"⚠️ Politics error: {e_pol}")
            
            notify(
                f"🏆 <b>MEGA BATCH COMPLETED!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• Startup Videos Delivered: <b>{c1}</b>\n"
                f"• Politics Videos Delivered: <b>{c2}</b>\n"
                f"Dono Telegram channels par videos deliver ho chuki hain! 🚀"
            )

    except Exception as e:
        print(f"Error in job {pipeline_type}: {e}", flush=True)
        send_telegram_msg(token, chat_id, f"❌ Error during processing: {str(e)}")
    finally:
        with lock:
            is_processing = False
            current_job_name = ""

def poll_bot(token, bot_name, default_type):
    offset = None
    print(f"🤖 Listening for commands on {bot_name}...", flush=True)
    
    # Target chat
    target_chat = STARTUP_CHAT_ID if default_type == "startup" else POLITICS_CHAT_ID
    welcome = (
        f"🤖 <b>{bot_name} Active & Listening!</b>\n\n"
        f"Aap jab chahein ye command bhejein:\n"
        f"👉 <code>/all</code> ➔ Startup & Politics dono ke 2-2 fresh reels banayega\n"
        f"👉 <code>/all 5</code> ➔ Dono categories ke 5-5 reels banayega\n"
        f"👉 <code>/run</code> ya <code>make</code> ➔ Current channel ke 2 reels banayega\n"
        f"👉 <code>/run 10</code> ➔ 10 reels banayega\n"
        f"👉 <code>/ping</code> ya <code>/status</code> ➔ Check karega bot active hai ya nahi"
    )
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

                    print(f"[{bot_name}] Received message: '{text}' from chat {chat_id}", flush=True)

                    # Quick ping/status response (0 seconds latency)
                    if text in ["/ping", "ping", "/status", "status"]:
                        status_str = "🟡 PROCESSING" if is_processing else "🟢 IDLE (Ready for work)"
                        send_telegram_msg(
                            token,
                            chat_id,
                            f"🤖 <b>Bot Status:</b> {status_str}\n"
                            f"• Active Task: {current_job_name or 'None'}\n"
                            f"• Time: {datetime.now().strftime('%H:%M:%S')}\n"
                            f"• Send <code>/all</code> to start generating videos!"
                        )
                        continue

                    # Determine command and custom number
                    pipeline = None
                    limit = 2  # Default to 2 for instant execution (user can specify e.g. /all 5 or /run 10)

                    parts = text.split()
                    raw_cmd = parts[0]
                    cmd = raw_cmd.split("@")[0]
                    if len(parts) > 1 and parts[1].isdigit():
                        limit = int(parts[1])

                    if cmd in ["/run", "run", "make", "banao", "start", "/start", "create", "generate"]:
                        pipeline = default_type
                    elif cmd in ["/all", "all", "dono", "/dono", "both", "/both", "mega", "/mega", "startall", "/startall"]:
                        pipeline = "all"
                    elif cmd in ["/politics", "politics", "bharat", "/bharat"]:
                        pipeline = "politics"
                    elif cmd in ["/startup", "startup"]:
                        pipeline = "startup"
                    elif cmd in ["/help", "help", "hi", "hello"]:
                        help_text = (
                            f"👋 <b>Automation Bot Commands:</b>\n\n"
                            f"• <b>/all</b> ➔ Dono categories ek-sath run karega (Startup + Politics) aur dono par video bhejega\n"
                            f"• <b>/all 5</b> ➔ 5 reels each banayega\n"
                            f"• <b>/run</b> ➔ Current category ke reels banayega\n"
                            f"• <b>/politics</b> ➔ Sirf Politics videos banayega\n"
                            f"• <b>/startup</b> ➔ Sirf Startup videos banayega\n"
                            f"• <b>/ping</b> ➔ Bot health check"
                        )
                        send_telegram_msg(token, chat_id, help_text)
                        continue

                    if pipeline:
                        # Immediate confirmation so user sees response instantly
                        send_telegram_msg(token, chat_id, f"⚡ <i>Command '{cmd}' received! Starting pipeline ({limit} reels)...</i>")
                        t = threading.Thread(target=run_job, args=(pipeline, token, chat_id, limit), daemon=True)
                        t.start()

            time.sleep(1)
        except Exception as e:
            # print("Polling error:", e, flush=True)
            time.sleep(3)

if __name__ == '__main__':
    print("==================================================", flush=True)
    print("    TELEGRAM COMMAND TRIGGER CONTROLLER           ", flush=True)
    print("==================================================", flush=True)
    
    # Start thread for Startup Bot listener
    t1 = threading.Thread(target=poll_bot, args=(STARTUP_BOT_TOKEN, "Startup Bot (@my_reel_auto_bot)", "startup"), daemon=True)
    t1.start()

    # Start thread for Politics Bot listener
    t2 = threading.Thread(target=poll_bot, args=(POLITICS_BOT_TOKEN, "Politics Bot (@my_reel_news_bot)", "politics"), daemon=True)
    t2.start()

    print("\n✅ Dono Telegram bots ab active hain aur aapke messages ka wait kar rahe hain!", flush=True)
    print("Aap Telegram par '/all', '/run' ya 'ping' bhej sakte hain.\n", flush=True)

    # Keep main alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping controller...", flush=True)
