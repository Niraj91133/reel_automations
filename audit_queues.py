import glob
import json
import os

for q in sorted(glob.glob("C:/reel_cache/*/tomorrow_reels")):
    js = sorted(glob.glob(os.path.join(q, "ready_*.json")))
    mp4s = sorted(glob.glob(os.path.join(q, "ready_*.mp4")))
    print(f"\n=== {q} === (JSON: {len(js)}, MP4: {len(mp4s)})")
    for j in js:
        try:
            with open(j, "r", encoding="utf-8") as f:
                d = json.load(f)
            print(f"  File: {os.path.basename(j)} | Code: {d.get('shortcode')} | Creator: {d.get('creator')}")
            print(f"  Title: {repr(d.get('title'))}")
            print(f"  Hook Pill: {repr(d.get('hook_pill'))}")
            caption_preview = d.get('caption', '').replace('\n', ' ')[:100]
            print(f"  Caption: {caption_preview}...")
        except Exception as e:
            print(f"  Error reading {j}: {e}")
