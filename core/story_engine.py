"""
================================================================================
🌟 AUTOMATED INSTAGRAM STORIES ENGINE (20 STORIES / DAY PER ACCOUNT)
================================================================================
Promotes your own reels to Instagram Stories:
- 🔥 VIRAL REELS: Shows top-performing reels with like counts to capture social proof
- 👀 LOW-VIEW REELS: Pushes underrated/recent reels to get them extra views and reach

Distribution: Alternates every ~43 minutes between Viral Reels & Low-View Reels!
Pacing: 08:00 AM - 10:00 PM (20 Stories / Day per Account = 80 Stories Total)
================================================================================
"""

import os
import sys
import time
import json
import random
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase
from core.iron_shield import CircuitBreaker, is_reel_100pct_safe

CHANNEL_THEMES = {
    "startup_road": {
        "bg_color": (15, 23, 42),       # Slate Dark #0f172a
        "border_color": (225, 29, 72),   # Crimson Rose #e11d48
        "badge_bg": (225, 29, 72),
        "badge_text": "💼 STARTUP ROAD • REEL SPOTLIGHT",
        "handle": "@startup_road"
    },
    "trading_pulse": {
        "bg_color": (9, 13, 22),         # Deep Navy #090d16
        "border_color": (14, 165, 233),   # Cyan Blue #0ea5e9
        "badge_bg": (14, 165, 233),
        "badge_text": "📈 TRADING ROAD • REEL SPOTLIGHT",
        "handle": "@trading_road_"
    },
    "healthy_diet": {
        "bg_color": (6, 26, 20),         # Forest Dark #061a14
        "border_color": (16, 185, 129),  # Emerald Green #10b981
        "badge_bg": (16, 185, 129),
        "badge_text": "🥗 GUDTREE • REEL SPOTLIGHT",
        "handle": "@gudtree_"
    },
    "viral_finds": {
        "bg_color": (11, 7, 20),         # Cyber Dark #0b0714
        "border_color": (139, 92, 246),  # Neon Violet #8b5cf6
        "badge_bg": (139, 92, 246),
        "badge_text": "🛍️ TRENDING ROAD • REEL SPOTLIGHT",
        "handle": "@trending_road"
    },
    "trading_road24": {
        "bg_color": (9, 13, 22),         # Deep Navy #090d16
        "border_color": (14, 165, 233),   # Cyan Blue #0ea5e9
        "badge_bg": (14, 165, 233),
        "badge_text": "📈 TRADING ROAD 24 • REEL SPOTLIGHT",
        "handle": "@trading_road24"
    },
    "the_loan_road": {
        "bg_color": (10, 25, 20),         # Deep Emerald Black
        "border_color": (16, 185, 129),   # Emerald Green #10b981
        "badge_bg": (16, 185, 129),
        "badge_text": "💰 THE LOAN ROAD • REEL SPOTLIGHT",
        "handle": "@the_loan_road"
    }
}

def get_story_fonts():
    """Loads system TrueType fonts with fallback."""
    try:
        f_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
        f_tag = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
        f_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 44)
        f_cta = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
    except:
        f_badge = ImageFont.load_default()
        f_tag = ImageFont.load_default()
        f_title = ImageFont.load_default()
        f_cta = ImageFont.load_default()
    return f_badge, f_tag, f_title, f_cta

# ------------------------------------------------------------------------------
# FETCH VIRAL & LOW-VIEW REEL POOLS FROM META GRAPH API
# ------------------------------------------------------------------------------
def get_channel_reels_pools(channel_id: str) -> dict:
    """
    Fetches up to 50 posted reels directly from Meta Graph API.
    Splits them into:
      - viral: Top reels sorted by likes & comments (highest social proof)
      - low_views: Reels with lowest likes (needs boost & traffic)
    """
    config = get_channel_config(channel_id)
    creds = config.get("credentials", {})
    account_id = creds.get("instagram_account_id")
    token = creds.get("page_access_token")

    if not account_id or not token:
        return {"viral": [], "low_views": []}

    url = f"https://graph.facebook.com/v21.0/{account_id}/media?fields=id,caption,like_count,comments_count,permalink,thumbnail_url,timestamp&limit=50&access_token={token}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"⚠️ Failed to fetch media for {channel_id}: {resp.status_code} {resp.text}")
            return {"viral": [], "low_views": []}

        items = resp.json().get("data", [])
        # Filter items with valid thumbnail_url
        valid_items = [it for it in items if it.get("thumbnail_url")]
        if not valid_items:
            return {"viral": [], "low_views": []}

        # Sort by engagement score = (likes * 2 + comments)
        sorted_by_eng = sorted(
            valid_items,
            key=lambda x: (x.get("like_count", 0) * 2 + x.get("comments_count", 0)),
            reverse=True
        )

        # Top 15 are Viral Pool
        viral_pool = sorted_by_eng[:15]

        # Lowest 15 are Low-Views Pool (sorted ascending)
        low_views_pool = sorted(
            valid_items,
            key=lambda x: (x.get("like_count", 0) * 2 + x.get("comments_count", 0))
        )[:15]

        return {"viral": viral_pool, "low_views": low_views_pool}
    except Exception as e:
        print(f"❌ Error fetching reels pools for {channel_id}: {e}")
        return {"viral": [], "low_views": []}

# ------------------------------------------------------------------------------
# RENDER 1080x1920 REEL SHOWCASE STORY CARD
# ------------------------------------------------------------------------------
def render_reel_story_card(channel_id: str, reel_item: dict, is_viral: bool, output_path: str):
    """
    Renders an ultra-luxurious 1080x1920 Instagram Story showcasing your actual reel:
    - Real Thumbnail in center with Play Button
    - 'VIRAL REEL • X LIKES' or '👀 IN CASE YOU MISSED THIS'
    - Clean Hook/Title extracted from caption
    - Prominent 'TAP PROFILE TO WATCH FULL REEL' CTA
    """
    theme = CHANNEL_THEMES.get(channel_id, CHANNEL_THEMES["startup_road"])
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), color=theme["bg_color"])
    draw = ImageDraw.Draw(img)

    f_badge, f_tag, f_title, f_cta = get_story_fonts()

    # 1. Subtle Outer Border
    margin = 35
    draw.rounded_rectangle(
        [(margin, margin), (w - margin, h - margin)],
        radius=24,
        outline=theme["border_color"],
        width=4
    )

    # 2. Header Badge
    badge_w, badge_h = 740, 75
    badge_x = (w - badge_w) // 2
    badge_y = 120
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
        radius=37,
        fill=theme["badge_bg"]
    )
    bbox = draw.textbbox((0, 0), theme["badge_text"], font=f_badge)
    tx = badge_x + (badge_w - (bbox[2] - bbox[0])) // 2
    ty = badge_y + (badge_h - (bbox[3] - bbox[1])) // 2 - 3
    draw.text((tx, ty), theme["badge_text"], fill=(255, 255, 255), font=f_badge)

    # 3. Status Tag (Viral vs Boost)
    tag_y = 225
    likes = reel_item.get("like_count", 0)
    if is_viral:
        tag_str = f"🔥 VIRAL REEL • {likes:,} LIKES" if likes > 10 else "🔥 VIRAL REEL • TRENDING NOW"
        tag_bg = (225, 29, 72)
    else:
        tag_str = "👀 IN CASE YOU MISSED THIS REEL"
        tag_bg = (30, 41, 59)

    t_box = draw.textbbox((0, 0), tag_str, font=f_tag)
    t_w = (t_box[2] - t_box[0]) + 60
    t_x = (w - t_w) // 2
    draw.rounded_rectangle(
        [(t_x, tag_y), (t_x + t_w, tag_y + 60)],
        radius=30,
        fill=tag_bg,
        outline=theme["border_color"],
        width=2
    )
    draw.text((t_x + 30, tag_y + 12), tag_str, fill=(255, 255, 255), font=f_tag)

    # 4. Download and Place Reel Thumbnail in Center
    thumb_url = reel_item.get("thumbnail_url")
    tw, th = 640, 1136
    tx_pos = (w - tw) // 2
    ty_pos = 315

    try:
        resp = requests.get(thumb_url, timeout=12)
        thumb = Image.open(BytesIO(resp.content)).convert("RGB")
        thumb = thumb.resize((tw, th), Image.Resampling.LANCZOS)

        # Rounded corner mask
        mask = Image.new("L", (tw, th), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (tw, th)], radius=30, fill=255)

        # Border behind thumb
        draw.rounded_rectangle(
            [(tx_pos - 6, ty_pos - 6), (tx_pos + tw + 6, ty_pos + th + 6)],
            radius=34,
            outline=theme["border_color"],
            width=6
        )
        img.paste(thumb, (tx_pos, ty_pos), mask)
    except Exception as e:
        print(f"⚠️ Thumbnail load failed: {e}")
        draw.rectangle([(tx_pos, ty_pos), (tx_pos + tw, ty_pos + th)], fill=(30, 41, 59))

    # 5. Central Play Button Overlay (▶)
    cx = w // 2
    cy = ty_pos + th // 2
    pr = 55
    play_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(play_overlay)
    pdraw.ellipse([(cx - pr, cy - pr), (cx + pr, cy + pr)], fill=(0, 0, 0, 170), outline=(255, 255, 255, 230), width=4)
    pdraw.polygon([(cx - 15, cy - 25), (cx - 15, cy + 25), (cx + 25, cy)], fill=(255, 255, 255, 245))
    img.paste(Image.alpha_composite(img.convert("RGBA"), play_overlay).convert("RGB"))

    # 6. Extract Hook/Title from Reel Caption
    draw = ImageDraw.Draw(img)
    caption = reel_item.get("caption", "").strip()
    first_line = caption.split("\n")[0] if caption else "WATCH OUR LATEST REEL"
    # Clean emojis or hashtags from first line
    words = [w for w in first_line.split() if not w.startswith("#")]
    title_text = " ".join(words[:12]).upper()

    # Wrap title into max 2 lines
    lines = []
    cur = []
    for wd in title_text.split():
        if len(" ".join(cur + [wd])) <= 26:
            cur.append(wd)
        else:
            lines.append(" ".join(cur))
            cur = [wd]
        if len(lines) >= 2: break
    if cur and len(lines) < 2: lines.append(" ".join(cur))

    by = 1495
    for l in lines:
        l_box = draw.textbbox((0, 0), l, font=f_title)
        lx = (w - (l_box[2] - l_box[0])) // 2
        draw.text((lx, by), l, fill=(255, 255, 255), font=f_title)
        by += 60

    # 7. Big CTA Banner
    cta_y = 1655
    cta_w, cta_h = 800, 85
    cta_x = (w - cta_w) // 2
    draw.rounded_rectangle(
        [(cta_x, cta_y), (cta_x + cta_w, cta_y + cta_h)],
        radius=42,
        fill=theme["border_color"]
    )
    cta_text = "👆 TAP PROFILE TO WATCH FULL REEL ↗"
    c_box = draw.textbbox((0, 0), cta_text, font=f_cta)
    cx_t = cta_x + (cta_w - (c_box[2] - c_box[0])) // 2
    cy_t = cta_y + (cta_h - (c_box[3] - c_box[1])) // 2 - 3
    draw.text((cx_t, cy_t), cta_text, fill=(255, 255, 255), font=f_cta)

    # 8. Footer Handle
    footer_text = f"Follow {theme['handle']} for daily insights"
    f_box = draw.textbbox((0, 0), footer_text, font=f_tag)
    fx = (w - (f_box[2] - f_box[0])) // 2
    draw.text((fx, 1775), footer_text, fill=(148, 163, 184), font=f_tag)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "JPEG", quality=95)
    return output_path

# ------------------------------------------------------------------------------
# PUBLISH SINGLE STORY FOR CHANNEL (ALTERNATING VIRAL & LOW-VIEWS)
# ------------------------------------------------------------------------------
def publish_single_channel_story(channel_id: str, story_index: int = 1, today_str: str = None):
    """
    Renders and publishes a single Instagram Story promoting one of your reels:
    - Odd slots (1, 3, 5, 7, 9...) ➔ Top Viral Reels
    - Even slots (2, 4, 6, 8, 10...) ➔ Low-View Reels needing boost
    """
    if not today_str:
        today_str = datetime.now().strftime("%Y-%m-%d")

    config = get_channel_config(channel_id)
    if not config.get("enabled", True):
        return False

    db = ChannelDatabase(config["runtime"]["db_path"])
    if db.is_story_processed(story_index, today_str):
        print(f"⏩ [Story Already Live] {channel_id} Story #{story_index} already posted for {today_str}.")
        return True

    # Check Circuit Breaker
    is_locked, lock_reason = CircuitBreaker.is_channel_locked(channel_id)
    if is_locked:
        print(f"🛑 [Circuit Breaker Lock] Skipping story for {channel_id}: {lock_reason}")
        return False

    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))

    if not publisher.is_configured():
        return False

    # Fetch reel pools
    pools = get_channel_reels_pools(channel_id)
    viral_pool = pools.get("viral", [])
    low_views_pool = pools.get("low_views", [])

    is_viral = (story_index % 2 == 1)
    target_pool = viral_pool if is_viral else low_views_pool

    # Fallback to the other pool if target is empty
    if not target_pool:
        target_pool = low_views_pool if is_viral else viral_pool

    if not target_pool:
        print(f"⚠️ [Story Engine] No posted reels found for {channel_id} to showcase. Skipping slot #{story_index}.")
        return False

    # Pick reel based on slot index
    pool_idx = (story_index // 2) % len(target_pool)
    selected_reel = target_pool[pool_idx]
    reel_permalink = selected_reel.get("permalink", "")
    caption_line = selected_reel.get("caption", "").split("\n")[0][:60]
    reel_likes = selected_reel.get("like_count", 0)

    # Pre-Flight Compliance Check on title
    is_safe, reason = is_reel_100pct_safe(caption_line, "REEL_STORY", caption_line)
    if not is_safe:
        print(f"🛑 [Iron Shield Blocked Story] {reason}")
        # Try next reel in pool
        selected_reel = target_pool[(pool_idx + 1) % len(target_pool)]

    temp_img = os.path.join(config["runtime"]["workspace_dir"], f"story_slot_{story_index:02d}.jpg")
    render_reel_story_card(channel_id, selected_reel, is_viral, temp_img)

    display_name = config.get("display_name", channel_id)
    story_type = f"🔥 VIRAL REEL ({reel_likes} likes)" if is_viral else "👀 LOW-VIEW REEL BOOST"
    print(f"\n🌟 [{display_name}] Publishing Story #{story_index}/20: {story_type} -> {caption_line}...")

    try:
        sent, cdn_url = hub.send_photo_with_cdn_url(temp_img, caption=f"[{display_name}] Story #{story_index} ({story_type}): {reel_permalink}")
        if sent and cdn_url:
            res = publisher.publish_story(cdn_url)
            if res and "media_id" in res:
                media_id = res["media_id"]
                db.mark_story_processed(story_index, today_str, caption_line, media_id)
                print(f"🎉 [{display_name}] Story #{story_index}/20 LIVE on Instagram! (Media ID: {media_id})")
                hub.send_message(
                    f"🌟 <b>{display_name} Story #{story_index}/20 LIVE!</b>\n\n"
                    f"🎯 <b>Type:</b> {story_type}\n"
                    f"🎬 <b>Reel:</b> {reel_permalink}\n"
                    f"💡 <b>Hook:</b> {caption_line}"
                )
                return True
    except Exception as e:
        print(f"❌ Story publish failed for {channel_id}: {e}")
    finally:
        if os.path.exists(temp_img):
            try: os.remove(temp_img)
            except: pass

    return False

# ------------------------------------------------------------------------------
# 20 SLOTS GENERATOR (08:00 AM - 10:00 PM) ~ Every 43 Minutes
# ------------------------------------------------------------------------------
def generate_20_story_slots():
    """Generates 20 slots between 08:00 AM and 10:00 PM (~43 mins apart)."""
    slots = []
    start_total = 8 * 60       # 08:00 AM
    end_total = 21 * 60 + 50   # 09:50 PM
    interval = (end_total - start_total) / 19
    for i in range(20):
        m_total = int(start_total + i * interval)
        h = m_total // 60
        m = m_total % 60
        slots.append((i + 1, h, m))
    return slots

STORY_SLOTS = generate_20_story_slots()
