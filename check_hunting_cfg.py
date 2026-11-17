import glob
import json

for cfg in sorted(glob.glob("configs/*.json")):
    with open(cfg, "r", encoding="utf-8") as f:
        d = json.load(f)
    hs = d.get("hunting_settings", {})
    cs = d.get("content_settings", {})
    cat = d.get("category", "")
    print(f"{cfg}: category={cat}, dm_target={hs.get('dm_target_chat')}, thread={hs.get('dm_thread_url')}")
