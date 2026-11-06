import os
import requests

class TelegramHub:
    """
    Multi-channel Telegram router.
    Routes video previews, status alerts, and approval requests to dedicated channels.
    """
    def __init__(self, bot_token, default_chat_id=None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id

    def send_message(self, text, chat_id=None, parse_mode="HTML"):
        target_chat = str(chat_id or self.default_chat_id)
        if not target_chat or not self.bot_token:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                return True
            elif r.status_code == 400 and parse_mode:
                payload.pop("parse_mode", None)
                r2 = requests.post(url, json=payload, timeout=15)
                return r2.status_code == 200
        except Exception as e:
            print(f"Failed to send Telegram message to {target_chat}: {e}")
        return False

    def send_video_with_cdn_url(self, video_path, caption, chat_id=None):
        """
        Sends video to Telegram and retrieves public CDN link via getFile API.
        This public link is passed directly to Meta Graph API for publishing.
        """
        target_chat = str(chat_id or self.default_chat_id)
        if not target_chat or not self.bot_token:
            print("Telegram credentials missing.")
            return False, None

        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
        success = False
        public_url = None
        upload_path = video_path
        temp_comp = None
        
        try:
            # Strictly enforce < 19.5MB for Telegram getFile CDN compatibility
            if os.path.exists(video_path) and os.path.getsize(video_path) > 19.5 * 1024 * 1024:
                temp_comp = video_path + ".tg_comp.mp4"
                import subprocess
                cmd = ["ffmpeg", "-y", "-i", video_path, "-c:v", "h264_mf", "-b:v", "1800k", "-c:a", "aac", "-b:a", "128k", temp_comp]
                sub_res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if sub_res.returncode != 0 or not os.path.exists(temp_comp):
                    cmd_cpu = ["ffmpeg", "-y", "-i", video_path, "-threads", "2", "-c:v", "libx264", "-crf", "28", "-preset", "faster", "-c:a", "aac", "-b:a", "128k", temp_comp]
                    subprocess.run(cmd_cpu, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(temp_comp) and os.path.getsize(temp_comp) < os.path.getsize(video_path):
                    upload_path = temp_comp

            with open(upload_path, "rb") as video_file:
                files = {"video": video_file}
                data = {
                    "chat_id": target_chat,
                    "caption": caption[:1024],
                    "parse_mode": "HTML",
                    "supports_streaming": True
                }
                r = requests.post(url, data=data, files=files, timeout=180)
                
            resp_obj = None
            if r.status_code == 200:
                success = True
                resp_obj = r.json()
            else:
                # Retry plain text if HTML tags failed
                with open(upload_path, "rb") as video_file:
                    files = {"video": video_file}
                    clean_caption = caption[:1024].replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
                    data = {
                        "chat_id": target_chat,
                        "caption": clean_caption,
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
                        f_info = requests.get(f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}", timeout=15)
                        if f_info.status_code == 200:
                            file_path = f_info.json().get("result", {}).get("file_path")
                            if file_path:
                                public_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                except Exception as e:
                    print(f"Could not retrieve CDN URL: {e}")

        except Exception as e:
            print(f"Error sending video to Telegram: {e}")
        finally:
            if temp_comp and os.path.exists(temp_comp):
                try: os.remove(temp_comp)
                except: pass

        return success, public_url
