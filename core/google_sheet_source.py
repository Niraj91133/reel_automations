import os
import sys
import csv
import io
import re
import urllib.request
from typing import List, Dict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import ChannelDatabase
from core.config_manager import get_channel_config

SHEET_ID = "1hID-uXSmtTGR7wJq1Xbzl9kH73OemGlHluppqM1BQ7s"

# Exact Sheet Tab Routing per User Architecture
CHANNEL_SHEET_MAPPING = {
    "healthy_diet": {
        "tab_name": "Gudtree",
        "gid": "1153198966",
        "display_name": "Gud Tree",
        "source_handle": "@sundari_ki_lucy",
        "dest_handle": "@gudtree_"
    },
    "marketing_road24": {
        "tab_name": "Marketing_Road",
        "gid": "1070740749",
        "display_name": "Marketing Road",
        "source_handle": "@startupwithram",
        "dest_handle": "@marketing_road24"
    },
    "theloan_road": {
        "tab_name": "Vivek2000",
        "gid": "1084652383",
        "display_name": "The Loan Road",
        "source_handle": "@vivek2000__",
        "dest_handle": "@the_loan_road"
    }
}

def get_pending_reels_from_sheet(channel_id: str, limit: int = 30) -> List[Dict]:
    """
    Fetches unposted pending reels directly from the Google Sheet tab for this channel.
    Cross-checks with local SQLite database to guarantee ZERO duplicates.
    """
    mapping = CHANNEL_SHEET_MAPPING.get(channel_id)
    if not mapping:
        return []

    tab_name = mapping["tab_name"]
    gid = mapping["gid"]
    display_name = mapping["display_name"]

    cfg = get_channel_config(channel_id)
    db_path = cfg.get("runtime", {}).get("db_path")
    db = ChannelDatabase(db_path) if db_path else None

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    print(f"\n📥 [Google Sheet Bridge] Reading {tab_name} tab for [{display_name}]...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            reader = list(csv.reader(io.StringIO(content)))

        if len(reader) <= 1:
            print(f"ℹ️ [Google Sheet Bridge] {tab_name} tab is empty.")
            return []

        # Find column indices from header
        header = [h.strip().lower() for h in reader[0]]
        link_col = 1
        shortcode_col = 2
        caption_col = 7
        status_col = 8

        for idx, col in enumerate(header):
            if "reel link" in col or "link" in col:
                link_col = idx
            elif "shortcode" in col or "code" in col:
                shortcode_col = idx
            elif "caption" in col:
                caption_col = idx
            elif "status" in col:
                status_col = idx

        candidates = []
        for row in reader[1:]:
            if len(row) <= link_col:
                continue

            reel_url = row[link_col].strip()
            if not reel_url or ("instagram.com" not in reel_url and "/reel/" not in reel_url):
                continue

            # Extract shortcode
            shortcode = ""
            if len(row) > shortcode_col and row[shortcode_col].strip():
                shortcode = row[shortcode_col].strip()
            else:
                m = re.search(r'/(?:reel|p)/([A-Za-z0-9_-]+)', reel_url)
                if m:
                    shortcode = m.group(1)

            if not shortcode:
                continue

            # Check status column: Pending, Tracked, or blank are eligible
            status_val = row[status_col].strip().lower() if len(row) > status_col else ""
            if status_val in ("sent", "processed", "posted", "failed", "rejected"):
                continue

            # Check local DB so we never re-post
            if db and db.is_reel_processed(shortcode):
                continue

            # Extract creator handle from caption if available
            caption_text = row[caption_col].strip() if len(row) > caption_col else ""
            creator = "creator"
            m_cr = re.search(r'@([A-Za-z0-9._]+)', caption_text)
            if m_cr:
                creator = m_cr.group(1)

            candidates.append({
                "shortcode": shortcode,
                "url": f"https://www.instagram.com/reel/{shortcode}/",
                "creator": creator,
                "caption": caption_text,
                "source_tab": tab_name,
                "views": "Google Sheet Curated"
            })

            if len(candidates) >= limit:
                break

        print(f"🎯 [Google Sheet Bridge] Found {len(candidates)} unposted reels for [{display_name}] from {tab_name} tab!")
        return candidates

    except Exception as e:
        print(f"❌ [Google Sheet Bridge] Error reading sheet for {channel_id}: {e}")
        return []

if __name__ == '__main__':
    for ch_id in ["healthy_diet", "marketing_road24", "theloan_road"]:
        reels = get_pending_reels_from_sheet(ch_id, limit=5)
        print(f"Result for {ch_id}: {len(reels)} candidate reels")
        for r in reels:
            print(f"  • {r['shortcode']} | @{r['creator']} | {r['url']}")
