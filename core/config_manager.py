import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIGS_DIR = BASE_DIR / "configs"
DATABASES_DIR = BASE_DIR / "databases"

# Use high-performance local SSD cache outside OneDrive if available
# This prevents Windows OneDrive from churning CPU to sync multi-megabyte temporary video files
LOCAL_CACHE = Path("C:/reel_cache")
if LOCAL_CACHE.exists():
    WORKSPACES_DIR = LOCAL_CACHE
else:
    WORKSPACES_DIR = BASE_DIR / "workspaces"

# Ensure runtime directories exist
DATABASES_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)

def load_master_config():
    master_path = CONFIGS_DIR / "master_config.json"
    if master_path.exists():
        with open(master_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "channels": ["startup_road", "healthy_diet", "trading_pulse", "viral_finds"],
        "default_model": "gemini-3.1-flash-lite"
    }

def get_channel_config(channel_id):
    """
    Loads config for a specific channel and resolves environment variables if present.
    Creates an isolated workspace and database path for this channel.
    """
    config_file = CONFIGS_DIR / f"{channel_id}.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found for channel: {channel_id} at {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Set up isolated workspace and DB path
    channel_workspace = WORKSPACES_DIR / channel_id
    channel_workspace.mkdir(parents=True, exist_ok=True)
    
    channel_db = DATABASES_DIR / f"{channel_id}_history.db"

    config["runtime"] = {
        "workspace_dir": str(channel_workspace),
        "db_path": str(channel_db)
    }

    # Allow environment variables to override sensitive credentials if set
    env_prefix = channel_id.upper()
    creds = config.get("credentials", {})
    creds["gemini_api_key"] = os.environ.get(f"{env_prefix}_GEMINI_KEY", creds.get("gemini_api_key", ""))
    creds["instagram_account_id"] = os.environ.get(f"{env_prefix}_IG_ID", creds.get("instagram_account_id", ""))
    creds["page_access_token"] = os.environ.get(f"{env_prefix}_PAGE_TOKEN", creds.get("page_access_token", ""))
    creds["telegram_chat_id"] = os.environ.get(f"{env_prefix}_CHAT_ID", creds.get("telegram_chat_id", ""))
    creds["telegram_bot_token"] = os.environ.get(f"{env_prefix}_BOT_TOKEN", creds.get("telegram_bot_token", ""))

    return config

def save_channel_config(channel_id, new_config):
    """Saves updated channel config back to configs/{channel_id}.json."""
    config_file = CONFIGS_DIR / f"{channel_id}.json"
    # Remove transient runtime info before saving to disk
    save_data = dict(new_config)
    save_data.pop("runtime", None)
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    return True

def list_available_channels():
    master = load_master_config()
    return master.get("channels", [])

if __name__ == "__main__":
    for ch in list_available_channels():
        cfg = get_channel_config(ch)
        print(f"Loaded {ch}: DB -> {cfg['runtime']['db_path']}")
