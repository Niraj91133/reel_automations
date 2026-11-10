"""
================================================================================
🌟 ULTRA-LUXURY AUTOMATED INSTAGRAM STORIES ENGINE (20 STORIES / DAY)
================================================================================
Promotes your own published reels to Instagram Stories with:
- 🎬 Cinematic Ambient Gaussian Blur Video Background
- 📱 Floating 9:16 Glassmorphism Reel Card with 3D Drop Shadow
- 🏷️ Native Interactive User Tag Sticker (Clicking sticker opens profile & reels tab)
- 🚫 Zero Tofu/Unicode Box Artifacts (Clean typography)
- ⚡ High-Conversion 'WATCH FULL REEL' CTA

Distribution: Alternates every ~43 minutes between Viral Reels & Low-View Boosts!
Pacing: 08:00 AM - 10:00 PM (20 Stories / Day per Account)
================================================================================
"""

import os
import sys
import time
import json
import random
import re
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
        "accent_color": (225, 29, 72),     # Crimson Rose
        "display_name": "Startup Road",
        "badge_text": "REEL SPOTLIGHT | BUSINESS MODEL",
        "handle": "@startup_road"
    },
    "trading_pulse": {
        "accent_color": (14, 165, 233),    # Cyan Blue
        "display_name": "Trading Road",
        "badge_text": "REEL SPOTLIGHT | PRICE ACTION",
        "handle": "@trading_road_"
    },
    "healthy_diet": {
        "accent_color": (16, 185, 129),    # Emerald Green
        "display_name": "Gudtree",
        "badge_text": "REEL SPOTLIGHT | HEALTH & DIET",
        "handle": "@gudtree_"
    },
    "viral_finds": {
        "accent_color": (245, 158, 11),    # Amber Gold
        "display_name": "Trending Road",
        "badge_text": "REEL SPOTLIGHT | AI & GROWTH",
        "handle": "@trending_road"
    },
    "trading_road24": {
        "accent_color": (14, 165, 233),    # Cyan Blue
        "display_name": "Trading Road 24",
        "badge_text": "REEL SPOTLIGHT | MARKET ANALYSIS",
        "handle": "@trading_road24"
    },
    "the_loan_road": {
        "accent_color": (16, 185, 129),    # Emerald Green
        "display_name": "The Loan Road",
        "badge_text": "REEL SPOTLIGHT | WEALTH & LOANS",
        "handle": "@the_loan_road"
    },
    "the_startuproad": {
        "accent_color": (225, 29, 72),     # Crimson Rose
        "display_name": "The Startup Road",
        "badge_text": "REEL SPOTLIGHT | STARTUP BLUEPRINT",
        "handle": "@the_startuproad"
    }
}

def get_story_fonts():
    """Loads modern typography fonts with clean fallback."""
    font_paths = [
        ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf"),
        ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"),
    ]
    for bold_p, reg_p in font_paths:
        if os.path.exists(bold_p) and os.path.exists(reg_p):
            try:
                f_header = ImageFont.truetype(bold_p, 32)
                f_sub = ImageFont.truetype(reg_p, 22)
                f_title = ImageFont.truetype(bold_p, 36)
                f_btn = ImageFont.truetype(bold_p, 28)
                return f_header, f_sub, f_title, f_btn
            except Exception:
                pass
    f_def = ImageFont.load_default()
    return f_def, f_def, f_def, f_def

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

        # Lowest 15 are Low-Views Pool
        low_views_pool = sorted(
            valid_items,
            key=lambda x: (x.get("like_count", 0) * 2 + x.get("comments_count", 0))
        )[:15]

        return {"viral": viral_pool, "low_views": low_views_pool}
    except Exception as e:
        print(f"❌ Error fetching reels pools for {channel_id}: {e}")
        return {"viral": [], "low_views": []}

# ------------------------------------------------------------------------------
# RENDER ULTRA-LUXURY AESTHETIC STORY CARD (1080x1920)
# ------------------------------------------------------------------------------
def render_reel_story_card(channel_id: str, reel_item: dict, is_viral: bool, output_path: str):
    """
    Renders an ultra-modern 1080x1920 Instagram Story with:
    1. Dynamic Ambient Gaussian Blur Background matching the reel's actual color palette
    2. Floating 9:16 Glassmorphism Reel Card with soft 3D shadow
    3. Sleek Frosted Glass Play Icon
    4. Minimalist native header pill with channel avatar initial
    5. Clean typography (100% sanitized, zero emoji boxes)
    6. Native-style 'WATCH FULL REEL' Sticker Button mapped to user_tags
    """
    theme = CHANNEL_THEMES.get(channel_id, CHANNEL_THEMES["startup_road"])
    w, h = 1080, 1920
    accent = theme.get("accent_color", (225, 29, 72))
    handle_str = theme.get("handle", "@channel").lstrip("@")

    thumb_url = reel_item.get("thumbnail_url")
    real_thumb = None
    if thumb_url:
        try:
            resp = requests.get(thumb_url, timeout=12)
            if resp.status_code == 200:
                real_thumb = Image.open(BytesIO(resp.content)).convert("RGB")
        except Exception as e:
            print(f"⚠️ Thumbnail fetch note: {e}")

    if not real_thumb:
        # Graceful modern fallback card
        real_thumb = Image.new("RGB", (720, 1280), color=(15, 23, 42))
        f_d = ImageDraw.Draw(real_thumb)
        f_d.rectangle([(20, 20), (700, 1260)], outline=accent, width=4)

    # 1. Ambient Blurred Video Background
    bg = real_thumb.resize((w, h), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=55))
    dark_overlay = Image.new("RGBA", (w, h), (10, 14, 22, 195))
    bg = Image.alpha_composite(bg.convert("RGBA"), dark_overlay)

    f_header, f_sub, f_title, f_btn = get_story_fonts()

    # 2. Modern Glassmorphism Top Header Pill
    top_y = 105
    pill_w, pill_h = 560, 72
    pill_x = (w - pill_w) // 2

    pill_bg = Image.new("RGBA", (pill_w, pill_h), (255, 255, 255, 20))
    p_draw = ImageDraw.Draw(pill_bg)
    p_draw.rounded_rectangle([(0, 0), (pill_w, pill_h)], radius=36, fill=(255, 255, 255, 25), outline=(255, 255, 255, 60), width=1)
    bg.paste(pill_bg, (pill_x, top_y), pill_bg)

    p_draw_full = ImageDraw.Draw(bg)
    av_r = 20
    av_x = pill_x + 36
    av_y = top_y + pill_h // 2
    initial = handle_str[:1].upper() if handle_str else "S"
    p_draw_full.ellipse([(av_x - av_r, av_y - av_r), (av_x + av_r, av_y + av_r)], fill=accent)
    p_draw_full.text((av_x - 6, av_y - 12), initial, fill=(255, 255, 255), font=f_sub)
    p_draw_full.text((av_x + 30, top_y + 11), handle_str, fill=(255, 255, 255), font=f_header)
    status_label = f"VIRAL REEL | {reel_item.get('like_count', 0):,} LIKES" if is_viral else "REEL SPOTLIGHT | NEW UPLOAD"
    p_draw_full.text((av_x + 30, top_y + 42), status_label, fill=(203, 213, 225), font=f_sub)

    # 3. Centered Floating 9:16 Card with 3D Drop Shadow
    card_w, card_h = 740, 1220
    card_x = (w - card_w) // 2
    card_y = 215

    card_thumb = real_thumb.resize((card_w, card_h), Image.Resampling.LANCZOS)
    mask = Image.new("L", (card_w, card_h), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([(0, 0), (card_w, card_h)], radius=34, fill=255)

    # Soft 3D drop shadow behind card
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([(card_x - 10, card_y - 6), (card_x + card_w + 10, card_y + card_h + 20)], radius=42, fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
    bg = Image.alpha_composite(bg, shadow)

    # Paste Card Image
    bg.paste(card_thumb, (card_x, card_y), mask)

    # Subtle Frosted Glass Border
    card_draw = ImageDraw.Draw(bg)
    card_draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=34, outline=(255, 255, 255, 75), width=2)

    # Minimal Frosted Play Icon in center
    cx = w // 2
    cy = card_y + card_h // 2
    play_r = 50
    play_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p_icon_draw = ImageDraw.Draw(play_layer)
    p_icon_draw.ellipse([(cx - play_r, cy - play_r), (cx + play_r, cy + play_r)], fill=(0, 0, 0, 140), outline=(255, 255, 255, 220), width=3)
    p_icon_draw.polygon([(cx - 12, cy - 20), (cx - 12, cy + 20), (cx + 22, cy)], fill=(255, 255, 255, 245))
    bg = Image.alpha_composite(bg, play_layer)

    # 4. Clean Reel Title (Zero Tofu/Unicode Box Artifacts)
    final_draw = ImageDraw.Draw(bg)
    raw_caption = reel_item.get("caption", "WATCH OUR LATEST REEL").split("\n")[0]
    clean_title = re.sub(r"[^\w\s\-,:!\?\.]", "", raw_caption).strip().upper()
    words = [wd for wd in clean_title.split() if not wd.startswith("#")][:9]
    clean_title = " ".join(words)
    bbox_t = final_draw.textbbox((0, 0), clean_title, font=f_title)
    tx = (w - (bbox_t[2] - bbox_t[0])) // 2
    final_draw.text((tx, card_y + card_h + 35), clean_title, fill=(255, 255, 255), font=f_title)

    # 5. Native Instagram-Style Story Link Sticker Button (x: 0.5, y: 0.82)
    btn_w, btn_h = 560, 84
    btn_x = (w - btn_w) // 2
    btn_y = 1575

    btn_layer = Image.new("RGBA", (btn_w, btn_h), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(btn_layer)
    b_draw.rounded_rectangle([(0, 0), (btn_w, btn_h)], radius=42, fill=(255, 255, 255, 250))
    bg.paste(btn_layer, (btn_x, btn_y), btn_layer)

    b_text = "WATCH FULL REEL  >"
    btn_final_draw = ImageDraw.Draw(bg)
    bbox_b = btn_final_draw.textbbox((0, 0), b_text, font=f_btn)
    bx = btn_x + (btn_w - (bbox_b[2] - bbox_b[0])) // 2
    by = btn_y + (btn_h - (bbox_b[3] - bbox_b[1])) // 2 - 3
    btn_final_draw.text((bx, by), b_text, fill=(15, 23, 42), font=f_btn)

    # Draw small crisp arrow next to button text
    arrow_x = bx + (bbox_b[2] - bbox_b[0]) + 10
    arrow_y = by + 6
    btn_final_draw.polygon([(arrow_x, arrow_y), (arrow_x, arrow_y + 14), (arrow_x + 10, arrow_y + 7)], fill=(15, 23, 42))

    # Explanatory Subtext
    sub_text = f"Tap sticker to open full reel on @{handle_str}"
    bbox_s = btn_final_draw.textbbox((0, 0), sub_text, font=f_sub)
    sx = (w - (bbox_s[2] - bbox_s[0])) // 2
    btn_final_draw.text((sx, btn_y + 105), sub_text, fill=(148, 163, 184), font=f_sub)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    bg.convert("RGB").save(output_path, "JPEG", quality=95)
    return output_path

# ------------------------------------------------------------------------------
# PUBLISH SINGLE STORY FOR CHANNEL (WITH INTERACTIVE USER_TAGS)
# ------------------------------------------------------------------------------
def publish_single_channel_story(channel_id: str, story_index: int = 1, today_str: str = None):
    """
    Renders and publishes a single Instagram Story promoting one of your reels:
    - Alternates between Viral Reels and Low-View Boosts
    - Passes user_tags=[{"username": handle, "x": 0.5, "y": 0.82}] so tapping
      the Story button directly links viewers to your account's Reels tab!
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
    theme = CHANNEL_THEMES.get(channel_id, CHANNEL_THEMES["startup_road"])
    clean_handle = theme.get("handle", "@channel").lstrip("@")

    # Interactive User Tag Sticker directly on the CTA Button (x: 0.5, y: 0.82)
    user_tags = [{"username": clean_handle, "x": 0.5, "y": 0.82}]

    print(f"\n🌟 [{display_name}] Publishing Story #{story_index}/20: {story_type} -> {caption_line}...")

    try:
        sent, cdn_url = hub.send_photo_with_cdn_url(
            temp_img,
            caption=f"[{display_name}] Story #{story_index} ({story_type}): {reel_permalink}"
        )
        if sent and cdn_url:
            res = publisher.publish_story(cdn_url, user_tags=user_tags)
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
