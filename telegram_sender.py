import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8149202459:AAGRZBE4uZY7UXUV4HySazIuc-M5V2hHK8A")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "711598335")

def send_reel_to_telegram(video_path, caption_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    print(f"Sending {video_path} to Telegram...")
    
    with open(video_path, "rb") as video_file:
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
        return True
    else:
        print("Telegram HTML send failed, trying plain text...")
        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption_text[:1024].replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""),
                "supports_streaming": True
            }
            r2 = requests.post(url, data=data, files=files, timeout=180)
            return r2.status_code == 200

if __name__ == '__main__':
    print("Telegram sender ready.")
