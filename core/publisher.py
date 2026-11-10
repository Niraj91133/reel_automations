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
    Supports auto-publishing, user tagging, and automated first comments.
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

    def create_reel_container(self, video_url, caption, creator_username=None, scheduled_publish_time=None):
        """Step 1: Initializes the Reel Media Container on Meta's servers (supports cloud scheduling)."""
        url = f"{BASE_URL}/{self.account_id}/media"
        payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": self.token
        }
        
        if scheduled_publish_time:
            # Unix timestamp for future cloud publish (between 15 mins and 75 days)
            payload["scheduled_publish_time"] = int(scheduled_publish_time)

        if creator_username and creator_username.lower() not in ["creator", "approved_creator"]:
            clean_tag = creator_username.replace("@", "").strip()
            import json
            payload["user_tags"] = json.dumps([{"username": clean_tag, "x": 0.5, "y": 0.5}])

        resp = requests.post(url, data=payload, timeout=60)
        data = resp.json()
        
        if resp.status_code == 200 and "id" in data:
            return data["id"]
        elif "user_tags" in payload:
            payload.pop("user_tags", None)
            resp2 = requests.post(url, data=payload, timeout=60)
            data2 = resp2.json()
            if resp2.status_code == 200 and "id" in data2:
                return data2["id"]

        print(f"❌ [Meta API Error] {data.get('error', {}).get('message', resp.text)}")
        from core.iron_shield import CircuitBreaker
        CircuitBreaker.check_response_and_trip_if_needed(self.account_id, data.get("error", {}))
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
        from core.iron_shield import CircuitBreaker
        CircuitBreaker.check_response_and_trip_if_needed(self.account_id, data.get("error", {}))
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

    def post_first_comment(self, media_id, comment_text):
        """Posts an engagement-boosting first comment via Meta Graph API."""
        if not media_id or not comment_text or not self.is_configured():
            return None
        url = f"{BASE_URL}/{media_id}/comments"
        payload = {
            "message": comment_text,
            "access_token": self.token
        }
        try:
            resp = requests.post(url, data=payload, timeout=30)
            data = resp.json()
            if resp.status_code == 200 and "id" in data:
                print(f"💬 [Meta API] Auto-posted first comment: '{comment_text[:40]}...' (ID: {data['id']})")
                return data["id"]
            else:
                print(f"⚠️ [Meta API Comment Note] {data.get('error', {}).get('message', resp.text)}")
        except Exception as e:
            print(f"Error posting first comment: {e}")
        return None

    def publish_reel(self, public_video_url, caption, creator_username=None, first_comment=None, scheduled_publish_time=None):
        """Full publishing workflow returning permalink and posting first comment or cloud scheduling."""
        if not self.is_configured():
            print(f"⚠️ Channel Instagram credentials not configured. Skipping auto-publish.")
            return None

        # Check Circuit Breaker Lockdown
        from core.iron_shield import CircuitBreaker
        is_locked, lock_reason = CircuitBreaker.is_channel_locked(self.account_id)
        if is_locked:
            print(f"🛑 [CIRCUIT BREAKER LOCKDOWN ACTIVE] Skipping publish for account {self.account_id}: {lock_reason}")
            return None

        # Meta Policy Compliance Pre-Flight Gatekeeper
        try:
            from core.compliance_guard import check_text_compliance
            is_safe, category, matched = check_text_compliance(caption)
            if not is_safe:
                print(f"🛑 [Compliance Guard BLOCKED] Post aborted due to Meta Policy [{category}] violation: '{matched}'")
                return None
        except Exception as e_comp:
            print(f"Compliance check warning: {e_comp}")

        container_id = self.create_reel_container(
            video_url=public_video_url,
            caption=caption,
            creator_username=creator_username,
            scheduled_publish_time=scheduled_publish_time
        )
        if not container_id:
            return None
            
        if not self.wait_for_processing(container_id):
            return None

        if scheduled_publish_time:
            # In Meta Graph API: If scheduled_publish_time is set, DO NOT call publish_container!
            # Meta will automatically publish the container at scheduled_publish_time.
            print(f"📅 [Meta Cloud] Reel scheduled successfully! Container ID: {container_id} (Epoch: {scheduled_publish_time})")
            return {
                "media_id": container_id,
                "container_id": container_id,
                "permalink": f"https://www.instagram.com/reel/",
                "scheduled_publish_time": scheduled_publish_time,
                "is_scheduled": True
            }

        media_id = self.publish_container(container_id)
        if not media_id:
            return None
            
        permalink = self.get_reel_permalink(media_id)

        # Automated first comment (for immediate posts)
        if first_comment:
            time.sleep(2)
            self.post_first_comment(media_id, first_comment)

        return {
            "media_id": media_id,
            "permalink": permalink or f"https://www.instagram.com/reel/",
            "scheduled_publish_time": None,
            "is_scheduled": False
        }

    def publish_story(self, public_media_url, is_video=False, user_tags=None):
        """
        Publishes an Instagram Story (1080x1920) via Meta Graph API.
        Supports photo stories, video stories, and interactive user_tags stickers.
        """
        if not self.is_configured():
            print(f"⚠️ Channel Instagram credentials not configured. Skipping story publish.")
            return None

        # Check Circuit Breaker
        from core.iron_shield import CircuitBreaker
        is_locked, lock_reason = CircuitBreaker.is_channel_locked(self.account_id)
        if is_locked:
            print(f"🛑 [CIRCUIT BREAKER LOCK] Skipping story: {lock_reason}")
            return None

        url = f"{BASE_URL}/{self.account_id}/media"
        payload = {
            "media_type": "STORIES",
            "access_token": self.token
        }
        if is_video:
            payload["video_url"] = public_media_url
        else:
            payload["image_url"] = public_media_url

        if user_tags:
            try:
                import json
                payload["user_tags"] = json.dumps(user_tags) if isinstance(user_tags, list) else user_tags
            except Exception as e_tag:
                print(f"Note on user_tags encoding: {e_tag}")

        try:
            resp = requests.post(url, data=payload, timeout=60)
            data = resp.json()
            if resp.status_code != 200 and user_tags:
                print(f"⚠️ [Meta API] user_tags rejected on Story: {data.get('error', {}).get('message')}. Retrying clean Story publish...")
                payload.pop("user_tags", None)
                resp = requests.post(url, data=payload, timeout=60)
                data = resp.json()

            if resp.status_code != 200 or "id" not in data:
                err_msg = data.get("error", {}).get("message", resp.text)
                print(f"❌ [Meta API Story Error] {err_msg}")
                CircuitBreaker.check_response_and_trip_if_needed(self.account_id, data.get("error", {}))
                return None

            container_id = data["id"]
            if is_video:
                if not self.wait_for_processing(container_id):
                    return None
            else:
                time.sleep(3) # Settle image container

            media_id = self.publish_container(container_id)
            if media_id:
                print(f"🌟 [Meta API] Story LIVE successfully! (Media ID: {media_id})")
                return {"media_id": media_id, "is_story": True}
        except Exception as e:
            print(f"Story publish error: {e}")

        return None
