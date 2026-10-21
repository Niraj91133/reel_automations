import os
import sys
import time
import requests
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

from db import init_db, is_reel_processed, mark_reel_processed
from ai_service import analyze_reel_content
from video_processor import process_video_with_template
from telegram_sender import send_reel_to_telegram

def extract_thumbnail_for_circle(video_path, output_img_path="circle_hook.jpg"):
    """
    Extracts high-resolution, sharp keyframe from the reel for the circular hook.
    Selects 2.5 seconds mark where the speaker/topic visual is stable and clear.
    """
    cmd = [
        "ffmpeg", "-y",
        "-ss", "00:00:02.500",
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "1",  # Maximum JPEG quality
        output_img_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_img_path):
        return output_img_path
    return None

def process_single_reel(video_file_path, reel_id, username="creator"):
    print(f"\n==========================================")
    print(f"Processing Reel: {reel_id} (Original Creator: @{username})")
    print(f"==========================================")

    init_db()
    if is_reel_processed(reel_id):
        print(f"Reel {reel_id} already processed before! Skipping to avoid duplicates.")
        return False

    # 1. AI Analysis with Gemini
    print("Calling Gemini AI for content analysis, headline & caption...")
    ai_data = analyze_reel_content(video_file_path, creator_username=username)
    hook_pill = ai_data.get("hook_pill", "Must Watch")
    main_title = ai_data.get("main_title", "Important Lesson For Creators")
    sub_quote = ai_data.get("sub_quote", '"Stay consistent and build"')
    caption = ai_data.get("caption", f"Insights from @{username}\n\nCredits: @{username}")

    print(f"Hook Pill: {hook_pill}")
    print(f"Main Title: {main_title}")
    print(f"Sub Quote: {sub_quote}")

    # 2. Extract Crystal Clear Circle Image Hook
    circle_img = extract_thumbnail_for_circle(video_file_path, "temp_circle.jpg")

    # 3. Video Rendering with Solid Black Bottom + Big Text + 5s Animated Circle
    output_processed_path = f"final_{reel_id}.mp4"
    print("Rendering custom 9:16 template video with FFmpeg...")
    process_video_with_template(
        input_video_path=video_file_path,
        output_video_path=output_processed_path,
        hook_pill=hook_pill,
        main_title=main_title,
        sub_quote=sub_quote,
        circle_img_path=circle_img
    )

    # 4. Delivery to Telegram
    full_caption = (
        f"<b>{main_title.replace(chr(10), ' ')}</b>\n\n"
        f"{caption}\n\n"
        f"Original Creator: @{username}\n"
        f"Status: Ready to Post 🚀"
    )

    print("Sending finished video to Telegram...")
    sent = send_reel_to_telegram(output_processed_path, full_caption)

    if sent:
        mark_reel_processed(reel_id, username, main_title)
        print(f"Reel {reel_id} successfully delivered and logged into Database!")
    
    # Clean up local temporary files
    if os.path.exists(output_processed_path):
        os.remove(output_processed_path)
    if circle_img and os.path.exists(circle_img):
        os.remove(circle_img)

    return sent

if __name__ == '__main__':
    init_db()
    print("Pipeline ready.")
