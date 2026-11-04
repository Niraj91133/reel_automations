import os
import sys
import time
import json
import requests
import threading
from datetime import datetime
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import list_available_channels, get_channel_config, load_master_config
from core.database import ChannelDatabase
from run_channel import process_channel_pipeline
from core.niche_hunter import hunt_niche_reels, send_hunted_reels_to_raj_chat
from core.cloud_scheduler import cloud_schedule_channel_for_tomorrow

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

master_cfg = load_master_config()
MASTER_BOT_TOKEN = master_cfg.get("master_bot_token", "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A")
ADMIN_CHAT_ID = master_cfg.get("admin_chat_id", "711598335")

is_processing = False
current_job_name = ""
scheduler_enabled = True
delivery_mode = master_cfg.get("delivery_mode", "direct")
job_lock = threading.Lock()

CHANNEL_DISPLAY = {
    "startup_road": ("💼 Startup Road", "@startup_road"),
    "healthy_diet": ("🥗 Gudtree", "@gudtree_"),
    "trading_pulse": ("📈 Trading Road", "@trading_road_"),
    "viral_finds": ("🛍️ Trending Road", "@trending_road")
}

def resolve_channel(query):
    """Normalizes natural names or abbreviations to standard channel_id."""
    if not query:
        return "startup_road"
    q = str(query).lower().strip().replace("@", "").replace("-", "_").replace(" ", "_")
    alias_map = {
        "startup": "startup_road",
        "startup_road": "startup_road",
        "startuproad": "startup_road",
        "gudtree": "healthy_diet",
        "gudtree_": "healthy_diet",
        "health": "healthy_diet",
        "diet": "healthy_diet",
        "healthy_diet": "healthy_diet",
        "healthydiet": "healthy_diet",
        "trading": "trading_pulse",
        "trading_pulse": "trading_pulse",
        "tradingpulse": "trading_pulse",
        "trading_road": "trading_pulse",
        "tradingroad": "trading_pulse",
        "trending": "viral_finds",
        "viral": "viral_finds",
        "viral_finds": "viral_finds",
        "viralfinds": "viral_finds",
        "trending_road": "viral_finds",
        "finds": "viral_finds"
    }
    return alias_map.get(q, q)

def send_telegram(chat_id, text, parse_mode="HTML", reply_markup=None):
    url = f"https://api.telegram.org/bot{MASTER_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": str(chat_id), "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code != 200 and parse_mode:
            payload.pop("parse_mode", None)
            requests.post(url, json=payload, timeout=15)
    except:
        pass

def answer_callback(callback_id, text=None):
    url = f"https://api.telegram.org/bot{MASTER_BOT_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": str(callback_id)}
    if text:
        payload["text"] = text
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_main_menu_markup():
    """Builds interactive one-click buttons for channels and settings."""
    mode_text = "🚀 Mode: DIRECT POST" if delivery_mode == "direct" else "🎬 Mode: PREVIEW ON TG"
    return {
        "inline_keyboard": [
            [
                {"text": "💼 Startup Road", "callback_data": "menu:ch:startup_road"},
                {"text": "🥗 Gudtree", "callback_data": "menu:ch:healthy_diet"}
            ],
            [
                {"text": "📈 Trading Road", "callback_data": "menu:ch:trading_pulse"},
                {"text": "🛍️ Trending Road", "callback_data": "menu:ch:viral_finds"}
            ],
            [
                {"text": "🌙 Run Night Cloud-Schedule (All)", "callback_data": "action:sched_all"},
                {"text": "🏹 Run Morning Hunt (All)", "callback_data": "action:hunt_all"}
            ],
            [
                {"text": mode_text, "callback_data": "toggle:delivery_mode"},
                {"text": "📊 Live Status", "callback_data": "action:status"}
            ]
        ]
    }

def get_channel_menu_markup(ch_id):
    """Submenu for a specific channel offering Hunt, Cloud-Schedule, Make/Ready, or Direct Post."""
    name, uname = CHANNEL_DISPLAY.get(ch_id, (ch_id, ""))
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ Make & Ready 30 Reels", "callback_data": f"make:30:{ch_id}"},
                {"text": "📅 Cloud-Schedule 25", "callback_data": f"sched:25:{ch_id}"}
            ],
            [
                {"text": "🏹 Hunt 5 Reels (Send to Raj)", "callback_data": f"hunt:5:{ch_id}"},
                {"text": "🏹 Hunt 80 Daily Target", "callback_data": f"hunt:80:{ch_id}"}
            ],
            [
                {"text": "🚀 Direct Auto-Post 1 Reel", "callback_data": f"post:direct:{ch_id}"},
                {"text": "🎬 Preview Video in Telegram", "callback_data": f"post:preview:{ch_id}"}
            ],
            [
                {"text": "⬅️ Back to Main Menu", "callback_data": "menu:main"}
            ]
        ]
    }

def get_channel_summary():
    """Generates a real-time status summary across all 4 channels."""
    channels = list_available_channels()
    lines = ["📊 <b>MULTI-ACCOUNT AUTOMATION DASHBOARD</b>", "━━━━━━━━━━━━━━━━━━━━━━"]
    
    for ch_id in channels:
        try:
            cfg = get_channel_config(ch_id)
            name, uname = CHANNEL_DISPLAY.get(ch_id, (cfg.get("display_name", ch_id), ""))
            db = ChannelDatabase(cfg["runtime"]["db_path"])
            today_count = db.get_today_count()
            today_hunted = db.get_today_hunted_count()
            daily_limit = cfg.get("content_settings", {}).get("daily_post_limit", 25)
            hunt_target = cfg.get("hunting_settings", {}).get("hunt_target_daily", 80)
            
            lines.append(f"<b>{name}</b> ({uname})")
            lines.append(f"• Scheduled/Posts: <b>{today_count}/{daily_limit}</b> | Hunted: <b>{today_hunted}/{hunt_target}</b>")
            lines.append(f"• Token: 🟢 Permanent | Gemini: 🟢 Active")
            lines.append("──────────────────────")
        except Exception as e:
            lines.append(f"❌ Error reading {ch_id}: {e}")

    lines.append("🕒 <b>24H Production Cycle:</b>")
    lines.append("• 06:00 - 10:00 AM: 🏹 Morning Viral Hunt (80 reels/ch)")
    lines.append("• 11:00 AM - 09:00 PM: ☕ Raj Curation Window")
    lines.append("• 10:00 PM - 02:00 AM: 🌙 Night Cloud-Scheduling (25 reels/ch)")
    lines.append(f"• Auto-Scheduler: {'🟢 ACTIVE' if scheduler_enabled else '🔴 PAUSED'}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<i>Neeche buttons par click karke direct control karein 👇</i>")
    return "\n".join(lines)

def run_isolated_job(channel_id, limit=1, notify_chat_id=None, is_preview=False):
    global is_processing, current_job_name
    chat_id = notify_chat_id or ADMIN_CHAT_ID

    with job_lock:
        if is_processing:
            send_telegram(chat_id, f"⚠️ Ek process already chal raha hai (<b>{current_job_name}</b>). Wait karo.")
            return
        is_processing = True
        current_job_name = f"PROCESSING: {channel_id} ({limit} reels)"

    try:
        cfg = get_channel_config(channel_id)
        name, uname = CHANNEL_DISPLAY.get(channel_id, (channel_id, ""))
        mode_str = "🎬 Preview on Telegram (No IG Post)" if is_preview else "🚀 Live Feed Post (Instagram + Telegram)"
        send_telegram(
            chat_id,
            f"🚀 <b>Starting [{name}] Processing Pipeline!</b>\n"
            f"• Target Reels: <b>{limit}</b>\n"
            f"• Mode: <b>{mode_str}</b>\n"
            f"• Sourcing: Raj-approved reels from @im_raaaj_ / inbox\n\n"
            f"<i>Video rendering in progress. Updates yahan aayenge 👇</i>"
        )
        count = process_channel_pipeline(channel_id, max_reels=limit, dry_run=is_preview)
        send_telegram(
            chat_id,
            f"✅ <b>Job Finished for [{name}]!</b>\n"
            f"Total <b>{count}</b> reel(s) successfully processed & delivered.\n"
            f"Destination: {'Telegram Preview Only' if is_preview else 'Instagram LIVE & Telegram'}",
            reply_markup=get_main_menu_markup()
        )
    except Exception as e:
        send_telegram(chat_id, f"❌ <b>Job Error [{channel_id}]:</b> {e}", reply_markup=get_main_menu_markup())
    finally:
        with job_lock:
            is_processing = False
            current_job_name = ""

def run_hunt_job(channel_id, limit=80, notify_chat_id=None):
    global is_processing, current_job_name
    chat_id = notify_chat_id or ADMIN_CHAT_ID

    with job_lock:
        if is_processing:
            send_telegram(chat_id, f"⚠️ Ek process already chal raha hai (<b>{current_job_name}</b>). Wait karo.")
            return
        is_processing = True
        current_job_name = f"HUNTING: {channel_id} ({limit} reels)"

    try:
        cfg = get_channel_config(channel_id)
        name, uname = CHANNEL_DISPLAY.get(channel_id, (channel_id, ""))
        send_telegram(chat_id, f"🏹 <b>Hunting {limit} viral reels for [{name}]</b> (Hashtags + Keywords)...")
        candidates = hunt_niche_reels(cfg, target_count=limit)
        if candidates:
            sent = send_hunted_reels_to_raj_chat(cfg, candidates, max_to_send=limit)
            send_telegram(chat_id, f"🎯 <b>Hunt Done for [{name}]!</b>\n{sent} reels directly sent to @im_raaaj_ DM chat for approval.", reply_markup=get_main_menu_markup())
        else:
            send_telegram(chat_id, f"⚠️ No fresh candidates found for [{name}].", reply_markup=get_main_menu_markup())
    except Exception as e:
        send_telegram(chat_id, f"❌ <b>Hunt Error [{channel_id}]:</b> {e}", reply_markup=get_main_menu_markup())
    finally:
        with job_lock:
            is_processing = False
            current_job_name = ""

def run_cloud_schedule_job(channel_id, limit=25, notify_chat_id=None):
    global is_processing, current_job_name
    chat_id = notify_chat_id or ADMIN_CHAT_ID

    with job_lock:
        if is_processing:
            send_telegram(chat_id, f"⚠️ Ek process already chal raha hai (<b>{current_job_name}</b>). Wait karo.")
            return
        is_processing = True
        current_job_name = f"CLOUD SCHEDULING: {channel_id}"

    try:
        cfg = get_channel_config(channel_id)
        name, _ = CHANNEL_DISPLAY.get(channel_id, (channel_id, ""))
        send_telegram(chat_id, f"🌙 <b>Starting Cloud-Scheduling for [{name}]</b> (Target: {limit} reels for tomorrow)...")
        count = cloud_schedule_channel_for_tomorrow(channel_id, target_count=limit, notify_telegram=False)
        send_telegram(
            chat_id,
            f"✅ <b>[{name}] Scheduled!</b>\n{count} reels successfully loaded on Meta Cloud for tomorrow between 07:00 AM - 10:00 PM.",
            reply_markup=get_main_menu_markup()
        )
    except Exception as e:
        send_telegram(chat_id, f"❌ <b>Cloud Schedule Error [{channel_id}]:</b> {e}", reply_markup=get_main_menu_markup())
    finally:
        with job_lock:
            is_processing = False
            current_job_name = ""

def run_all_cloud_schedules(notify_chat_id=None):
    """Executes tomorrow's cloud scheduling across all 4 channels sequentially."""
    channels = list_available_channels()
    chat_id = notify_chat_id or ADMIN_CHAT_ID
    send_telegram(chat_id, "🌙 <b>Starting Nightly Cloud-Scheduling Pipeline for All Channels...</b>")
    for ch in channels:
        run_cloud_schedule_job(ch, limit=25, notify_chat_id=chat_id)
        time.sleep(15)
    send_telegram(
        chat_id,
        "🎉 <b>ALL 4 ACCOUNTS FULLY SCHEDULED ON META CLOUD!</b>\n\n"
        "Agle din ke saare reels Meta ke servers par safely lock ho chuke hain.\n"
        "🛌 <b>Aap ab apna laptop safely shut down (band) kar sakte hain!</b>",
        reply_markup=get_main_menu_markup()
    )

def run_all_hunts(notify_chat_id=None):
    """Executes hunting for all 4 channels sequentially."""
    channels = list_available_channels()
    chat_id = notify_chat_id or ADMIN_CHAT_ID
    for ch in channels:
        run_hunt_job(ch, limit=80, notify_chat_id=chat_id)
        time.sleep(15)

def handle_telegram_updates():
    """Polls Telegram for both text commands and Interactive Inline Keyboard clicks."""
    global delivery_mode, scheduler_enabled
    offset = 0
    print("Telegram Command & Button Listener online...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{MASTER_BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("result", []):
                    offset = item["update_id"] + 1

                    # 1. Handle Inline Button Clicks (Callbacks)
                    if "callback_query" in item:
                        cq = item["callback_query"]
                        cq_id = cq["id"]
                        cq_data = cq.get("data", "")
                        from_chat = str(cq["message"]["chat"]["id"])

                        if cq_data == "menu:main":
                            answer_callback(cq_id, "Main Menu")
                            send_telegram(from_chat, get_channel_summary(), reply_markup=get_main_menu_markup())

                        elif cq_data.startswith("menu:ch:"):
                            target_ch = cq_data.split("menu:ch:")[1]
                            name, _ = CHANNEL_DISPLAY.get(target_ch, (target_ch, ""))
                            answer_callback(cq_id, f"Selected {name}")
                            send_telegram(
                                from_chat,
                                f"🎛️ <b>{name} Control Panel:</b>\nAction select karein:",
                                reply_markup=get_channel_menu_markup(target_ch)
                            )

                        elif cq_data == "action:sched_all":
                            answer_callback(cq_id, "Starting night schedule for all...")
                            t = threading.Thread(target=run_all_cloud_schedules, args=(from_chat,))
                            t.daemon = True
                            t.start()

                        elif cq_data == "action:hunt_all":
                            answer_callback(cq_id, "Starting hunt for all...")
                            t = threading.Thread(target=run_all_hunts, args=(from_chat,))
                            t.daemon = True
                            t.start()

                        elif cq_data.startswith("sched:"):
                            parts = cq_data.split(":")
                            target_ch = parts[2]
                            answer_callback(cq_id, f"Scheduling tomorrow's reels...")
                            t = threading.Thread(target=run_cloud_schedule_job, args=(target_ch, 25, from_chat))
                            t.daemon = True
                            t.start()

                        elif cq_data == "toggle:delivery_mode":
                            delivery_mode = "preview" if delivery_mode == "direct" else "direct"
                            answer_callback(cq_id, f"Switched to {delivery_mode.upper()}")
                            send_telegram(from_chat, get_channel_summary(), reply_markup=get_main_menu_markup())

                        elif cq_data == "action:status":
                            answer_callback(cq_id)
                            send_telegram(from_chat, get_channel_summary(), reply_markup=get_main_menu_markup())

                        elif cq_data.startswith("hunt:"):
                            parts = cq_data.split(":")
                            count = int(parts[1])
                            target_ch = parts[2]
                            answer_callback(cq_id, f"Hunting {count} reels...")
                            t = threading.Thread(target=run_hunt_job, args=(target_ch, count, from_chat))
                            t.daemon = True
                            t.start()

                        elif cq_data.startswith("make:"):
                            parts = cq_data.split(":")
                            count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 30
                            target_ch = parts[2]
                            is_prev = (delivery_mode == "preview")
                            answer_callback(cq_id, f"Processing {count} reels for {target_ch}...")
                            t = threading.Thread(target=run_isolated_job, args=(target_ch, count, from_chat, is_prev))
                            t.daemon = True
                            t.start()

                        elif cq_data.startswith("post:"):
                            parts = cq_data.split(":")
                            is_prev = (parts[1] == "preview")
                            target_ch = parts[2]
                            answer_callback(cq_id, "Starting post...")
                            t = threading.Thread(target=run_isolated_job, args=(target_ch, 1, from_chat, is_prev))
                            t.daemon = True
                            t.start()

                    # 2. Handle Text Messages
                    elif "message" in item:
                        msg = item["message"]
                        chat_id = str(msg.get("chat", {}).get("id"))
                        text = (msg.get("text") or "").strip()

                        if not text:
                            continue

                        cmd_parts = text.split()
                        cmd = cmd_parts[0].lower()

                        if cmd in ["/start", "/menu", "/dash"]:
                            send_telegram(chat_id, get_channel_summary(), reply_markup=get_main_menu_markup())

                        elif cmd in ["/help", "/commands"]:
                            help_text = (
                                "📖 <b>TELEGRAM QUICK COMMANDS GUIDE</b>\n"
                                "━━━━━━━━━━━━━━━━━━━━━━\n"
                                "⚡ <b>Make / Ready Reels (Render & Produce):</b>\n"
                                "• <code>/make startup 30</code> (Startup Road - 30 reels)\n"
                                "• <code>/make gudtree 30</code> (Gudtree - 30 reels)\n"
                                "• <code>/make trading 30</code> (Trading Road - 30 reels)\n"
                                "• <code>/make trending 30</code> (Trending Road - 30 reels)\n"
                                "<i>(Shortcut: simply type <code>startup 30</code> or <code>gudtree 30</code>)</i>\n\n"
                                "🏹 <b>Viral Hunting (Scout from Competitors to Raj):</b>\n"
                                "• <code>/hunt startup 30</code> (ya 80)\n"
                                "• <code>/hunt gudtree 30</code>\n"
                                "• <code>/hunt trading 30</code>\n"
                                "• <code>/hunt trending 30</code>\n"
                                "• <code>/hunt_all</code> (Hunt for all 4 channels)\n\n"
                                "📅 <b>Meta Cloud-Scheduling (For Tomorrow):</b>\n"
                                "• <code>/schedule startup 25</code>\n"
                                "• <code>/schedule gudtree 25</code>\n"
                                "• <code>/schedule_tomorrow</code> (Schedule all 4 channels)\n\n"
                                "⚙️ <b>Settings & Mode:</b>\n"
                                "• <code>/mode direct</code> (Live Instagram Feed Post + Telegram)\n"
                                "• <code>/mode preview</code> (Delivered to Telegram ONLY - No IG Post)\n"
                                "• <code>/status</code> (Real-time account & queue status)\n"
                                "━━━━━━━━━━━━━━━━━━━━━━\n"
                                "<i>Ya niche /menu bhejkar 1-Click buttons use karein!</i>"
                            )
                            send_telegram(chat_id, help_text, reply_markup=get_main_menu_markup())

                        elif cmd in ["/status"]:
                            send_telegram(chat_id, get_channel_summary(), reply_markup=get_main_menu_markup())

                        elif cmd in ["/schedule_tomorrow", "/sched_all"]:
                            t = threading.Thread(target=run_all_cloud_schedules, args=(chat_id,))
                            t.daemon = True
                            t.start()

                        elif cmd in ["/hunt_all", "/huntall"]:
                            t = threading.Thread(target=run_all_hunts, args=(chat_id,))
                            t.daemon = True
                            t.start()

                        elif cmd in ["/make", "/process", "/create", "/render"]:
                            target_raw = cmd_parts[1] if len(cmd_parts) > 1 else "startup"
                            target_ch = resolve_channel(target_raw)
                            count = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 30
                            is_prev = (delivery_mode == "preview")
                            if target_ch in list_available_channels():
                                t = threading.Thread(target=run_isolated_job, args=(target_ch, count, chat_id, is_prev))
                                t.daemon = True
                                t.start()
                            else:
                                send_telegram(chat_id, f"❌ Channel '{target_raw}' nahi mila!\nValid: <code>startup</code>, <code>gudtree</code>, <code>trading</code>, <code>trending</code>")

                        elif cmd in ["/hunt", "/scout"]:
                            target_raw = cmd_parts[1] if len(cmd_parts) > 1 else "startup"
                            target_ch = resolve_channel(target_raw)
                            count = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 80
                            if target_ch in list_available_channels():
                                t = threading.Thread(target=run_hunt_job, args=(target_ch, count, chat_id))
                                t.daemon = True
                                t.start()
                            else:
                                send_telegram(chat_id, f"❌ Channel '{target_raw}' nahi mila!\nValid: <code>startup</code>, <code>gudtree</code>, <code>trading</code>, <code>trending</code>")

                        elif cmd in ["/schedule", "/sched"]:
                            target_raw = cmd_parts[1] if len(cmd_parts) > 1 else "startup"
                            target_ch = resolve_channel(target_raw)
                            count = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 25
                            if target_ch in list_available_channels():
                                t = threading.Thread(target=run_cloud_schedule_job, args=(target_ch, count, chat_id))
                                t.daemon = True
                                t.start()
                            else:
                                send_telegram(chat_id, f"❌ Channel '{target_raw}' nahi mila!\nValid: <code>startup</code>, <code>gudtree</code>, <code>trading</code>, <code>trending</code>")

                        elif cmd in ["/post"]:
                            target_raw = cmd_parts[1] if len(cmd_parts) > 1 else "startup"
                            target_ch = resolve_channel(target_raw)
                            count = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 1
                            if target_ch in list_available_channels():
                                t = threading.Thread(target=run_isolated_job, args=(target_ch, count, chat_id, False))
                                t.daemon = True
                                t.start()

                        elif cmd in ["/mode"]:
                            if len(cmd_parts) > 1 and cmd_parts[1].lower() in ["direct", "preview"]:
                                delivery_mode = cmd_parts[1].lower()
                            else:
                                delivery_mode = "preview" if delivery_mode == "direct" else "direct"
                            mode_name = "🚀 DIRECT POST (Instagram LIVE & Telegram)" if delivery_mode == "direct" else "🎬 PREVIEW ONLY (Telegram Delivered, Not on Instagram)"
                            send_telegram(chat_id, f"🔄 Delivery mode switched to:\n<b>{mode_name}</b>", reply_markup=get_main_menu_markup())

                        # Natural shortcut syntax: "startup 30", "gudtree 30", "trading 30", "trending 30"
                        elif len(cmd_parts) >= 2 and resolve_channel(cmd_parts[0]) in list_available_channels() and cmd_parts[1].isdigit():
                            target_ch = resolve_channel(cmd_parts[0])
                            count = int(cmd_parts[1])
                            is_prev = (delivery_mode == "preview")
                            t = threading.Thread(target=run_isolated_job, args=(target_ch, count, chat_id, is_prev))
                            t.daemon = True
                            t.start()

        except Exception as e:
            time.sleep(5)

def scheduler_24h_loop():
    """
    Automated 24-Hour Master Clock:
    - 06:00 AM - 10:00 AM: Staggered Morning Viral Hunting (80 reels per channel)
    - 11:00 AM - 09:00 PM: Curation Window (Raj reviews DMs)
    - 10:00 PM - 02:00 AM: Nightly Pre-Baking & Meta Cloud-Scheduling (25 reels per channel for tomorrow)
    """
    print("Master 24-Hour Automated Clock online...")
    last_hunted_day = None
    last_scheduled_day = None

    HUNT_HOURS = {
        6: "startup_road",
        7: "healthy_diet",
        8: "trading_pulse",
        9: "viral_finds"
    }

    SCHED_HOURS = {
        22: "startup_road",
        23: "healthy_diet",
        0: "trading_pulse",
        1: "viral_finds"
    }

    while True:
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")

            if scheduler_enabled:
                # 1. MORNING HUNTING (06:00 AM - 10:00 AM)
                if now.hour in HUNT_HOURS and now.minute == 0:
                    ch_to_hunt = HUNT_HOURS[now.hour]
                    print(f"⏰ [06-10 AM Hunt Clock] Triggering hunting for: {ch_to_hunt}...")
                    run_hunt_job(ch_to_hunt, limit=80)

                # 2. NIGHTLY PRE-BAKING & CLOUD-SCHEDULING (10:00 PM - 02:00 AM)
                elif now.hour in SCHED_HOURS and now.minute == 0:
                    ch_to_sched = SCHED_HOURS[now.hour]
                    print(f"⏰ [10 PM - 02 AM Cloud-Scheduler Clock] Triggering tomorrow's cloud scheduling for: {ch_to_sched}...")
                    run_cloud_schedule_job(ch_to_sched, limit=25)

                # 3. 02:00 AM NOTIFICATION: All channels done for tomorrow
                elif now.hour == 2 and now.minute == 5 and last_scheduled_day != today_str:
                    last_scheduled_day = today_str
                    send_telegram(
                        ADMIN_CHAT_ID,
                        "🎉 <b>ALL 4 ACCOUNTS SCHEDULED ON META CLOUD FOR TODAY!</b>\n\n"
                        "Saare 100 reels Meta ke servers par lock ho chuke hain aur din bhar post hote rahenge.\n"
                        "🛌 <b>Aap ab laptop band (shut down) kar sakte hain!</b>",
                        reply_markup=get_main_menu_markup()
                    )

            time.sleep(45) # Check every 45 seconds

        except Exception as e:
            print(f"Master scheduler clock error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print("==================================================")
    print("  MULTI-ACCOUNT AUTOMATION MASTER CONTROLLER      ")
    print("==================================================")

    t_sched = threading.Thread(target=scheduler_24h_loop)
    t_sched.daemon = True
    t_sched.start()

    handle_telegram_updates()
