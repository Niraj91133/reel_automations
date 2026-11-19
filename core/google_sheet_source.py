import os
import sys
import re
import csv
import io
import json
import urllib.request
from datetime import datetime

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

            status = row[col_status].strip() if len(row) > col_status else ""
            if status.lower() in ("sent", "posted"):
                continue

            # Check if already processed in local DB
            if db and db.is_reel_processed(shortcode):
                continue
            
            caption = row[col_caption].strip() if len(row) > col_caption else ""
            
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

def mark_reel_in_sheet_posted(channel_id, shortcode, live_permalink=None):
    """
    Updates the reel status when posted:
    1. Writes to databases/sheet_posted_reels.json to keep permanent audit trail.
    2. If GOOGLE_SHEET_WEBHOOK_URL is configured in .env, sends POST to update Google Sheet cell in real-time.
    """
    mapping = CHANNEL_SHEET_MAP.get(channel_id)
    tab_name = mapping["tab_name"] if mapping else "Unknown"

    # 1. Local persistent tracking log
    try:
        log_file = os.path.join(BASE_DIR, "databases/sheet_posted_reels.json")
        data = []
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                try: data = json.load(f)
                except: data = []
        data.append({
            "channel_id": channel_id,
            "tab": tab_name,
            "shortcode": shortcode,
            "permalink": live_permalink,
            "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"📝 [Sheet Tracker] Logged posted reel {shortcode} for {tab_name} tab.")
    except Exception as e_log:
        print(f"Sheet Tracker notice: {e_log}")

    # 2. Remote Webhook Update (if configured)
    webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
    if webhook_url:
        try:
            payload = json.dumps({
                "action": "mark_posted",
                "tab": tab_name,
                "shortcode": shortcode,
                "status": "Posted",
                "live_link": live_permalink or "",
                "posted_date": datetime.now().strftime("%Y-%m-%d")
            }).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"✅ [Google Sheet Sync] Successfully marked {shortcode} as Posted in {tab_name} tab.")
        except Exception as e_wh:
            print(f"⚠️ [Google Sheet Sync Warning] Webhook update failed: {e_wh}")

def sync_pending_posted_reels_to_sheet():
    """
    Scans all mapped channels for reels that are posted locally in DB
    but still marked 'Pending' in the Google Sheet.
    Uses Playwright in headless mode to update the cells to 'Sent' and today's date.
    """
    from playwright.sync_api import sync_playwright
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Group pending updates by tab
    updates_by_tab = {}

    for channel_id, mapping in CHANNEL_SHEET_MAP.items():
        tab_name = mapping["tab_name"]
        gid = mapping["gid"]
        db_path = os.path.join(BASE_DIR, f"databases/{channel_id}_history.db")
        if not os.path.exists(db_path):
            continue
        db = ChannelDatabase(db_path)

        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        try:
            req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
            reader = list(csv.reader(io.StringIO(content)))
            if not reader:
                continue

            col_link = 1
            col_shortcode = 2
            col_status = 8
            for idx, h in enumerate(reader[0]):
                h_l = h.lower().strip()
                if "shortcode" in h_l: col_shortcode = idx
                elif "link" in h_l: col_link = idx
                elif "status" in h_l: col_status = idx

            rows_to_update = []
            for r_idx, row in enumerate(reader[1:], start=2):
                if len(row) <= col_link:
                    continue
                sc = row[col_shortcode].strip() if len(row) > col_shortcode else ""
                link = row[col_link].strip()
                if not sc and link:
                    m = re.search(r'/(?:reel|p)/([A-Za-z0-9_-]+)', link)
                    if m: sc = m.group(1)
                if not sc:
                    continue

                curr_status = row[col_status].strip().lower() if len(row) > col_status else ""
                if curr_status not in ("sent", "posted") and db.is_reel_processed(sc):
                    rows_to_update.append(r_idx)

            if rows_to_update:
                updates_by_tab[tab_name] = {"gid": gid, "rows": rows_to_update}

        except Exception as e:
            print(f"Error checking sheet tab {tab_name}: {e}")

    if not updates_by_tab:
        print("✅ [Sheet Sync] All posted reels are already up-to-date in Google Sheet!")
        return True

    print(f"🔄 [Sheet Sync] Updating Google Sheet for {sum(len(v['rows']) for v in updates_by_tab.values())} rows...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 900})

            for tab_name, info in updates_by_tab.items():
                gid = info["gid"]
                rows = info["rows"]
                tab_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={gid}"
                page.goto(tab_url)
                page.wait_for_timeout(7000)

                for r_num in rows:
                    print(f"   -> [{tab_name}] Setting Row {r_num}: Status='Sent', Date='{today_str}'")
                    # Update Column I
                    name_box = page.wait_for_selector("#t-name-box", timeout=10000)
                    name_box.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.type(f"I{r_num}")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(400)

                    f_bar = page.wait_for_selector("#t-formula-bar-input", timeout=5000)
                    f_bar.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.type("Sent")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(500)

                    # Update Column J
                    name_box.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.type(f"J{r_num}")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(400)

                    f_bar.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.type(today_str)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(500)

            page.wait_for_timeout(3500)
            browser.close()
            print("✅ [Sheet Sync] Successfully synced all posted reels to Google Sheet!")
            return True
    except Exception as e_pw:
        print(f"❌ [Sheet Sync Error] Playwright update failed: {e_pw}")
        return False

if __name__ == "__main__":
    ch = sys.argv[1] if len(sys.argv) > 1 else "marketing_road24"
    res = fetch_reels_from_google_sheet(ch)
    for r in res[:5]:
        print(r)
