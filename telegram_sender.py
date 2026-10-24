import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "711598335")

def ensure_under_50mb(video_path):
    """Ensures video is under Telegram's strict 50MB limit by compressing if necessary."""
    MAX_SIZE = 48 * 1024 * 1024 # 48 MB safety limit
    if not os.path.exists(video_path):
        return video_path
    
    file_size = os.path.getsize(video_path)
    if file_size <= MAX_SIZE:
        return video_path

    print(f"⚠️ Video size ({file_size / (1024*1024):.1f} MB) exceeds Telegram 50MB limit! Compressing with FFmpeg...", flush=True)
    compressed_path = f"compressed_{os.path.basename(video_path)}"
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-c:v", "libx264",
        "-crf", "26",
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", "128k",
        compressed_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(compressed_path):
        new_size = os.path.getsize(compressed_path)
        print(f"✅ Video successfully compressed to {new_size / (1024*1024):.1f} MB for Telegram!", flush=True)
        return compressed_path
    return video_path

def send_reel_to_telegram(video_path, caption_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    final_video = ensure_under_50mb(video_path)
    print(f"Sending {final_video} to Telegram...")
    
    success = False
    try:
        with open(final_video, "rb") as video_file:
            files = {"video": video_file}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption_text[:1024],
                "parse_mode": "HTML",
                "supports_streaming": True
            }
            r = requests.post(url, data=data, files=files, timeout=180)
            
        if r.status_code == 200:
            print("Successfully sent reel to Telegram!")
            success = True
        else:
            print(f"Telegram HTML send returned {r.status_code}, trying plain text...")
            with open(final_video, "rb") as video_file:
                files = {"video": video_file}
                data = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": caption_text[:1024].replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""),
                    "supports_streaming": True
                }
                r2 = requests.post(url, data=data, files=files, timeout=180)
                success = (r2.status_code == 200)
    finally:
        # Clean up temporary compressed file if one was generated
        if final_video != video_path and os.path.exists(final_video):
            try: os.remove(final_video)
            except: pass

    return success

if __name__ == '__main__':
    print("Telegram sender ready.")
