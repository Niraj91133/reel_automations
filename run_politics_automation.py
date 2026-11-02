import os
import sys
import time
import requests
import sqlite3
import subprocess
from datetime import datetime
from politics_dm_scraper import get_politics_reels_from_chat
from scraper import download_reel_video
from ai_service import analyze_reel_content
from politics_template import create_politics_base_layer, create_politics_circle_layer

sys.stdout.reconfigure(encoding='utf-8')

POLITICS_BOT_TOKEN = "8997893199:AAEUxCeRiVupFV9KElzdsni2kTre7klWteM"
POLITICS_CHAT_ID = "5903254012"
POLITICS_DB_PATH = "politics_history.db"

def init_politics_db():
    conn = sqlite3.connect(POLITICS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_politics_reels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shortcode TEXT UNIQUE,
            username TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_politics_reel_processed(shortcode):
    conn = sqlite3.connect(POLITICS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM processed_politics_reels WHERE shortcode = ?", (shortcode,))
    row = cursor.fetchone()
    conn.close()
    if row is not None:
        return True

    # Also check reels_history.db to avoid duplicate reels across channels
    if os.path.exists("reels_history.db"):
        try:
            conn_reels = sqlite3.connect("reels_history.db")
            c_reels = conn_reels.cursor()
            c_reels.execute("SELECT id FROM processed_reels WHERE shortcode = ?", (shortcode,))
            row_reels = c_reels.fetchone()
            conn_reels.close()
            if row_reels is not None:
                return True
        except:
            pass
    return False

def mark_politics_reel_processed(shortcode, username, title):
    conn = sqlite3.connect(POLITICS_DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO processed_politics_reels (shortcode, username, title) VALUES (?, ?, ?)",
            (shortcode, username, title)
        )
        conn.commit()
    finally:
        conn.close()

def extract_thumbnail_for_circle(video_path, output_img_path="circle_hook.jpg"):
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:02.500",
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "1",
        output_img_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_img_path):
        return output_img_path
    return None

def process_politics_reel(video_file_path, reel_id, username="creator", reel_index=1, total_reels=10):
    print(f"\n==========================================")
    print(f"🇮🇳 Processing Politics Reel {reel_index}/{total_reels}: {reel_id} (Creator: @{username})")
    print(f"==========================================")

    init_politics_db()
    if is_politics_reel_processed(reel_id):
        print(f"Reel {reel_id} already processed before in Politics DB. Skipping.")
        return False

    # 1. AI Content Analysis with Gemini Real Audio (Viral SEO Mode)
    print("Calling Gemini AI for political/national speech analysis (Viral SEO Mode)...")
    ai_data = analyze_reel_content(video_file_path, creator_username=username, category="politics")
    hook_pill = ai_data.get("hook_pill", "Bharat Ki Awaz")
    main_title = ai_data.get("main_title", "Desh Ki Badi Khabar Aur Vishleshan")
    sub_quote = ai_data.get("sub_quote", '"Loktantra me janta ki awaz hi sabse badi taqat hai"')
    caption = ai_data.get("caption", f"Insights from @{username}\n\nCredits: @{username}")

    print(f"Hook Pill: {hook_pill}")
    print(f"Main Title: {main_title}")
    print(f"Sub Quote: {sub_quote}")

    # 2. Extract Circle Image Hook
    circle_img = extract_thumbnail_for_circle(video_file_path, "temp_pol_circle.jpg")

    # 3. Generate Bhagwa Layers & Video Render
    base_layer_path = "temp_pol_base.png"
    circle_layer_path = "temp_pol_circle_layer.png"
    output_processed_path = f"final_pol_{reel_id}.mp4"

    create_politics_base_layer(
        output_path=base_layer_path,
        hook_pill=hook_pill,
        main_title=main_title,
        sub_quote=sub_quote
    )
    create_politics_circle_layer(
        output_path=circle_layer_path,
        circle_img_path=circle_img
    )

    print("Rendering Ultra-HD Politics Video with FFmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_file_path,
        "-loop", "1", "-i", base_layer_path,
        "-loop", "1", "-i", circle_layer_path,
        "-filter_complex",
        (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[vid];"
            "[vid][1:v]overlay=0:0[with_base];"
            "[2:v]fade=t=out:st=4.3:d=0.7:alpha=1[circle_faded];"
            "[with_base][circle_faded]overlay=0:0:enable='between(t,0,5)'[v_out]"
        ),
        "-map", "[v_out]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        output_processed_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode != 0:
        raise RuntimeError("FFmpeg processing failed for Politics reel")

    # Ensure output is strictly under 50MB for Telegram
    send_target_path = output_processed_path
    if os.path.exists(output_processed_path) and os.path.getsize(output_processed_path) > 48 * 1024 * 1024:
        comp_path = f"comp_{output_processed_path}"
        subprocess.run([
            "ffmpeg", "-y", "-i", output_processed_path,
            "-c:v", "libx264", "-crf", "26", "-preset", "faster",
            "-c:a", "aac", "-b:a", "128k", comp_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(comp_path):
            send_target_path = comp_path

    # 4. Clean Direct Instagram Caption (Title + AI Transcript + Credits + Hashtags)
    clean_title = main_title.replace(chr(10), ' ').strip()
    caption_body = caption.strip()
    if f"@{username}" not in caption_body:
        caption_body += f"\n\nCredits & Speaker: @{username}"
    
    full_caption = f"🔥 <b>{clean_title}</b>\n\n{caption_body}"

    # 5. Send to Second Telegram Bot
    print(f"Sending finished Politics reel to Telegram Bot...")
    url = f"https://api.telegram.org/bot{POLITICS_BOT_TOKEN}/sendVideo"
    with open(send_target_path, "rb") as vf:
        r = requests.post(
            url,
            data={"chat_id": POLITICS_CHAT_ID, "caption": full_caption[:1024], "parse_mode": "HTML", "supports_streaming": True},
            files={"video": vf},
            timeout=180
        )
    sent = r.status_code == 200

    if not sent:
        # Fallback to plain text if HTML had parsing issue
        with open(send_target_path, "rb") as vf:
            r2 = requests.post(
                url,
                data={"chat_id": POLITICS_CHAT_ID, "caption": full_caption[:1024].replace("<b>","").replace("</b>",""), "supports_streaming": True},
                files={"video": vf},
                timeout=180
            )
            sent = r2.status_code == 200

    if sent:
        mark_politics_reel_processed(reel_id, username, main_title)
        print(f"Reel {reel_id} delivered to Politics Telegram bot successfully!")

    # Cleanup temp
    if send_target_path != output_processed_path and os.path.exists(send_target_path):
        try: os.remove(send_target_path)
        except: pass

    # Cleanup temp
    for f in [base_layer_path, circle_layer_path, output_processed_path, circle_img]:
        if f and os.path.exists(f):
            try: os.remove(f)
            except: pass

    return sent

def send_daily_politics_start_message(day_name, date_str, total_found):
    url = f"https://api.telegram.org/bot{POLITICS_BOT_TOKEN}/sendMessage"
    text = (
        f"🇮🇳 <b>JAI HIND! TODAY'S POLITICS REEL BATCH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Day:</b> {day_name}\n"
        f"🗓️ <b>Date:</b> {date_str}\n"
        f"🎯 <b>Found:</b> {total_found} new reels from @baatleaderki!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Delivering ready-to-post Bhagwa template reels below 👇</i>"
    )
    try:
        requests.post(url, json={"chat_id": POLITICS_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
    except:
        pass

def run_politics_daily_automation(max_reels=10, target_chat_id=None, notify_callback=None):
    chat_id = target_chat_id or POLITICS_CHAT_ID
    now = datetime.now()
    day_name = now.strftime("%A")
    date_str = now.strftime("%d-%b-%Y")

    print("========================================================")
    print(f"   STARTING POLITICS AUTOMATION: {day_name.upper()}     ")
    print("========================================================")
    init_politics_db()

    if notify_callback:
        notify_callback(f"🔍 <b>Politics:</b> @baatleaderki chat se reels fetch kar rha hu...")

    reels = get_politics_reels_from_chat(max_count=max(max_reels, 25))
    if not reels:
        print("No shared reels found in @baatleaderki chat.")
        msg_text = "⚠️ <b>Politics Update:</b> @baatleaderki chat me koi shared reels nahi mili!"
        try:
            requests.post(
                f"https://api.telegram.org/bot{POLITICS_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"},
                timeout=10
            )
        except:
            pass
        if notify_callback:
            notify_callback(msg_text)
        return 0

    unprocessed = [r for r in reels if not is_politics_reel_processed(r["shortcode"])]
    print(f"Total fresh unprocessed politics reels found: {len(unprocessed)}")

    if not unprocessed:
        print("No new politics reels today. Already up to date!")
        msg_text = "ℹ️ <b>Politics Update:</b> @baatleaderki chat me sabhi reels already processed hain! Chat me nayi reels share karein fir run karein."
        try:
            requests.post(
                f"https://api.telegram.org/bot{POLITICS_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"},
                timeout=10
            )
        except:
            pass
        if notify_callback:
            notify_callback(msg_text)
        return 0

    target_reels = unprocessed[:max_reels]
    total_today = len(target_reels)

    send_daily_politics_start_message(day_name, date_str, total_today)

    processed_count = 0
    for idx, item in enumerate(target_reels, start=1):
        shortcode = item["shortcode"]
        reel_url = item["url"]
        creator = item["creator"]

        if notify_callback:
            notify_callback(f"📥 <b>[Politics {idx}/{total_today}]</b> Downloading reel from @{creator}...")

        temp_video = f"temp_pol_{shortcode}.mp4"
        print(f"\n📥 Downloading Reel ({idx}/{total_today}): {reel_url}...")
        downloaded = download_reel_video(reel_url, temp_video)

        if downloaded and os.path.exists(downloaded):
            try:
                if notify_callback:
                    notify_callback(f"🇮🇳 <b>[Politics {idx}/{total_today}]</b> Bhagwa Ultra-HD video render ho rhi hai...")
                success = process_politics_reel(
                    video_file_path=downloaded,
                    reel_id=shortcode,
                    username=creator,
                    reel_index=idx,
                    total_reels=total_today
                )
                if success:
                    processed_count += 1
                    if notify_callback:
                        notify_callback(f"🚀 <b>[Politics {idx}/{total_today}]</b> Delivered to Politics Channel! ✅")
            except Exception as e:
                print(f"Error processing reel {shortcode}:", e)
                if notify_callback:
                    notify_callback(f"⚠️ Error in politics reel {shortcode}: {e}")
            finally:
                if os.path.exists(temp_video):
                    try: os.remove(temp_video)
                    except: pass

    print(f"\n🎉 Finished Politics batch! Delivered {processed_count} reels to Politics Telegram Bot!")
    return processed_count

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_politics_daily_automation(limit)
