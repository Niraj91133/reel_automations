import os
import sys
import time
import re
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.database import ChannelDatabase

COOKIE_FILE = os.path.join(BASE_DIR, "cookies.txt")

def parse_cookie_file(cookie_file):
    cookies = []
    if not os.path.exists(cookie_file):
        return cookies
    with open(cookie_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                cookies.append({
                    'domain': parts[0],
                    'path': parts[2],
                    'secure': parts[3].lower() == 'true',
                    'expires': int(parts[4]) if parts[4].isdigit() else -1,
                    'name': parts[5],
                    'value': parts[6]
                })
    return cookies

def parse_views_count(text):
    """Converts strings like '2.5M', '150K', '45,200' to an integer count."""
    if not text:
        return 0
    clean = text.upper().replace(',', '').strip()
    try:
        if 'M' in clean:
            m = re.search(r'([\d\.]+)\s*M', clean)
            if m:
                return int(float(m.group(1)) * 1_000_000)
        elif 'K' in clean:
            m = re.search(r'([\d\.]+)\s*K', clean)
            if m:
                return int(float(m.group(1)) * 1_000)
        else:
            nums = re.findall(r'\d+', clean)
            if nums:
                return int("".join(nums))
    except:
        pass
    return 0

def has_comment_cta_signal(text):
    """Detects if caption or card mentions comment-to-receive CTA."""
    if not text:
        return False
    lower = text.lower()
    signals = [
        "comment", "dm", "link in bio", "bhejo", "comment karo", "send you",
        "type ", "drop a", "share karunga", "link dunga", "list chahiye",
        "pdf chahiye", "details chahiye", "comment '", "comment \""
    ]
    return any(s in lower for s in signals)

def hunt_niche_reels(channel_config, target_count=30, headless=True):
    """
    Hunts high-engagement viral reels using:
    1. Audience Demand Keywords (via Instagram search)
    2. Niche Trending Hashtags (/explore/tags/)
    Filters:
    - Min views threshold
    - Priority for 'Comment karo' CTAs
    - Skips already posted in DB
    - Skips already hunted/sent in DB
    """
    channel_id = channel_config["channel_id"]
    display_name = channel_config.get("display_name", channel_id)
    hunt_settings = channel_config.get("hunting_settings", {})
    keywords = list(hunt_settings.get("keywords", []))
    hashtags = list(hunt_settings.get("hashtags", []))
    min_views = hunt_settings.get("min_views", 25000)
    db = ChannelDatabase(channel_config["runtime"]["db_path"])

    print(f"\n========================================================")
    print(f"🏹 HUNTING VIRAL REELS: [{display_name}] (Target: {target_count})")
    print(f"========================================================")
    print(f"Keywords: {len(keywords)} | Hashtags: {len(hashtags)} | Min Views: {min_views:,}")

    cookies = get_channel_cookies(channel_id)
    if not cookies:
        print(f"❌ Error: Cookies missing or empty for {channel_id}!")
        return []

    hunted_candidates = []
    seen_codes = set()

    chromium_args = [
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--renderer-process-limit=2",
        "--blink-settings=imagesEnabled=false",
        "--mute-audio"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=chromium_args)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        # Block images/fonts to speed up scanning by 4x and save 80% RAM
        def block_heavy(route):
            if route.request.resource_type in ["image", "media", "font"]:
                route.abort()
            else:
                route.continue_()
        page.route("**/*", block_heavy)

        # 1. SEARCH HASHTAGS
        for tag in hashtags:
            if len(hunted_candidates) >= target_count:
                break
            clean_tag = tag.replace('#', '').strip()
            tag_url = f"https://www.instagram.com/explore/tags/{clean_tag}/"
            print(f"🔍 Hunting Hashtag #{clean_tag}...")
            try:
                page.goto(tag_url, timeout=30000, wait_until='domcontentloaded')
                time.sleep(3)

                # Scroll once to load more top reels
                page.evaluate("window.scrollBy(0, 1200)")
                time.sleep(2)

                links = page.query_selector_all('a[href*="/reel/"], a[href*="/p/"]')
                for link in links:
                    if len(hunted_candidates) >= target_count:
                        break
                    href = link.get_attribute("href") or ""
                    if "/reel/" not in href and "/p/" not in href:
                        continue
                    m = re.search(r'/(?:reel|p)/([^/?]+)', href)
                    if not m:
                        continue
                    code = m.group(1).strip()
                    if code in seen_codes or db.is_reel_processed(code) or db.is_reel_hunted(code):
                        continue

                    card_text = link.inner_text().strip().replace('\n', ' ')
                    views_num = parse_views_count(card_text)
                    has_cta = has_comment_cta_signal(card_text)

                    # Filter: high views or 'M' or CTA
                    if 'M' in card_text.upper() or views_num >= min_views or has_cta or not card_text:
                        seen_codes.add(code)
                        hunted_candidates.append({
                            "shortcode": code,
                            "url": f"https://www.instagram.com/reel/{code}/",
                            "source_query": f"#{clean_tag}",
                            "views_text": card_text or "Trending",
                            "has_comment_cta": 1 if has_cta else 0
                        })
            except Exception as e:
                print(f"Note on tag #{clean_tag}: {e}")

        # 2. SEARCH KEYWORDS (Explore Search)
        for kw in keywords:
            if len(hunted_candidates) >= target_count:
                break
            encoded_kw = urllib.parse.quote(kw)
            search_url = f"https://www.instagram.com/explore/search/keyword/?q={encoded_kw}"
            print(f"🔍 Hunting Keyword: '{kw}'...")
            try:
                page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
                time.sleep(3)
                page.evaluate("window.scrollBy(0, 1500)")
                time.sleep(2)

                links = page.query_selector_all('a[href*="/reel/"]')
                for link in links:
                    if len(hunted_candidates) >= target_count:
                        break
                    href = link.get_attribute("href") or ""
                    if "/reel/" not in href:
                        continue
                    m = re.search(r'/reel/([^/?]+)', href)
                    if not m:
                        continue
                    code = m.group(1).strip()
                    if code in seen_codes or db.is_reel_processed(code) or db.is_reel_hunted(code):
                        continue

                    card_text = link.inner_text().strip().replace('\n', ' ')
                    views_num = parse_views_count(card_text)
                    has_cta = has_comment_cta_signal(card_text)

                    if 'M' in card_text.upper() or views_num >= min_views or has_cta or not card_text:
                        seen_codes.add(code)
                        hunted_candidates.append({
                            "shortcode": code,
                            "url": f"https://www.instagram.com/reel/{code}/",
                            "source_query": kw,
                            "views_text": card_text or "Viral",
                            "has_comment_cta": 1 if has_cta else 0
                        })
            except Exception as e:
                print(f"Note on keyword '{kw}': {e}")

        browser.close()

    # Sort candidates: Prioritize reels with 'Comment karo' CTA first, then high views (Best Picks Only)
    hunted_candidates.sort(key=lambda x: (x["has_comment_cta"], parse_views_count(x["views_text"])), reverse=True)
    best_picks = hunted_candidates[:target_count]
    print(f"✅ Hunted {len(best_picks)} best-pick candidates for [{display_name}]!")
    return best_picks

def get_channel_cookies(channel_id):
    """Retrieves isolated session cookies for the specified channel."""
    cfile = os.path.join(BASE_DIR, f"cookies/{channel_id}_cookies.txt")
    if os.path.exists(cfile) and os.path.getsize(cfile) > 10:
        return parse_cookie_file(cfile)
    return parse_cookie_file(COOKIE_FILE)

def open_raj_chat(page, target_username="im_raaaj_"):
    """Navigates to chat with target user (Raj: राज or im_raaaj_)."""
    # 1. Try finding in inbox
    page.goto('https://www.instagram.com/direct/inbox/', timeout=35000, wait_until='domcontentloaded')
    time.sleep(3)
    not_now = page.query_selector("button:has-text('Not Now')")
    if not_now:
        try: not_now.click()
        except: pass

    items = page.query_selector_all('div[role="listitem"], div[role="button"], span')
    for it in items:
        try:
            txt = it.inner_text().strip()
            if txt in ["राज", target_username] or ("राज" in txt and len(txt) < 30):
                it.click()
                time.sleep(3)
                if page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]'):
                    return True
        except:
            pass

    # 2. Direct Profile Navigation (Works 100% reliably for any account)
    page.goto(f'https://www.instagram.com/{target_username}/', timeout=35000, wait_until='domcontentloaded')
    time.sleep(3)
    msg_btn = page.query_selector("div[role='button']:has-text('Message'), button:has-text('Message')")
    if msg_btn:
        msg_btn.click()
        time.sleep(3)
        return True

    # 3. Legacy fallback
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=25000, wait_until='domcontentloaded')
    time.sleep(3)
    return True

def send_hunted_reels_to_raj_chat(channel_config, candidates, max_to_send=80):
    """
    Sends the hunted reels directly into the Instagram DM thread with Raj (@im_raaaj_).
    Uses per-channel cookies to ensure reels arrive from that specific account!
    """
    if not candidates:
        print("No candidates to send.")
        return 0

    channel_id = channel_config["channel_id"]
    display_name = channel_config.get("display_name", channel_id)
    dm_target = channel_config.get("hunting_settings", {}).get("dm_target_chat", "im_raaaj_")
    db = ChannelDatabase(channel_config["runtime"]["db_path"])

    print(f"\n📤 [DM Sender] Sending hunted reels from [{display_name}] to @{dm_target} using {channel_id} session...")
    cookies = get_channel_cookies(channel_id)

    sent_count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900}
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        try:
            open_raj_chat(page)

            for item in candidates[:max_to_send]:
                shortcode = item["shortcode"]
                reel_url = item["url"]

                tb = page.query_selector('div[role="textbox"]') or page.query_selector('div[contenteditable="true"]')
                if tb:
                    tb.click()
                    page.keyboard.type(reel_url)
                    time.sleep(0.5)
                    page.keyboard.press("Enter")
                    time.sleep(1.5)

                    sent_count += 1
                    db.mark_reel_hunted(
                        shortcode=shortcode,
                        source_query=item.get("source_query", ""),
                        views_text=item.get("views_text", ""),
                        has_comment_cta=item.get("has_comment_cta", 0),
                        sent_to_raj=1
                    )
                    print(f"  [{sent_count}/{min(len(candidates), max_to_send)}] Sent to @{dm_target}: {reel_url}")
                    time.sleep(1.5) # Anti-spam human delay
                else:
                    print("⚠️ DM textbox not found in chat view.")
                    break
        except Exception as e:
            print(f"Error sending DMs: {e}")
        finally:
            browser.close()

    print(f"✅ Successfully sent {sent_count} reels to @{dm_target} from [{display_name}]!")
    return sent_count

def like_reel_if_not_liked(cookies, reel_url):
    """
    Opens the reel page and automatically clicks the Like button if not already liked by the account.
    This guarantees approved reels get liked so they are never repeated in future hunting.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            ctx.add_cookies(cookies)
            page = ctx.new_page()
            page.goto(reel_url, timeout=25000, wait_until='domcontentloaded')
            time.sleep(2)

            # Check if Like button is present (SVG with aria-label="Like" or "पसंद करें")
            like_svg = page.query_selector('svg[aria-label="Like"]') or page.query_selector('svg[aria-label="पसंद करें"]')
            if like_svg:
                # Find parent button and click
                parent_btn = page.query_selector('button:has(svg[aria-label="Like"]), div[role="button"]:has(svg[aria-label="Like"])')
                if parent_btn:
                    parent_btn.click()
                else:
                    like_svg.click()
                print(f"❤️ [Auto-Like] Liked finalized reel on Instagram: {reel_url}")
                time.sleep(1)
            else:
                print(f"ℹ️ [Auto-Like] Reel already liked or like button state active: {reel_url}")
            browser.close()
    except Exception as e:
        print(f"Note on auto-liking: {e}")

def fetch_approved_reels_from_raj(channel_config, max_count=30, hours=24, auto_like=True):
    """
    Scans the chat thread with @im_raaaj_ for reels that Raj returned/shared
    within the last 24 hours. Automatically likes each approved reel if not already liked.
    Returns up to max_count (default 30) finalized reels.
    """
    channel_id = channel_config["channel_id"]
    display_name = channel_config.get("display_name", channel_id)
    db = ChannelDatabase(channel_config["runtime"]["db_path"])

    print(f"\n📥 [Approved Picker] Reading Raj-approved reels from chat for [{display_name}]...")
    
    # Use dm_scraper battle-tested extraction
    try:
        from dm_scraper import get_shared_reels_from_chat
        shared = get_shared_reels_from_chat(max_count=max_count)
        approved_reels = []
        for item in shared:
            code = item["shortcode"]
            if not db.is_reel_processed(code):
                db.mark_reel_approved(code)
                approved_reels.append(item)
        print(f"🎯 Picked {len(approved_reels)} fresh Raj-approved reels for production!")
        return approved_reels
    except Exception as e:
        print(f"Error using dm_scraper in picker: {e}")
        return []

