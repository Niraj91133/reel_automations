import os
import sys
import time
import requests
import threading
from datetime import datetime, timedelta

# Import startup pipeline and Instagram publisher
from run_dm_automation import run_chat_automation
from instagram_publisher import INSTAGRAM_ACCOUNT_ID, PAGE_ACCESS_TOKEN, BASE_URL

# Line buffering ensures logs flush immediately to disk/pipe
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

# Startup Road Bot Credentials
STARTUP_BOT_TOKEN = os.environ.get("STARTUP_BOT_TOKEN", "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A")
STARTUP_CHAT_ID = os.environ.get("STARTUP_CHAT_ID", "711598335")

# Track if a job is actively running to prevent overlapping
is_processing = False
current_job_name = ""
lock = threading.Lock()

# 30-Posts Schedule State
SCHEDULER_ENABLED = True
DAILY_TARGET = 30
START_HOUR = 6    # 06:00 AM IST
END_HOUR = 22     # 10:00 PM IST
INTERVAL_MINUTES = 32  # 16 hours / 30 reels = ~32 mins
today_date_str = ""
today_posts_count = 0
next_scheduled_run = None

def send_telegram_msg(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return True
        else:
            print(f"Telegram msg status {r.status_code}: {r.text}", flush=True)
            if r.status_code == 400:
                payload.pop("parse_mode", None)
                r2 = requests.post(url, json=payload, timeout=15)
                return r2.status_code == 200
            return False
    except Exception as e:
        print(f"Failed to send Telegram msg: {e}", flush=True)
        return False

def get_instagram_stats():
    """Fetches real-time follower count and media count for @startup_road."""
    try:
        url = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}?fields=username,name,followers_count,media_count&access_token={PAGE_ACCESS_TOKEN}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error fetching IG stats: {e}", flush=True)
    return None

def run_job(token, chat_id, limit=1, is_scheduled=False):
    global is_processing, current_job_name, today_posts_count
    with lock:
        if is_processing:
            send_telegram_msg(token, chat_id, f"⚠️ <b>Ek task pehle se chal rha hai ({current_job_name})!</b>\nKripya thoda wait karein ya <code>/status</code> check karein.")
            return
        is_processing = True
        current_job_name = f"STARTUP ROAD ({limit} reels)"

    def notify(msg):
        print(f"[STARTUP ROAD] {msg}", flush=True)
        send_telegram_msg(token, chat_id, msg)

    try:
        if is_scheduled:
            notify(
                f"⏰ <b>AUTO-PILOT SLOT TRIGGERED! [Post #{today_posts_count + 1}/{DAILY_TARGET}]</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 1 Fresh Reel (@im_raaaj_ ➔ @startup_road)\n"
                f"Live status yahan update hoga 👇"
            )
        else:
            notify(
                f"🚀 <b>MANUAL BATCH TRIGGERED!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 Target: up to {limit} fresh reels (from @im_raaaj_)\n"
                f"📱 Destination: Instagram <b>@startup_road</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Har step ka live status yahan update hoga 👇"
            )

        count = run_chat_automation(max_reels=limit, target_chat_id=STARTUP_CHAT_ID, notify_callback=notify)
        
        if count > 0:
            today_posts_count += count

        notify(
            f"🏆 <b>COMPLETED!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Reels Published This Run: <b>{count}</b>\n"
            f"• Today's Total Progress: <b>{today_posts_count}/{DAILY_TARGET}</b> reels\n"
            f"Instagram @startup_road par posts live ho chuki hain! 🚀"
        )
    except Exception as e:
        print(f"Error in job: {e}", flush=True)
        send_telegram_msg(token, chat_id, f"❌ Error during processing: {str(e)}")
    finally:
        with lock:
            is_processing = False
            current_job_name = ""

def auto_30_posts_scheduler():
    """
    Schedules 30 posts evenly between 6:00 AM and 10:00 PM IST (every ~32 minutes).
    """
    global today_date_str, today_posts_count, next_scheduled_run
    print(f"⏰ [SCHEDULER] 30-Posts Schedule active! (6:00 AM to 10:00 PM IST, every {INTERVAL_MINUTES} mins)", flush=True)
    
    last_run_time = datetime.now()
    next_scheduled_run = last_run_time + timedelta(minutes=INTERVAL_MINUTES)

    while True:
        try:
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")

            # Reset daily counter at midnight
            if today_date_str != today:
                today_date_str = today
                today_posts_count = 0
                last_run_time = None
                print(f"🔄 Date reset to {today}. Daily counter reset to 0/{DAILY_TARGET}.", flush=True)

            # Check if within window (06:00 AM to 10:00 PM)
            in_window = (START_HOUR <= now.hour < END_HOUR) or (now.hour == END_HOUR and now.minute == 0)

            if SCHEDULER_ENABLED and in_window and today_posts_count < DAILY_TARGET:
                should_run = False
                if last_run_time is None:
                    should_run = True
                elif (now - last_run_time).total_seconds() >= (INTERVAL_MINUTES * 60):
                    should_run = True

                if should_run and not is_processing:
                    last_run_time = now
                    next_scheduled_run = now + timedelta(minutes=INTERVAL_MINUTES)
                    print(f"\n⏰ [SCHEDULER] Triggering scheduled post #{today_posts_count + 1}/{DAILY_TARGET} at {now.strftime('%I:%M:%S %p')}...", flush=True)
                    t = threading.Thread(
                        target=run_job,
                        args=(STARTUP_BOT_TOKEN, STARTUP_CHAT_ID, 1, True),
                        daemon=True
                    )
                    t.start()
            elif not in_window:
                # Outside window (after 10 PM, before 6 AM)
                next_morning = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
                if now.hour >= END_HOUR:
                    next_morning += timedelta(days=1)
                next_scheduled_run = next_morning

        except Exception as e:
            print(f"Error in scheduler loop: {e}", flush=True)

        time.sleep(30)

def poll_bot(token, bot_name):
    global SCHEDULER_ENABLED
    bot_start_time = time.time()
    offset = None
    print(f"🤖 Listening for commands on {bot_name}...", flush=True)
    
    welcome = (
        f"🤖 <b>Startup Road 24/7 Controller Active!</b>\n\n"
        f"📱 <b>Target:</b> Instagram @startup_road\n"
        f"⏰ <b>Auto-Schedule:</b> 30 Posts/Day (6:00 AM - 10:00 PM, har ~32 mins)\n\n"
        f"<b>Available Commands:</b>\n"
        f"👉 <code>/run 5</code> ➔ Abhi turant 5 reels publish karega\n"
        f"👉 <code>/status</code> ➔ Check daily progress (e.g. 12/30) & next run\n"
        f"👉 <code>/account</code> ➔ Live @startup_road stats\n"
        f"👉 <code>/pause</code> ➔ Auto-scheduler ko pause karein\n"
        f"👉 <code>/resume</code> ➔ Auto-scheduler ko resume karein\n"
        f"👉 <code>/help</code> ➔ Show full guide"
    )
    send_telegram_msg(token, STARTUP_CHAT_ID, welcome)

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

                    msg_date = msg.get("date", 0)
                    if msg_date and msg_date < (bot_start_time - 300):
                        continue

                    if not text:
                        continue

                    print(f"[{bot_name}] Received message: '{text}' from chat {chat_id}", flush=True)

                    # Status / Schedule
                    if text in ["/status", "status", "/schedule", "schedule", "/ping", "ping"]:
                        status_str = "🟡 PROCESSING" if is_processing else "🟢 IDLE (Ready)"
                        sched_str = "🟢 ACTIVE (30 posts/day)" if SCHEDULER_ENABLED else "🔴 PAUSED"
                        next_str = next_scheduled_run.strftime('%I:%M %p') if next_scheduled_run else "Pending"
                        now_dt = datetime.now()

                        send_telegram_msg(
                            token,
                            chat_id,
                            f"🤖 <b>Startup Road Bot Status:</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"• <b>Status:</b> {status_str}\n"
                            f"• <b>Auto-Schedule:</b> {sched_str}\n"
                            f"• 📊 <b>Today's Progress:</b> <b>{today_posts_count} / {DAILY_TARGET}</b> Reels\n"
                            f"• ⏰ <b>Next Auto-Run:</b> {next_str}\n"
                            f"• ⏱️ <b>Window:</b> 06:00 AM - 10:00 PM IST (Har 32 min)\n"
                            f"• <b>Active Task:</b> {current_job_name or 'None'}"
                        )
                        continue

                    # Pause/Resume
                    if text in ["/pause", "pause", "stop"]:
                        SCHEDULER_ENABLED = False
                        send_telegram_msg(token, chat_id, "⏸️ <b>Auto-scheduler PAUSED!</b>\nAb automatically posts nahi honge. Resume karne ke liye <code>/resume</code> bhejein.")
                        continue
                    if text in ["/resume", "resume", "chalu"]:
                        SCHEDULER_ENABLED = True
                        send_telegram_msg(token, chat_id, "▶️ <b>Auto-scheduler RESUMED!</b>\n30 posts schedule ab wapas active hai.")
                        continue

                    # Account stats
                    if text in ["/account", "account", "/stats", "stats", "/followers", "followers"]:
                        stats = get_instagram_stats()
                        if stats:
                            send_telegram_msg(
                                token,
                                chat_id,
                                f"📊 <b>Instagram @startup_road Stats:</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"• <b>Handle:</b> @{stats.get('username')}\n"
                                f"• <b>Name:</b> {stats.get('name')}\n"
                                f"• <b>Followers:</b> {stats.get('followers_count'):,}\n"
                                f"• <b>Total Posts:</b> {stats.get('media_count')}\n"
                                f"• <b>Meta API:</b> 🟢 100% Connected"
                            )
                        else:
                            send_telegram_msg(token, chat_id, "⚠️ Could not fetch Instagram stats from Meta API.")
                        continue

                    # Run commands
                    parts = text.split()
                    raw_cmd = parts[0]
                    cmd = raw_cmd.split("@")[0]
                    limit = 2

                    if len(parts) > 1 and parts[1].isdigit():
                        limit = int(parts[1])

                    # Scout command: Finds trending reels and sends to @im_raaaj_ DM for review
                    if cmd in ["/scout", "scout", "/find", "find", "khojo", "/khojo"]:
                        from viral_reel_scout import scout_and_send_reels
                        def notify_scout(m):
                            send_telegram_msg(token, chat_id, m)
                        send_telegram_msg(token, chat_id, f"🔍 <i>Viral Scout shuru ho rha hai... Top creators se {limit} viral reels dhoondh kar @im_raaaj_ DM me bhej rha hu...</i>")
                        t_scout = threading.Thread(target=scout_and_send_reels, args=(limit, notify_scout), daemon=True)
                        t_scout.start()
                        continue

                    if cmd in ["/run", "run", "make", "banao", "start", "/start", "create", "generate"]:
                        send_telegram_msg(token, chat_id, f"⚡ <i>Command received! Starting {limit} reels for @startup_road...</i>")
                        t = threading.Thread(target=run_job, args=(token, chat_id, limit, False), daemon=True)
                        t.start()
                    elif cmd in ["/help", "help", "hi", "hello"]:
                        help_text = (
                            f"👋 <b>Startup Road Automation Commands:</b>\n\n"
                            f"• <b>/scout 5</b> ➔ Top creators se viral reels dhoondh kar @im_raaaj_ ke DM me bhejega review ke liye\n"
                            f"• <b>/status</b> ➔ Check today's {today_posts_count}/{DAILY_TARGET} count & next run time\n"
                            f"• <b>/run 5</b> ➔ Turant 5 reels process aur publish karega\n"
                            f"• <b>/account</b> ➔ Live follower count aur stats dekhein\n"
                            f"• <b>/pause</b> ➔ Schedule ko pause karein\n"
                            f"• <b>/resume</b> ➔ Schedule ko wapas shuru karein"
                        )
                        send_telegram_msg(token, chat_id, help_text)

            time.sleep(1)
        except Exception as e:
            time.sleep(3)

if __name__ == '__main__':
    print("==================================================", flush=True)
    print("    STARTUP ROAD 30-POSTS/DAY CONTROLLER          ", flush=True)
    print("==================================================", flush=True)
    
    # 1. Start thread for Startup Bot listener
    t1 = threading.Thread(target=poll_bot, args=(STARTUP_BOT_TOKEN, "Startup Bot (@my_reel_auto_bot)"), daemon=True)
    t1.start()

    # 2. Start thread for 30-Posts Schedule (6:00 AM to 10:00 PM)
    t_sched = threading.Thread(target=auto_30_posts_scheduler, daemon=True)
    t_sched.start()

    print("\n✅ Startup Road 30-Posts/Day Controller ACTIVE!", flush=True)
    print("⏰ Schedule: Har roz 6:00 AM se 10:00 PM tak har 32 minute me 1 reel post hogi.", flush=True)
    print("Aap Telegram par kabhi bhi '/status', '/run 5' ya '/account' bhej sakte hain.\n", flush=True)

    # Keep main alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping controller...", flush=True)
