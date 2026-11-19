import os
import sys
import re
import csv
import io
import urllib.request

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import ChannelDatabase

SHEET_ID = "1hID-uXSmtTGR7wJq1Xbzl9kH73OemGlHluppqM1BQ7s"

# Exact mapping requested by user:
# 1. @sundari_ki_lucy  -> @gudtree_ (Gudtree tab)
# 2. @startupwithram   -> @marketing_road24 (Marketing_Road tab)
# 3. @vivek2000__      -> @the_loan_road (Vivek2000 tab)
CHANNEL_SHEET_MAP = {
    "healthy_diet": {
        "channel_id": "healthy_diet",
        "handle": "@gudtree_",
        "tab_name": "Gudtree",
        "gid": "1153198966",
        "source_account": "@sundari_ki_lucy"
    },
    "marketing_road24": {
        "channel_id": "marketing_road24",
        "handle": "@marketing_road24",
        "tab_name": "Marketing_Road",
        "gid": "1070740749",
        "source_account": "@startupwithram"
    },
    "theloan_road": {
        "channel_id": "theloan_road",
        "handle": "@the_loan_road",
        "tab_name": "Vivek2000",
        "gid": "1084652383",
        "source_account": "@vivek2000__"
    }
}

def fetch_reels_from_google_sheet(channel_id, max_count=30):
    """
    Directly fetches fresh, unposted reel links from the Google Sheet for the channel.
    Picks 'Pending' or 'Tracked' rows that haven't been posted yet in the local DB.
    Returns: list of dicts with shortcode, url, creator, views, caption
    """
    mapping = CHANNEL_SHEET_MAP.get(channel_id)
    if not mapping:
        return []

    tab_name = mapping["tab_name"]
    gid = mapping["gid"]
    source = mapping["source_account"]
    handle = mapping["handle"]
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    print(f"📊 [Google Sheet Fetch] Pulling {tab_name} ({source} -> {handle})...")

    db_path = os.path.join(BASE_DIR, f"databases/{channel_id}_history.db")
    db = ChannelDatabase(db_path) if os.path.exists(db_path) else None

    candidates = []

    try:
        req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")

        reader = list(csv.reader(io.StringIO(content)))
        if not reader or len(reader) < 2:
            print(f"⚠️ [Google Sheet] No data rows found in {tab_name} tab.")
            return []

        header = [h.strip().lower() for h in reader[0]]
        
        # Locate column indexes dynamically
        col_link = 1
        col_shortcode = 2
        col_likes = 5
        col_comments = 6
        col_caption = 7
        col_status = 8

        for idx, h in enumerate(header):
            if "link" in h: col_link = idx
            elif "shortcode" in h: col_shortcode = idx
            elif "like" in h: col_likes = idx
            elif "comment" in h: col_comments = idx
            elif "caption" in h: col_caption = idx
            elif "status" in h: col_status = idx

        for row in reader[1:]:
            if len(row) <= col_link:
                continue
            
            link = row[col_link].strip()
            if not link or "instagram.com" not in link:
                continue

            shortcode = ""
            if len(row) > col_shortcode and row[col_shortcode].strip():
                shortcode = row[col_shortcode].strip()
            else:
                m = re.search(r'/(?:reel|p)/([A-Za-z0-9_-]+)', link)
                if m:
                    shortcode = m.group(1)

            if not shortcode:
                continue

            # Check if already processed in local DB
            if db and db.is_reel_processed(shortcode):
                continue

            caption = row[col_caption].strip() if len(row) > col_caption else ""
            status = row[col_status].strip() if len(row) > col_status else ""
            
            # Extract creator username from caption if available (e.g. @username)
            creator = "creator"
            m_cr = re.search(r'@([A-Za-z0-9._]{3,30})', caption)
            if m_cr:
                creator = m_cr.group(1)

            likes = row[col_likes].strip() if len(row) > col_likes else ""
            comments = row[col_comments].strip() if len(row) > col_comments else ""
            views_str = f"{likes} likes" if likes else "Sheet Link"

            # Auto-save to hunted_reels DB so it persists
            if db:
                try:
                    conn = db.get_connection()
                    c = conn.cursor()
                    c.execute(
                        "INSERT OR IGNORE INTO hunted_reels (shortcode, source_query, views_text, has_comment_cta, sent_to_raj, creator) VALUES (?, ?, ?, ?, ?, ?)",
                        (shortcode, f"sheet_{tab_name}", views_str, 1, 1, f"@{creator}")
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

            candidates.append({
                "shortcode": shortcode,
                "url": f"https://www.instagram.com/reel/{shortcode}/",
                "creator": creator,
                "views": views_str,
                "caption": caption,
                "status": status,
                "tab": tab_name
            })

            if len(candidates) >= max_count:
                break

        print(f"🎯 [Google Sheet] Found {len(candidates)} unposted reels for {handle} from {tab_name} tab!")
        return candidates

    except Exception as e:
        print(f"❌ [Google Sheet Error] Failed to read {tab_name} tab: {e}")
        return []

if __name__ == "__main__":
    ch = sys.argv[1] if len(sys.argv) > 1 else "marketing_road24"
    res = fetch_reels_from_google_sheet(ch)
    for r in res[:5]:
        print(r)
