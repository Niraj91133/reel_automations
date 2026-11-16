import os
import sys
import time
import json
import requests
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from core.config_manager import get_channel_config
    cfg = get_channel_config("thestartup_street")
    INSTAGRAM_ACCOUNT_ID = cfg.get("credentials", {}).get("instagram_account_id", "17841464149880503")
    PAGE_ACCESS_TOKEN = cfg.get("credentials", {}).get("page_access_token", "")
except Exception:
    cfg_file = os.path.join(BASE_DIR, "configs", "thestartup_street.json")
    if os.path.exists(cfg_file):
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            INSTAGRAM_ACCOUNT_ID = data.get("credentials", {}).get("instagram_account_id", "17841464149880503")
            PAGE_ACCESS_TOKEN = data.get("credentials", {}).get("page_access_token", "")
    else:
        INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "17841464149880503")
        PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

GRAPH_API_VERSION = "v21.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

def create_reel_container(video_url, caption, creator_username=None):
    """
    Step 1: Initializes the Reel Media Container on Meta's servers.
    Includes user_tags tagging if creator_username is provided.
    """
    url = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    if creator_username and creator_username.lower() != "creator":
        clean_tag = creator_username.replace("@", "").strip()
        import json
        payload["user_tags"] = json.dumps([{"username": clean_tag, "x": 0.5, "y": 0.5}])
        print(f"🏷️ [Meta API] Tagging creator @{clean_tag} on Reel...", flush=True)

    print(f"🎬 [Meta API] Initializing Reel container for @startup_road...", flush=True)
    resp = requests.post(url, data=payload, timeout=60)
    data = resp.json()
    
    if resp.status_code == 200 and "id" in data:
        container_id = data["id"]
        print(f"✅ [Meta API] Container created successfully! Container ID: {container_id}", flush=True)
        return container_id
    elif "user_tags" in payload:
        # If user_tags failed (e.g. user disabled tagging), retry without user_tags
        print(f"⚠️ Tagging failed ({data.get('error', {}).get('message')}), retrying without user tag...", flush=True)
        payload.pop("user_tags", None)
        resp2 = requests.post(url, data=payload, timeout=60)
        data2 = resp2.json()
        if resp2.status_code == 200 and "id" in data2:
            return data2["id"]

    error_msg = data.get("error", {}).get("message", resp.text)
    print(f"❌ [Meta API] Failed to create container: {error_msg}", flush=True)
    return None

def wait_for_processing(container_id, max_retries=30, delay=10):
    """
    Step 2: Polls Meta servers until video rendering/encoding is FINISHED.
    """
    url = f"{BASE_URL}/{container_id}"
    params = {
        "fields": "status_code,status",
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    print(f"⏳ [Meta API] Waiting for Meta servers to process video (Container: {container_id})...", flush=True)
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status_code", "UNKNOWN")
                print(f"   [{attempt}/{max_retries}] Status: {status} ({data.get('status', '')})", flush=True)
                
                if status == "FINISHED":
                    print(f"🎉 [Meta API] Video processing finished and ready for publishing!", flush=True)
                    return True
                elif status in ["ERROR", "EXPIRED"]:
                    print(f"❌ [Meta API] Video processing failed with status: {status}", flush=True)
                    return False
        except Exception as e:
            print(f"   Warning during status check: {e}", flush=True)
            
        time.sleep(delay)
        
    print("❌ [Meta API] Timed out waiting for video processing.", flush=True)
    return False

def publish_container(container_id):
    """
    Step 3: Publishes the processed container directly to @startup_road.
    """
    url = f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    print(f"🚀 [Meta API] Publishing Reel to @startup_road feed...", flush=True)
    resp = requests.post(url, data=payload, timeout=60)
    data = resp.json()
    
    if resp.status_code == 200 and "id" in data:
        media_id = data["id"]
        print(f"🏆 [Meta API] REEL IS LIVE! Media ID: {media_id}", flush=True)
        return media_id
    else:
        error_msg = data.get("error", {}).get("message", resp.text)
        print(f"❌ [Meta API] Failed to publish media: {error_msg}", flush=True)
        return None

def get_reel_permalink(media_id):
    """
    Fetches the live permanent Instagram link (e.g. https://www.instagram.com/reel/...)
    """
    url = f"{BASE_URL}/{media_id}"
    params = {
        "fields": "permalink,shortcode",
        "access_token": PAGE_ACCESS_TOKEN
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("permalink")
    except Exception as e:
        print(f"Failed to fetch permalink: {e}", flush=True)
    return None

def publish_reel_pipeline(public_video_url, caption, creator_username=None):
    """
    Full End-to-End Reels Publishing Pipeline:
    1. Create Container (with creator tagging)
    2. Wait for Processing
    3. Publish to Live Feed
    4. Return Live Permalink
    """
    container_id = create_reel_container(public_video_url, caption, creator_username=creator_username)
    if not container_id:
        return None
        
    processed = wait_for_processing(container_id)
    if not processed:
        return None
        
    media_id = publish_container(container_id)
    if not media_id:
        return None
        
    permalink = get_reel_permalink(media_id)
    return {
        "media_id": media_id,
        "permalink": permalink or f"https://www.instagram.com/reel/"
    }

if __name__ == '__main__':
    print("Testing Instagram Publisher Connection...")
    r = requests.get(f"{BASE_URL}/{INSTAGRAM_ACCOUNT_ID}?fields=username,name,followers_count&access_token={PAGE_ACCESS_TOKEN}")
    print("Status:", r.status_code)
    print("Account:", r.json())
