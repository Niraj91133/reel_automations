import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "711598335")

def ensure_video_for_delivery(video_path):
    """
    Ensures video is under 19.5 MB so that Telegram's getFile API 
    can generate a public CDN link for Meta Graph API auto-publishing.
    Telegram's hard limit for getFile download URLs is 20 MB.
    """
    MAX_SIZE = int(19.5 * 1024 * 1024) # 19.5 MB for getFile API compatibility
    if not os.path.exists(video_path):
        return video_path
    
    file_size = os.path.getsize(video_path)
    if file_size <= MAX_SIZE:
        return video_path

    print(f"⚠️ Video size ({file_size / (1024*1024):.1f} MB) exceeds Telegram getFile 20MB limit! Compressing with FFmpeg...", flush=True)
    compressed_path = f"compressed_{os.path.basename(video_path)}"
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "faster",
        "-c:a", "aac",
        "-b:a", "128k",
        compressed_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(compressed_path):
        new_size = os.path.getsize(compressed_path)
        if new_size > MAX_SIZE:
            crf_31_path = f"c31_{os.path.basename(video_path)}"
            cmd2 = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-c:v", "libx264",
                "-crf", "31",
                "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "96k",
                crf_31_path
            ]
            res2 = subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res2.returncode == 0 and os.path.exists(crf_31_path):
                if os.path.exists(compressed_path):
                    try: os.remove(compressed_path)
                    except: pass
                compressed_path = crf_31_path
                new_size = os.path.getsize(compressed_path)

        print(f"✅ Video successfully compressed to {new_size / (1024*1024):.1f} MB for Meta Graph API & Telegram!", flush=True)
        return compressed_path
    return video_path

def send_reel_to_telegram(video_path, caption_text, target_chat_id=None, token=None):
    use_token = token or TELEGRAM_BOT_TOKEN
    chat_id = str(target_chat_id or TELEGRAM_CHAT_ID)
    url = f"https://api.telegram.org/bot{use_token}/sendVideo"
    final_video = ensure_video_for_delivery(video_path)
    print(f"Sending {final_video} to Telegram (chat: {chat_id})...")
    
    success = False
    public_url = None
    try:
        with open(final_video, "rb") as video_file:
            files = {"video": video_file}
            data = {
                "chat_id": chat_id,
                "caption": caption_text[:1024],
                "parse_mode": "HTML",
                "supports_streaming": True
            }
            r = requests.post(url, data=data, files=files, timeout=180)
            
        resp_obj = None
        if r.status_code == 200:
            print("Successfully sent reel to Telegram!")
            success = True
            resp_obj = r.json()
        else:
            print(f"Telegram HTML send returned {r.status_code}, trying plain text...")
            with open(final_video, "rb") as video_file:
                files = {"video": video_file}
                data = {
                    "chat_id": chat_id,
                    "caption": caption_text[:1024].replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""),
                    "supports_streaming": True
                }
                r2 = requests.post(url, data=data, files=files, timeout=180)
                if r2.status_code == 200:
                    success = True
                    resp_obj = r2.json()

        if success and resp_obj:
            try:
                file_id = resp_obj.get("result", {}).get("video", {}).get("file_id")
                if file_id:
                    f_info = requests.get(f"https://api.telegram.org/bot{use_token}/getFile?file_id={file_id}", timeout=15)
                    if f_info.status_code == 200:
                        file_path = f_info.json().get("result", {}).get("file_path")
                        if file_path:
                            public_url = f"https://api.telegram.org/file/bot{use_token}/{file_path}"
                            print(f"🔗 [Telegram CDN] Public video URL obtained: {public_url[:60]}...", flush=True)
                    else:
                        print(f"⚠️ Telegram getFile failed ({f_info.status_code}): {f_info.text}", flush=True)
            except Exception as e:
                print(f"Warning: Could not get public file URL from Telegram: {e}", flush=True)
    finally:
        # Clean up temporary compressed file if one was generated
        if final_video != video_path and os.path.exists(final_video):
            try: os.remove(final_video)
            except: pass

    return success, public_url

if __name__ == '__main__':
    print("Telegram sender ready.")
