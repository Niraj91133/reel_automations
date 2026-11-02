import os
import sys
import time
import requests
import subprocess
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

from db import init_db, is_reel_processed, mark_reel_processed
from ai_service import analyze_reel_content
from video_processor import process_video_with_template
from telegram_sender import send_reel_to_telegram
from instagram_publisher import publish_reel_pipeline

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

def process_single_reel(video_file_path, reel_id, username="creator", reel_index=1, total_reels=10, target_chat_id=None):
    print(f"\n==========================================")
    print(f"Processing Reel {reel_index}/{total_reels}: {reel_id} (Creator: @{username})")
    print(f"==========================================")

    init_db()
    if is_reel_processed(reel_id):
        print(f"Reel {reel_id} already processed before! Skipping to avoid duplicates.")
        return False

    # 1. AI Analysis with Gemini Real Speech (Viral SEO Mode)
    print("Calling Gemini AI for real spoken audio analysis (Viral SEO Mode)...")
    ai_data = analyze_reel_content(video_file_path, creator_username=username, category="startup")
    hook_pill = ai_data.get("hook_pill", "Must Watch")
    main_title = ai_data.get("main_title", "Important Lesson For Creators")
    sub_quote = ai_data.get("sub_quote", '"Stay consistent and build"')
    caption = ai_data.get("caption", f"Insights from @{username}\n\nCredits: @{username}")

    print(f"Hook Pill: {hook_pill}")
    print(f"Main Title: {main_title}")
    print(f"Sub Quote: {sub_quote}")

    # 2. Extract High-Res Keyframe Hook
    circle_img = extract_thumbnail_for_circle(video_file_path, "temp_circle.jpg")

    # 3. Video Rendering with Safe Zone + Smooth Top Fade + Authentic Arrow
    output_processed_path = f"final_{reel_id}.mp4"
    print("Rendering Ultra-HD video with FFmpeg...")
    process_video_with_template(
        input_video_path=video_file_path,
        output_video_path=output_processed_path,
        hook_pill=hook_pill,
        main_title=main_title,
        sub_quote=sub_quote,
        circle_img_path=circle_img
    )

    # 4. Clean Direct Instagram Caption (Title + AI Transcript + Credits + Hashtags)
    clean_title = main_title.replace(chr(10), ' ').strip()
    caption_body = caption.strip()
    if f"@{username}" not in caption_body:
        caption_body += f"\n\nCredits & Speaker: @{username}"
    
    full_caption = f"🔥 <b>{clean_title}</b>\n\n{caption_body}"

    print("Sending finished video to Telegram...")
    sent, public_video_url = send_reel_to_telegram(output_processed_path, full_caption, target_chat_id=target_chat_id)

    # 5. Official Meta Graph API Auto-Publish to @startup_road
    insta_permalink = None
    if sent and public_video_url:
        print("🚀 Auto-publishing Reel to @startup_road via Official Meta Graph API...", flush=True)
        clean_insta_caption = f"🔥 {clean_title}\n\n{caption_body}"
        try:
            insta_result = publish_reel_pipeline(public_video_url, clean_insta_caption, creator_username=username)
            if insta_result and "permalink" in insta_result:
                insta_permalink = insta_result["permalink"]
                print(f"🏆 Reel successfully published on Instagram! Link: {insta_permalink}", flush=True)
                # Send confirmation message to Telegram
                try:
                    from telegram_sender import TELEGRAM_BOT_TOKEN
                    notify_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                    requests.post(notify_url, json={
                        "chat_id": str(target_chat_id or "711598335"),
                        "text": f"🎉 <b>Reel LIVE on Instagram (@startup_road)!</b>\n\n🔗 <b>Watch here:</b>\n{insta_permalink}",
                        "parse_mode": "HTML"
                    }, timeout=15)
                except Exception as e_notif:
                    print(f"Note: Could not send insta link to telegram: {e_notif}", flush=True)
        except Exception as e_pub:
            print(f"❌ Instagram publishing error: {e_pub}", flush=True)

    if sent:
        mark_reel_processed(reel_id, username, main_title)
        print(f"Reel {reel_id} successfully delivered and logged into Database!")
    
    # Clean up local temporary files
    if os.path.exists(output_processed_path):
        try: os.remove(output_processed_path)
        except: pass
    if circle_img and os.path.exists(circle_img):
        try: os.remove(circle_img)
        except: pass

    return sent

if __name__ == '__main__':
    init_db()
    print("Pipeline ready.")
