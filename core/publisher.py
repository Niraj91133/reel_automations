import os
import sys
import time
import requests

GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class InstagramPublisher:
    """
    Multi-tenant Instagram Graph API publisher.
    Fully isolated per channel using distinct Account IDs and Access Tokens.
    """
    def __init__(self, instagram_account_id, page_access_token):
        self.account_id = str(instagram_account_id)
        self.token = str(page_access_token)

    def is_configured(self):
        return bool(
            self.account_id and 
            self.token and 
            not self.account_id.startswith("YOUR_") and 
            not self.token.startswith("YOUR_")
        )

    def create_reel_container(self, video_url, caption, creator_username=None):
        """Step 1: Initializes the Reel Media Container on Meta's servers."""
        url = f"{BASE_URL}/{self.account_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": self.token
        }
        
        if creator_username and creator_username.lower() != "creator":
            clean_tag = creator_username.replace("@", "").strip()
            import json
            payload["user_tags"] = json.dumps([{"username": clean_tag, "x": 0.5, "y": 0.5}])

        resp = requests.post(url, data=payload, timeout=60)
        data = resp.json()
        
        if resp.status_code == 200 and "id" in data:
            return data["id"]
        elif "user_tags" in payload:
            # If user_tags failed, retry without tag
            payload.pop("user_tags", None)
            resp2 = requests.post(url, data=payload, timeout=60)
            data2 = resp2.json()
            if resp2.status_code == 200 and "id" in data2:
                return data2["id"]

        print(f"❌ [Meta API Error] {data.get('error', {}).get('message', resp.text)}")
        return None

    def wait_for_processing(self, container_id, max_retries=30, delay=10):
        """Step 2: Polls Meta servers until video rendering/encoding is FINISHED."""
        url = f"{BASE_URL}/{container_id}"
        params = {
            "fields": "status_code,status",
            "access_token": self.token
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status_code", "UNKNOWN")
                    if status == "FINISHED":
                        return True
                    elif status in ["ERROR", "EXPIRED"]:
                        print(f"❌ [Meta API] Video failed: {status}")
                        return False
            except Exception as e:
                print(f"Status check error: {e}")
            time.sleep(delay)
            
        print("❌ [Meta API] Timed out waiting for video processing.")
        return False

    def publish_container(self, container_id):
        """Step 3: Publishes the processed container directly to the Instagram feed."""
        url = f"{BASE_URL}/{self.account_id}/media_publish"
        payload = {
            "creation_id": container_id,
            "access_token": self.token
        }
        resp = requests.post(url, data=payload, timeout=60)
        data = resp.json()
        if resp.status_code == 200 and "id" in data:
            return data["id"]
        return None

    def get_reel_permalink(self, media_id):
        """Fetches live Instagram link (https://www.instagram.com/reel/...)"""
        url = f"{BASE_URL}/{media_id}"
        params = {
            "fields": "permalink,shortcode",
            "access_token": self.token
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("permalink")
        except:
            pass
        return None

    def publish_reel(self, public_video_url, caption, creator_username=None):
        """Full publishing workflow returning permalink."""
        if not self.is_configured():
            print(f"⚠️ Channel Instagram credentials not configured. Skipping auto-publish.")
            return None

        container_id = self.create_reel_container(public_video_url, caption, creator_username)
        if not container_id:
            return None
            
        if not self.wait_for_processing(container_id):
            return None
            
        media_id = self.publish_container(container_id)
        if not media_id:
            return None
            
        permalink = self.get_reel_permalink(media_id)
        return {
            "media_id": media_id,
            "permalink": permalink or f"https://www.instagram.com/reel/"
        }
