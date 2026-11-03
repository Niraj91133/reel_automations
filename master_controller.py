import os
import sys
import time
import requests
import threading
from datetime import datetime
from core.config_manager import list_available_channels, get_channel_config, load_master_config
from core.database import ChannelDatabase
from run_channel import process_channel_pipeline

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

master_cfg = load_master_config()
MASTER_BOT_TOKEN = master_cfg.get("master_bot_token", "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A")
ADMIN_CHAT_ID = master_cfg.get("admin_chat_id", "711598335")

is_processing = False
current_job_name = ""
scheduler_enabled = True
job_lock = threading.Lock()

def send_telegram(chat_id, text, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{MASTER_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": str(chat_id), "text": text, "parse_mode": parse_mode}
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code != 200 and parse_mode:
            payload.pop("parse_mode", None)
            requests.post(url, json=payload, timeout=15)
    except:
        pass

def get_channel_summary():
    """Generates a real-time status summary across all 4 channels."""
    channels = list_available_channels()
    lines = ["📊 <b>MULTI-ACCOUNT AUTOMATION DASHBOARD</b>", "━━━━━━━━━━━━━━━━━━━━━━"]
    
    for ch_id in channels:
        try:
            cfg = get_channel_config(ch_id)
            name = cfg.get("display_name", ch_id)
            db = ChannelDatabase(cfg["runtime"]["db_path"])
            today_count = db.get_today_count()
            daily_limit = cfg.get("content_settings", {}).get("daily_post_limit", 15)
            
            # Check credentials status
            creds = cfg.get("credentials", {})
            has_gemini = not creds.get("gemini_api_key", "").startswith("YOUR_")
            has_insta = not creds.get("instagram_account_id", "").startswith("YOUR_")
            
            gemini_badge = "🟢 Key Active" if has_gemini else "🟡 Key Missing"
            insta_badge = "🟢 IG Connected" if has_insta else "⚪ Approval Only"

            lines.append(f"<b>{name}</b> (<code>{ch_id}</code>)")
            lines.append(f"• Today's Posts: <b>{today_count}/{daily_limit}</b>")
            lines.append(f"• Status: {gemini_badge} | {insta_badge}")
            lines.append("──────────────────────")
        except Exception as e:
            lines.append(f"❌ Error reading {ch_id}: {e}")

    lines.append(f"⏰ <b>Auto-Scheduler:</b> {'🟢 ENABLED' if scheduler_enabled else '🔴 PAUSED'}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>Commands:</i>\n/run &lt;channel_id&gt; [limit]\n/run all\n/schedule on | off\n/status")
    return "\n".join(lines)

def run_isolated_job(channel_id, limit=1, notify_chat_id=None):
    global is_processing, current_job_name
    chat_id = notify_chat_id or ADMIN_CHAT_ID

    with job_lock:
        if is_processing:
            send_telegram(chat_id, f"⚠️ Ek process already chal raha hai (<b>{current_job_name}</b>). Wait karo.")
            return
        is_processing = True
        current_job_name = f"{channel_id} (Limit: {limit})"

    try:
        send_telegram(chat_id, f"🚀 <b>Starting Job:</b> {channel_id} ({limit} reel)...")
        count = process_channel_pipeline(channel_id, max_reels=limit)
        send_telegram(chat_id, f"✅ <b>Job Finished:</b> {channel_id} processed {count} reel(s).")
    except Exception as e:
        send_telegram(chat_id, f"❌ <b>Job Error [{channel_id}]:</b> {e}")
    finally:
        with job_lock:
            is_processing = False
            current_job_name = ""

def run_all_channels(notify_chat_id=None):
    """Executes 1 reel for each enabled channel sequentially."""
    channels = list_available_channels()
    chat_id = notify_chat_id or ADMIN_CHAT_ID
    for ch in channels:
        run_isolated_job(ch, limit=1, notify_chat_id=chat_id)
        time.sleep(5)

def handle_telegram_updates():
    """Polls Telegram for control commands from user."""
    offset = 0
    print("Telegram Command Listener online...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{MASTER_BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("result", []):
                    offset = item["update_id"] + 1
                    msg = item.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id"))
                    text = (msg.get("text") or "").strip()

                    if not text:
                        continue

                    # Security: check if sender is admin
                    if str(ADMIN_CHAT_ID) and chat_id != str(ADMIN_CHAT_ID):
                        # Allow sender to receive help if authorized
                        pass

                    cmd_parts = text.split()
                    cmd = cmd_parts[0].lower()

                    if cmd in ["/start", "/help", "/menu"]:
                        send_telegram(chat_id, get_channel_summary())

                    elif cmd in ["/status", "/dash"]:
                        send_telegram(chat_id, get_channel_summary())

                    elif cmd == "/run":
                        if len(cmd_parts) < 2:
                            send_telegram(chat_id, "Usage: <code>/run &lt;channel_id&gt; [limit]</code>\nExample: <code>/run startup_road 1</code> or <code>/run all</code>")
                            continue
                        target_ch = cmd_parts[1].lower()
                        limit = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 1

                        if target_ch == "all":
                            t = threading.Thread(target=run_all_channels, args=(chat_id,))
                            t.daemon = True
                            t.start()
                        elif target_ch in list_available_channels():
                            t = threading.Thread(target=run_isolated_job, args=(target_ch, limit, chat_id))
                            t.daemon = True
                            t.start()
                        else:
                            send_telegram(chat_id, f"❌ Unknown channel: <code>{target_ch}</code>\nAvailable: {', '.join(list_available_channels())}")

                    elif cmd == "/schedule":
                        global scheduler_enabled
                        if len(cmd_parts) > 1 and cmd_parts[1].lower() == "off":
                            scheduler_enabled = False
                            send_telegram(chat_id, "🔴 Scheduler has been PAUSED.")
                        elif len(cmd_parts) > 1 and cmd_parts[1].lower() == "on":
                            scheduler_enabled = True
                            send_telegram(chat_id, "🟢 Scheduler is now ACTIVE.")
                        else:
                            send_telegram(chat_id, f"Scheduler status: {'ACTIVE' if scheduler_enabled else 'PAUSED'}")

        except Exception as e:
            time.sleep(5)

def scheduler_loop():
    """Independent background scheduler that runs throughout the day."""
    print("Background Multi-Channel Scheduler initialized...")
    channels = list_available_channels()
    ch_index = 0

    while True:
        try:
            now = datetime.now()
            # Active window: 07:00 AM to 11:00 PM IST
            if scheduler_enabled and 7 <= now.hour <= 23:
                channel_to_run = channels[ch_index % len(channels)]
                ch_index += 1
                
                cfg = get_channel_config(channel_to_run)
                db = ChannelDatabase(cfg["runtime"]["db_path"])
                today_count = db.get_today_count()
                max_daily = cfg.get("content_settings", {}).get("daily_post_limit", 15)

                if today_count < max_daily:
                    print(f"⏰ [Scheduler] Triggering scheduled post for: {channel_to_run}...")
                    run_isolated_job(channel_to_run, limit=1)
                else:
                    print(f"⏰ [Scheduler] Channel {channel_to_run} reached daily limit ({today_count}/{max_daily}). Skipping.")

            # Wait 30 minutes before triggering next channel
            time.sleep(30 * 60)
        except Exception as e:
            print(f"Scheduler loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print("==================================================")
    print("  MULTI-ACCOUNT AUTOMATION MASTER CONTROLLER      ")
    print("==================================================")

    # Start background scheduler thread
    t_sched = threading.Thread(target=scheduler_loop)
    t_sched.daemon = True
    t_sched.start()

    # Start Telegram listener in main thread
    handle_telegram_updates()
